import os
import sys
from dotenv import load_dotenv

load_dotenv()

def print_status(component, status, message=""):
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"
    icon = "[OK]" if status else "[FAILED]"
    print(f"{icon} {color}{component}{reset}: {message}")

def test_firebase():
    try:
        from database.firebase_client import db
        if db is not None:
            # Try a simple read
            list(db.collection('test').limit(1).stream())
            print_status("Firebase Firestore", True, "Connected successfully")
        else:
            print_status("Firebase Firestore", False, "db object is None")
    except Exception as e:
        print_status("Firebase Firestore", False, str(e))

def test_pinecone():
    try:
        from database.pinecone_client import get_pinecone_index
        index = get_pinecone_index()
        if index is not None:
            stats = index.describe_index_stats()
            print_status("Pinecone", True, f"Connected. Dimension: {stats.get('dimension')}, Vectors: {stats.get('total_vector_count')}")
        else:
            print_status("Pinecone", False, "Index object is None")
    except Exception as e:
        print_status("Pinecone", False, str(e))

def test_cloudinary():
    try:
        import cloudinary
        import cloudinary.api
        config = cloudinary.config()
        if config.cloud_name and config.api_key and config.api_secret:
            # Just pinging config existence is usually enough, but let's try a ping
            cloudinary.api.ping()
            print_status("Cloudinary", True, f"Connected to cloud: {config.cloud_name}")
        else:
            print_status("Cloudinary", False, "Missing credentials")
    except Exception as e:
        print_status("Cloudinary", False, str(e))

def test_openrouter():
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        # Try a quick models fetch
        client.models.list()
        print_status("OpenRouter", True, "API Key is valid")
    except Exception as e:
        print_status("OpenRouter", False, str(e))

if __name__ == "__main__":
    print("\n--- Running Connection Tests ---\n")
    test_firebase()
    test_pinecone()
    test_cloudinary()
    test_openrouter()
    print("\n--------------------------------\n")
