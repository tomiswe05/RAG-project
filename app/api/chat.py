"""
Chat endpoint for RAG-based question answering.

This module handles:
- Receiving user questions
- Searching for relevant documentation
- Generating answers with LLM
- Saving messages to conversation history
"""

from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import Conversation, Message
from app.db.schemas import ChatRequest, ChatResponse, SourceInfo
from app.services.retrieval import hybrid_search
from app.services.llm import generate_answer
from app.auth import get_current_user

router = APIRouter()


def generate_title_from_question(question: str, max_length: int = 50) -> str:
    """
    Generate a conversation title from the first question.

    Takes the first sentence or truncates at max_length.
    """
    # Take first sentence or whole question if no period
    title = question.split('.')[0].split('?')[0].split('!')[0]

    # Truncate if too long
    if len(title) > max_length:
        title = title[:max_length - 3] + "..."

    return title.strip()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Receive a question, search for relevant chunks, generate answer.

    If conversation_id is provided, adds messages to existing conversation.
    If not provided, creates a new conversation.

    The conversation_id is returned so the frontend can continue the conversation.
    """

    conversation = None

    uid = current_user["uid"]

    # Step 1: Get or create conversation
    if request.conversation_id:
        # Load existing conversation - scoped to current user
        query = select(Conversation).where(
            Conversation.id == request.conversation_id,
            Conversation.user_id == uid,
        )
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {request.conversation_id} not found"
            )
    else:
        # Create new conversation with title from question
        title = generate_title_from_question(request.question)
        conversation = Conversation(title=title, user_id=uid)
        db.add(conversation)
        await db.flush()  # Generates the ID without committing

    # Step 2: Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.question
    )
    db.add(user_message)

    # Step 3: Retrieve relevant chunks using hybrid search
    results = hybrid_search(
        query=request.question,
        top_k=request.top_k,
        filter=request.filter
    )

    # Step 4: Generate answer using LLM
    answer = generate_answer(
        question=request.question,
        context_chunks=results
    )

    # Step 5: Extract sources for response
    sources = [
        SourceInfo(
            title=r["metadata"].get("title", "Unknown"),
            source=r["metadata"].get("source", "Unknown")
        )
        for r in results
    ]

    # Step 6: Save assistant message with sources
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        sources=[s.model_dump() for s in sources]  # Convert Pydantic to dict for JSON storage
    )
    db.add(assistant_message)

    # Step 7: Update conversation's updated_at timestamp
    conversation.updated_at = datetime.utcnow()

    # Step 8: Commit all changes
    await db.commit()

    # Return response with conversation_id
    return ChatResponse(
        conversation_id=conversation.id,
        question=request.question,
        answer=answer,
        sources=sources
    )
