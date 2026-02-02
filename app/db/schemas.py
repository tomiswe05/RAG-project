"""
Pydantic schemas for request/response validation.

These define the shape of data going IN and OUT of our API.
FastAPI uses these to:
1. Validate incoming JSON (reject invalid requests)
2. Serialize responses (convert Python objects to JSON)
3. Generate API documentation automatically
"""

from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# MESSAGE SCHEMAS
# =============================================================================

class MessageBase(BaseModel):
    """
    Base schema with fields common to all message operations.
    Other message schemas inherit from this.
    """
    role: str = Field(..., description="Who sent the message: 'user' or 'assistant'")
    content: str = Field(..., description="The message text")


class MessageCreate(MessageBase):
    """
    Schema for creating a new message.
    Used when saving messages to a conversation.

    The '...' in Field(...) means the field is required.
    """
    sources: Optional[list[dict]] = Field(
        default=None,
        description="Sources from RAG retrieval (only for assistant messages)"
    )


class MessageResponse(MessageBase):
    """
    Schema for returning a message in API responses.
    Includes the database-generated fields (id, created_at).
    """
    id: UUID
    sources: Optional[list[dict]] = None
    created_at: datetime

    class Config:
        # This tells Pydantic to read data from SQLAlchemy models
        # Without this, it can't convert SQLAlchemy objects to JSON
        from_attributes = True


# =============================================================================
# CONVERSATION SCHEMAS
# =============================================================================

class ConversationBase(BaseModel):
    """Base schema for conversations."""
    title: str = Field(default="New Chat", description="Conversation title for sidebar")


class ConversationCreate(BaseModel):
    """
    Schema for creating a new conversation.
    Title is optional - we'll generate it from the first message if not provided.
    """
    title: Optional[str] = Field(
        default=None,
        description="Optional title. If not provided, generated from first message."
    )


class ConversationUpdate(BaseModel):
    """
    Schema for updating a conversation (e.g., renaming).
    All fields optional since it's a PATCH operation.
    """
    title: Optional[str] = Field(default=None, description="New title for the conversation")


class ConversationSummary(BaseModel):
    """
    Schema for conversation list (sidebar).
    Lightweight - doesn't include messages, just metadata.
    """
    id: UUID
    title: str
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """
    Schema for returning a full conversation with messages.
    Used when loading a conversation from the sidebar.
    """
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """
    Schema for the GET /api/conversations endpoint.
    Returns a list of conversation summaries for the sidebar.
    """
    conversations: list[ConversationSummary]


# =============================================================================
# CHAT SCHEMAS (Updated)
# =============================================================================

class ChatRequest(BaseModel):
    """
    Schema for the POST /api/chat endpoint.
    Now includes optional conversation_id to continue existing conversations.
    """
    question: str = Field(..., description="The user's question")
    conversation_id: Optional[UUID] = Field(
        default=None,
        description="ID of existing conversation. If not provided, creates a new one."
    )
    top_k: int = Field(
        default=5,
        ge=1,  # Greater than or equal to 1
        le=20,  # Less than or equal to 20
        description="Number of documents to retrieve"
    )
    filter: Optional[dict] = Field(
        default=None,
        description="Optional metadata filter for retrieval"
    )


class SourceInfo(BaseModel):
    """Schema for a single source document."""
    title: str
    source: str


class ChatResponse(BaseModel):
    """
    Schema for the POST /api/chat response.
    Now includes conversation_id so frontend can continue the conversation.
    conversation_id is null for anonymous (unauthenticated) users.
    """
    conversation_id: Optional[UUID] = Field(default=None, description="ID of the conversation (null for anonymous users)")
    question: str
    answer: str
    sources: list[SourceInfo]
