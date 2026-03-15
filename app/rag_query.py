
import requests
from rank_bm25 import BM25Okapi
from app.rag_test import embedding_model
from app.vector_db import client 
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import CrossEncoder
reranker =  CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
import os
OLLAMA_URL = os.getenv("OLLAMA_URL")
def get_results(query , file_name , user_id = None):


    #query
    embedding_query = embedding_model.encode([query])[0] 

    results = client.query_points(
        collection_name="rag_test",
        query=embedding_query,
        query_filter = Filter(
        must=[
        FieldCondition(
            key="user_id",
            match=MatchValue(value=user_id)
        )
    ] 
),
        limit=15
        )
    

    if not results:
        return {
            "response": "No relevant documents found.",
            "metadata": []
        }
    
    retrieved_chunks = []
    retrieved_metadata = []

    vector_scores = []

    for r in results.points:
        payload = r.payload
        if file_name is None or payload["filename"] == file_name:
            retrieved_chunks.append(payload["chunk"])
            retrieved_metadata.append(payload)
            vector_scores.append(r.score)


    if not retrieved_chunks:
            return {
                "response": "No relevant documents found.",
                "metadata": []
        }


    #bm25_scores

    tokenized = [chunk.split() for chunk in retrieved_chunks]
    bm25_model = BM25Okapi(tokenized)
    bm25_scores = bm25_model.get_scores(query.split())

    #normalize
    max_scores = max(bm25_scores)
    bm25_scores = bm25_scores / max_scores  if max_scores > 0 else bm25_scores

    # combine vector_scores + bm25-scores 

    max_vector = max(vector_scores) if max(vector_scores) > 0 else 1
    vector_scores = [v / max_vector for v in vector_scores]

    v_weight = 0.6 
    b_weight = 0.4
    hybrid_scores = [
    v_weight * v + b_weight * b
    for v, b in zip(vector_scores, bm25_scores)
]

    hybrid_ranked = sorted(
         zip(hybrid_scores , retrieved_chunks , retrieved_metadata),
         key = lambda x : x[0],
         reverse = True
    )

    retrieved_chunks = [x[1] for x in hybrid_ranked]
    retrieved_metadata = [x[2] for x in hybrid_ranked]

    #reranker model 

    
    scores = reranker.predict([(query , chunk) for chunk in retrieved_chunks])
    
    ranked = sorted(
    zip(scores, retrieved_chunks, retrieved_metadata),
    key=lambda x: x[0],
    reverse=True
)
    
    top_k = ranked[:3]
    retrieved_chunks = [c[1] for c in top_k]
    retrieved_metadata = [m[2] for m in top_k]
    


    context = "\n\n".join(retrieved_chunks)

    #llm (ollama)   
    prompt = f"""You are a helpful assistant.   
    Use ONLY the information provided in the context below.
    If the answer is not in the context, say:
    "I don't know based on the given information."  

    Do NOT use outside knowledge.
    Context :{context}  
    question :{query}"""


    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model":"llama3",
            "prompt":prompt,
            "stream":False
        }
    )


    result = {
        "response": response.json()["response"],
        "metadata": []
    }

    unique_metadata = {
        (m["filename"], m["page_num"])
        for m in retrieved_metadata
    }

    for filename, page_num in unique_metadata:
        result["metadata"].append(f"{filename} page no:{page_num}")

    return result

