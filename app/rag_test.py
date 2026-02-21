from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import pickle
from rank_bm25 import BM25Okapi
import faiss
import os

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


Faiss = "app/faiss"
os.makedirs(Faiss, exist_ok=True)


def save_file(file , user_id):
    
    if os.path.exists(f"{Faiss}/chunks.pkl"):
        with open(f"{Faiss}/chunks.pkl", "rb") as f:
            chunks = pickle.load(f)
        with open(f"{Faiss}/metadata.pkl", "rb") as f:
            metadata = pickle.load(f)
        with open(f"{Faiss}/bm25.pkl", "rb") as f:
            bm25 = pickle.load(f)
        index = faiss.read_index(f"{Faiss}/faiss_index.bin")
    else:
        chunks = []
        metadata = []
        bm25 = None
        index = None



    documents = []
    reader = PdfReader(file.file)

    #extract_page
    for page_num , page in enumerate(reader.pages):
        text = page.extract_text()

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

    #tokenize chunks
    chunks.extend(new_chunks)
    metadata.extend(new_metadata)

    #embedding 
    embedded_chunks = embedding_model.encode(new_chunks , batch_size=32)

    #search
    if index is None:
        dimension = embedded_chunks.shape[1]
        index = faiss.IndexFlatL2(dimension)

    index.add(embedded_chunks)


    tokenized_chunks = [chunk.lower().split() for chunk in chunks]
    bm25 = BM25Okapi(tokenized_chunks)


    with open("app/faiss/bm25.pkl", "wb") as f:
        pickle.dump(bm25,f)
    with open("app/faiss/chunks.pkl","wb") as f:
        pickle.dump(chunks,f)
    with open("app/faiss/metadata.pkl", "wb") as f:
        pickle.dump(metadata,f)

    faiss.write_index(index, "app/faiss/faiss_index.bin")
    return "file indexed"







