import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

# Initialize Pinecone
api_key = os.getenv("PINECONE_API_KEY")
index_name = os.getenv("PINECONE_INDEX_NAME", "study-buddy-index")

pc = None
index = None

if api_key:
    try:
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
    except Exception as e:
        print(f"Failed to initialize Pinecone: {e}")
else:
    print("WARNING: PINECONE_API_KEY not found in environment variables.")

def get_pinecone_index():
    return index
