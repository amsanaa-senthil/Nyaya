"""Quick Qdrant connection test"""
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

host = os.getenv("QDRANT_HOST")
api_key = os.getenv("QDRANT_API_KEY")
collection = os.getenv("QDRANT_COLLECTION", "sri_lankan_cases")

print(f"Testing connection to: {host}")
print(f"Collection: {collection}")
print(f"API Key: {'[OK]' if api_key else '[MISSING]'}\n")

try:
    print("Creating client with 60s timeout...")
    client = QdrantClient(url=host, api_key=api_key, timeout=60)
    
    print("Checking collection info...")
    collection_info = client.get_collection(collection_name=collection)
    
    print(f"\n[SUCCESS] Connected to Qdrant!")
    print(f"Collection: {collection}")
    print(f"Vector count: {collection_info.points_count}")
    print(f"Vector size: {collection_info.config.params.vectors.size}")
    
except Exception as e:
    print(f"\n[ERROR] Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check if your Qdrant Cloud cluster is running")
    print("   → Visit: https://cloud.qdrant.io/")
    print("2. Verify the QDRANT_API_KEY in .env is correct")
    print("3. Check your network connection")
    print("4. Try restarting the Qdrant cluster if it's sleeping")
