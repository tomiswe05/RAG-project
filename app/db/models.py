"""
Database models for chat history.

These classes define the structure of our database tables.
SQLAlchemy ORM (Object-Relational Mapping) lets us work with
database rows as Python objects instead of writing raw SQL.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class Conversation(Base):
    """
    Represents a chat conversation.

    One conversation has many messages.
    Later, we'll link this to a user when we add authentication.

    Table: conversations
    """
    __tablename__ = "conversations"

    # Primary key - UUID is better than auto-increment for distributed systems
    # default=uuid.uuid4 generates a new UUID automatically when creating a row
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Title shown in sidebar - generated from first message
    # nullable=False means this field is required
    title = Column(String(255), nullable=False, default="New Chat")

    # For future user authentication - nullable for now
    # When we add users, we'll set this to the user's ID
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Timestamps for sorting and display
    # default=datetime.utcnow sets the value when row is created
    # onupdate=datetime.utcnow automatically updates when row is modified
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to messages
    # back_populates creates a two-way link (conversation.messages <-> message.conversation)
    # cascade="all, delete-orphan" means deleting a conversation deletes its messages too
    # order_by sorts messages by creation time when accessed
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    def __repr__(self):
        """String representation for debugging"""
        return f"<Conversation(id={self.id}, title='{self.title}')>"


class Message(Base):
    """
    Represents a single message in a conversation.

    Each message belongs to one conversation.
    Role is either 'user' or 'assistant'.

    Table: messages
    """
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key links this message to a conversation
    # ondelete="CASCADE" means if conversation is deleted, message is deleted too
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Index for faster lookups by conversation_id
    )

    # 'user' or 'assistant'
    role = Column(String(20), nullable=False)

    # The actual message text
    content = Column(Text, nullable=False)

    # Sources from RAG retrieval (only for assistant messages)
    # JSON type stores Python dicts/lists directly
    # Example: [{"title": "Hooks Guide", "source": "hooks.md"}, ...]
    sources = Column(JSON, nullable=True)

    # When was this message sent
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship back to conversation
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        """String representation for debugging"""
        return f"<Message(id={self.id}, role='{self.role}', content='{self.content[:50]}...')>"
