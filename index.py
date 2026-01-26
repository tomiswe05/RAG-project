"""
Run this script ONCE to index all your documents.

This will:
1. Load all markdown files
2. Clean and chunk them
3. Generate embeddings
4. Store in ChromaDB
"""

from app.processing.pipeline import process_all_documents
from app.services.embeddings import embed_chunks
from app.services.vectorstore import add_chunks, clear_collection

# Clear existing data (so you can run this multiple times)
print("Clearing existing data...")
clear_collection()

# Step 1: Run pipeline (load → clean → chunk → metadata)
print("\nStep 1: Processing documents...")
chunks = process_all_documents("data/learn")

# Step 2: Generate embeddings for all chunks
print("\nStep 2: Generating embeddings...")
chunks = embed_chunks(chunks)

# Step 3: Store in ChromaDB
print("\nStep 3: Storing in ChromaDB...")
add_chunks(chunks)

print("\nDone! Your documents are indexed.")
