from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams , Distance
import os


# client = QdrantClient(
#     host=os.getenv("QDRANT_HOST", "localhost"),
#     port=int(os.getenv("QDRANT_PORT", 6333))
# ) 

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)



def create_collection():
    if not client.collection_exists("rag_test"):
        client.create_collection(
            collection_name="rag_test",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )