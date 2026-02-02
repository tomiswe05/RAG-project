"""
API endpoints for managing conversations.

This module handles:
- Listing all conversations (for sidebar)
- Getting a single conversation with messages
- Creating new conversations
- Updating conversation titles
- Deleting conversations
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import Conversation, Message
from app.db.schemas import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationSummary,
    ConversationListResponse,
)
from app.auth import get_current_user

# Create a router - this groups related endpoints together
# prefix="/conversations" means all routes here start with /api/conversations
# tags=["conversations"] groups them in the API docs
router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
):
    """
    Get all conversations for the sidebar, scoped to the current user.

    Returns conversations sorted by most recently updated.
    Includes pagination with skip/limit parameters.
    """
    uid = current_user["uid"]

    query = (
        select(Conversation)
        .where(Conversation.user_id == uid)
        .order_by(desc(Conversation.updated_at))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    conversations = result.scalars().all()

    return ConversationListResponse(conversations=conversations)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a single conversation with all its messages.

    Used when user clicks on a conversation in the sidebar.
    Returns 404 if conversation doesn't exist or belongs to another user.
    """
    uid = current_user["uid"]

    query = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id, Conversation.user_id == uid)
    )

    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with id {conversation_id} not found"
        )

    return conversation


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new empty conversation.

    Usually called when user clicks "New Chat".
    Returns the created conversation with its generated ID.
    """
    conversation = Conversation(
        title=data.title or "New Chat",
        user_id=current_user["uid"],
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return conversation


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a conversation (e.g., rename it).

    PATCH means partial update - only provided fields are changed.
    """
    uid = current_user["uid"]

    query = select(Conversation).where(
        Conversation.id == conversation_id, Conversation.user_id == uid
    )
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with id {conversation_id} not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(conversation, field, value)

    await db.commit()
    await db.refresh(conversation)

    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a conversation and all its messages.

    Messages are deleted automatically due to CASCADE relationship.
    Returns 204 No Content on success.
    """
    uid = current_user["uid"]

    query = select(Conversation).where(
        Conversation.id == conversation_id, Conversation.user_id == uid
    )
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with id {conversation_id} not found"
        )

    await db.delete(conversation)
    await db.commit()

    return None
