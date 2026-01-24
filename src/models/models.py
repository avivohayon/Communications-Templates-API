import uuid
from sqlalchemy import Column, String, BigInteger, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.models.enums import ChannelType, MessageStatus


class BaseModel(Base):
    """
    Base model with common fields for all entities.
    
    Common Fields:
    - id: UUID primary key (generated in Python)
    - creation_date: Unix timestamp (UTC, integer)
    - update_date: Unix timestamp (UTC, integer)
    - status: 'active' or 'deleted' (soft deletion)
    """
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creation_date = Column(BigInteger, nullable=False)
    update_date = Column(BigInteger, nullable=False)
    status = Column(String(20), nullable=False, default='active')


# ============================================================
# TEMPLATE MODELS (Class Table Inheritance)
# ============================================================

class Template(BaseModel):
    """
    Base template model - stores only shared metadata.
    
    Class Table Inheritance:
    - Content is stored in channel-specific tables (email_templates, sms_templates)
    - channel_type determines which specific table to join with
    - channel_type is stored as VARCHAR, Python Enum is for validation only
    """
    __tablename__ = "templates"
    
    name = Column(String(255), nullable=False, unique=True, index=True)
    channel_type = Column(String(20), nullable=False, index=True)  # Stores enum value as string


class EmailTemplate(Base):
    """
    Email-specific template data.
    
    Foreign Key: template_id → templates.id (CASCADE delete)
    """
    __tablename__ = "email_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("templates.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    content = Column(Text, nullable=False)
    subject = Column(String(500), nullable=False)
    
    # Relationship to base template
    template = relationship("Template", backref="email_detail", foreign_keys=[template_id])


class SMSTemplate(Base):
    """
    SMS-specific template data.
    
    Foreign Key: template_id → templates.id (CASCADE delete)
    """
    __tablename__ = "sms_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("templates.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    content = Column(Text, nullable=False)
    
    # Relationship to base template
    template = relationship("Template", backref="sms_detail", foreign_keys=[template_id])


# ============================================================
# MESSAGE HISTORY MODELS (Class Table Inheritance)
# ============================================================

class MessageHistory(BaseModel):
    """
    Base message history model - stores shared tracking info.
    
    Class Table Inheritance:
    - Rendered content is stored in channel-specific tables
    - channel_type and status are stored as VARCHAR, Python Enums are for validation only
    """
    __tablename__ = "message_history"
    
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("templates.id"),
        nullable=False,
        index=True
    )
    template_name = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False, index=True)
    channel_type = Column(String(20), nullable=False, index=True)  # Stores enum value as string
    status = Column(String(20), nullable=False, index=True)  # Stores enum value as string
    error_message = Column(Text, nullable=True)
    
    # Relationship
    template = relationship("Template", backref="message_history")


class EmailMessageHistory(Base):
    """
    Email-specific message history data.
    
    Foreign Key: message_history_id → message_history.id (CASCADE delete)
    """
    __tablename__ = "email_message_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_history_id = Column(
        UUID(as_uuid=True),
        ForeignKey("message_history.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    rendered_content = Column(Text, nullable=False)
    rendered_subject = Column(String(500), nullable=False)
    external_message_id = Column(String(255), nullable=True)  # SendGrid message ID
    
    # Relationship
    message_history = relationship("MessageHistory", backref="email_detail", foreign_keys=[message_history_id])


class SMSMessageHistory(Base):
    """
    SMS-specific message history data.
    
    Foreign Key: message_history_id → message_history.id (CASCADE delete)
    """
    __tablename__ = "sms_message_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_history_id = Column(
        UUID(as_uuid=True),
        ForeignKey("message_history.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    rendered_content = Column(Text, nullable=False)
    external_message_id = Column(String(255), nullable=True)  # Twilio SID
    
    # Relationship
    message_history = relationship("MessageHistory", backref="sms_detail", foreign_keys=[message_history_id])


# ============================================================
# RATE LIMIT MODEL
# ============================================================

class RateLimit(BaseModel):
    """
    Rate limiting tracking model.
    
    Tracks message count per recipient within time windows.
    """
    __tablename__ = "rate_limits"
    
    recipient = Column(String(255), nullable=False, index=True)
    message_count = Column(Integer, nullable=False, default=0)
    window_start = Column(BigInteger, nullable=False, index=True)  # Unix timestamp
