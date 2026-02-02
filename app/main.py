"""
FastAPI application entry point.

This module sets up:
- The FastAPI app instance
- CORS middleware for frontend connectivity
- Route registration
- Database initialization on startup
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.conversations import router as conversations_router
from app.db.database import init_db
from app.auth import init_firebase


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.

    Code before 'yield' runs on startup.
    Code after 'yield' runs on shutdown.
    """
    # Startup: Initialize Firebase Auth
    print("Initializing Firebase...")
    init_firebase()

    # Startup: Create database tables if they don't exist
    print("Initializing database...")
    await init_db()
    print("Database initialized!")

    yield  # App runs here

    # Shutdown: Clean up resources if needed
    print("Shutting down...")


# Create FastAPI app with lifespan handler
app = FastAPI(
    title="React Docs RAG API",
    description="RAG-based Q&A API for React documentation with conversation history",
    version="1.0.0",
    lifespan=lifespan
)

# Allow frontend to connect (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://react-chatbot-pi-tawny.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# - /api/chat - RAG question answering
# - /api/conversations - Conversation history management
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(conversations_router, prefix="/api", tags=["conversations"])


@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "React Docs RAG API is running"}


@app.get("/api/admin/index")
def run_indexing():
    """
    Trigger document indexing.
    WARNING: This clears existing data and re-indexes everything.
    """
    try:
        import os
        from app.processing.pipeline import process_all_documents
        from app.services.embeddings import embed_chunks
        from app.services.vectorstore import add_chunks, clear_collection

        # Check if data folder exists
        data_path = "data/learn"
        if not os.path.exists(data_path):
            return {"error": f"Data path '{data_path}' does not exist", "cwd": os.getcwd(), "files": os.listdir(".")}

        # Clear existing data
        clear_collection()

        # Process documents
        chunks = process_all_documents(data_path)

        if not chunks:
            return {"error": "No chunks created", "data_path": data_path}

        # Generate embeddings
        chunks = embed_chunks(chunks)

        # Store in ChromaDB
        add_chunks(chunks)

        return {"message": f"Indexed {len(chunks)} chunks successfully"}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}
