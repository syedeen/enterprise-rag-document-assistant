from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams , Distance

client = QdrantClient(path="qdrant_data")

def create_collection():
    client.create_collection(
    collection_name="rag_test",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

