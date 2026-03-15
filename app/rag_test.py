from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct
from app.vector_db import client
from qdrant_client.models import Filter, FieldCondition, MatchValue
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
import uuid


def save_file(file , user_id):
  
    documents = []
    reader = PdfReader(file.file)

    #extract_page
    for page_num , page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue

        documents.append({
            "page_num":page_num+1,
            "file":file,
            "text":text
        })
    
    #chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 100
    )

    new_chunks = []
    new_metadata = []

    for docs in documents:
        splitted_text = text_splitter.split_text(docs["text"])
        
        for chunk in splitted_text:
            new_chunks.append(chunk)
            new_metadata.append({
                "filename":file.filename,
                "page_num":docs["page_num"],
                "user_id":user_id
            })



    #embedding 
    embedded_chunks = embedding_model.encode(new_chunks , batch_size=32)

    points = []
    for i, embedding in enumerate(embedded_chunks):
        points.append(
            PointStruct(
                id = str(uuid.uuid4()),
                vector = embedding.tolist(),
                payload = {
                    "filename": new_metadata[i]["filename"],
                    "page_num": new_metadata[i]["page_num"],
                    "user_id": user_id,
                    "chunk": new_chunks[i],
                }
            )
        )

    client.upsert(
    collection_name="rag_test",
    points=points,
    )

    print("Inserted:", len(points))

    return {"message": "File indexed"}


def delete_embeddings(file,user_id):
    client.delete(
        collection_name="rag_test",
        points_selector=Filter(
            must=[
                FieldCondition(key="filename", match = MatchValue(value=file.file_name)),
                FieldCondition(key="user_id", match = MatchValue(value=user_id))
            ]
        )
    )





