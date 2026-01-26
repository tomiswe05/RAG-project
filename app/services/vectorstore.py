"""
ChromaDB Vector Store Service

This module handles connection to ChromaDB for storing and retrieving embeddings.

In development: Can use either local PersistentClient or remote HttpClient
In production (Docker): Uses HttpClient to connect to ChromaDB container
"""

import os
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

load_dotenv()

# -----------------------------------------------------------------------------
# ChromaDB Connection Configuration
# -----------------------------------------------------------------------------
# CHROMA_HOST: If set, connect via HTTP (Docker/production)
# If not set, use local persistent storage (development)

CHROMA_HOST = os.getenv("CHROMA_HOST")
CHROMA_PORT = os.getenv("CHROMA_PORT", "8000")


def get_chroma_client():
    """
    Get ChromaDB client based on environment.

    - If CHROMA_HOST is set: Use HttpClient (for Docker/production)
    - Otherwise: Use PersistentClient (for local development)
    """
    if CHROMA_HOST:
        # Production: Connect to ChromaDB server via HTTP
        print(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
        return chromadb.HttpClient(
            host=CHROMA_HOST,
            port=int(CHROMA_PORT),
            settings=Settings(
                anonymized_telemetry=False  # Disable telemetry
            )
        )
    else:
        # Development: Use local persistent storage
        print("Using local ChromaDB at ./chroma_db")
        return chromadb.PersistentClient(path="./chroma_db")


# Initialize client and collection
client = get_chroma_client()
collection = client.get_or_create_collection(name="react_docs")


def clear_collection():
    """Delete all data from the collection."""
    global collection
    client.delete_collection(name="react_docs")
    collection = client.get_or_create_collection(name="react_docs")
    print("Collection cleared")


def add_chunks(chunks: list[dict]):
    """
    Add chunks with embeddings to the collection.

    Args:
        chunks: List of dicts with keys: content, embedding, title, source, chunk_index
    """
    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        ids.append(f"chunk_{i}")
        documents.append(chunk["content"])
        embeddings.append(chunk["embedding"])
        metadatas.append({
            "title": chunk["title"],
            "source": chunk["source"],
            "chunk_index": chunk["chunk_index"]
        })

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"Added {len(chunks)} chunks to the collection")


def get_collection_count():
    """Get the number of documents in the collection."""
    return collection.count()
