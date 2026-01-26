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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.

    Code before 'yield' runs on startup.
    Code after 'yield' runs on shutdown.
    """
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
# In production, replace "*" with your actual frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
