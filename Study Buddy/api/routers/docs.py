import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from datetime import datetime
from database.firebase_client import db, verify_token
from ingestion.embedder import ingest_pdf
from api.schemas import DocumentResponse, DocumentUploadResponse
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

load_dotenv()

cloudinary.config( 
  cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'), 
  api_key = os.getenv('CLOUDINARY_API_KEY'), 
  api_secret = os.getenv('CLOUDINARY_API_SECRET') 
)

router = APIRouter()

from api.dependencies import get_current_user

def process_pdf_background(pdf_path: str, user_id: str, document_id: str):
    try:
        ingest_pdf(pdf_path, user_id, document_id)
        
        # Update status in Firestore
        if db:
            doc_ref = db.collection('documents').document(document_id)
            doc_ref.update({"status": "ready"})
    except Exception as e:
        print(f"Background processing failed: {e}")
        if db:
            doc_ref = db.collection('documents').document(document_id)
            doc_ref.update({"status": "error", "error": str(e)})

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    document_id = str(uuid.uuid4())
    temp_path = f"data/pdfs/temp_{document_id}.pdf"
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    
    # Save locally temporarily
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    # Upload to Cloudinary
    try:
        upload_result = cloudinary.uploader.upload(
            temp_path, 
            resource_type="raw", # Important for PDFs
            public_id=f"study_buddy/users/{user_id}/{document_id}/{file.filename}"
        )
        pdf_url = upload_result.get("secure_url")
    except Exception as e:
        print(f"Failed to upload to Cloudinary: {e}")
        pdf_url = ""
    
    # Save metadata to Firestore
    if db:
        doc_ref = db.collection('documents').document(document_id)
        doc_ref.set({
            "id": document_id,
            "user_id": user_id,
            "filename": file.filename,
            "url": pdf_url,
            "upload_date": datetime.now().isoformat(),
            "status": "processing"
        })
    
    # Start background task to process PDF
    background_tasks.add_task(process_pdf_background, temp_path, user_id, document_id)
    
    return DocumentUploadResponse(document_id=document_id, status="processing")

@router.get("/", response_model=list[DocumentResponse])
async def list_documents(user_id: str = Depends(get_current_user)):
    if not db:
        return []
        
    docs_ref = db.collection('documents').where('user_id', '==', user_id).stream()
    documents = []
    for doc in docs_ref:
        data = doc.to_dict()
        documents.append(DocumentResponse(
            id=data["id"],
            filename=data["filename"],
            upload_date=datetime.fromisoformat(data["upload_date"]),
            status=data["status"]
        ))
    return documents
