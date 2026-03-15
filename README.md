# Enterprise RAG Document Assistant

A production-ready RAG (Retrieval Augmented Generation) API built with FastAPI.

## Tech Stack
- **FastAPI** — REST API
- **Qdrant** — vector database with hybrid search (BM25 + vector)
- **PostgreSQL** — user and file metadata storage
- **AWS S3** — PDF file storage
- **Sentence Transformers** — document embeddings
- **Cross-encoder reranking** — improved retrieval accuracy
- **Docker** — containerized deployment

## Features
- JWT authentication with account lockout
- PDF upload and processing
- Hybrid search (vector + BM25)
- Cross-encoder reranking
- Per-user document isolation
