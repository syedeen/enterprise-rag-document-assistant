from sentence_transformers import SentenceTransformer
import faiss
import requests
import pickle
from rank_bm25 import BM25Okapi
from app.rag_test import embedding_model


    

def get_results(query , file_name , user_id = None):

    with open("app/faiss/bm25.pkl", "rb") as f:
        bm25 = pickle.load(f)
    with open("app/faiss/chunks.pkl","rb") as f:
        chunks = pickle.load(f)
    with open("app/faiss/metadata.pkl", "rb") as f:
        metadata = pickle.load(f)

    index = faiss.read_index("app/faiss/faiss_index.bin")
    

    #query
    embedding_query = embedding_model.encode([query]) #wrapped in a list cause faiss expects embeddings as a 2d array 

    #tokenize query
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)

    #search
    k = 3
    distances , indices = index.search(embedding_query , k)

    filtered_indices = []
    for i in indices[0]:
        if metadata[i]["user_id"] == user_id:
            if file_name is None or metadata[i]["filename"] == file_name:
                filtered_indices.append(i)


    if not filtered_indices:
        return {
            "response": "No relevant documents found.",
            "metadata": []
        }


    #semantic scoring 

    sem_map = {
        idx:1/(1+distances[0][i])
        for i , idx in enumerate(indices[0])
    }

    final_scores = []
    alpha = 0.7 #semantic weight
    beta = 0.3 #keyword weight

    for i in  filtered_indices:
        sem_score = sem_map.get(i,0)
        key_score = bm25_scores[i]
        final_scores.append((i,sem_score * alpha + key_score * beta))



    top_k = sorted(range(len(final_scores)) , key = lambda x :final_scores[x] , reverse=True)[:k]

    retrieved_chunks = [chunks[i] for i in top_k]
    retrieved_metadata = [metadata[i] for i in top_k]

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
        "http://localhost:11434/api/generate",
        json={
            "model":"llama3",
            "prompt":prompt,
            "stream":False
        }
    )

    result = {}


    result["response"] = response.json()["response"]
    result["metadata"] = []
 

    unique_metadata = {(m["filename"], m["page_num"]) for m in retrieved_metadata}
    for filename , page_num in unique_metadata:
        result["metadata"].append(f"{filename} page no:{page_num}")
    
    return result

