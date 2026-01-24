from uuid import UUID
from typing import Literal
from pydantic import Field

from src.schemas.base_schema import AppBaseSchema, AppSchemaOut
from src.models.enums import ChannelType, MessageStatus


# ============================================================
# MESSAGE HISTORY BASE SCHEMAS
# ============================================================

class MessageHistoryBase(AppBaseSchema):
    """
    Base schema with fields shared by all message history types.
    """
    template_id: UUID = Field(..., description="Template UUID used for this message")
    template_name: str = Field(..., description="Template name used for this message")
    recipient: str = Field(..., description="Recipient address (email or phone)")
    channel_type: ChannelType = Field(..., description="Channel type (email or sms)")
    status: MessageStatus = Field(..., description="Message delivery status")
    error_message: str | None = Field(None, description="Error message if status='failed'")


class MessageHistoryOut(MessageHistoryBase, AppSchemaOut):
    """
    Base output schema for message history.
    """
    pass


# ============================================================
# EMAIL MESSAGE HISTORY SCHEMAS
# ============================================================

class EmailMessageHistoryOut(MessageHistoryOut):
    """
    Schema for email message history responses.
    """
    rendered_content: str = Field(..., description="Rendered email HTML/text content")
    rendered_subject: str = Field(..., description="Rendered email subject")
    external_message_id: str | None = Field(None, description="SendGrid message ID")


# ============================================================
# SMS MESSAGE HISTORY SCHEMAS
# ============================================================

class SMSMessageHistoryOut(MessageHistoryOut):
    """
    Schema for SMS message history responses.
    """
    rendered_content: str = Field(..., description="Rendered SMS text content")
    external_message_id: str | None = Field(None, description="Twilio message SID")


# ============================================================
# FILTER SCHEMA
# ============================================================

class MessageHistoryFilter(AppBaseSchema):
    """
    Schema for filtering message history queries.
    All fields are optional.
    """
    channel_type: ChannelType | None = Field(None, description="Filter by channel type")
    template_id: UUID | None = Field(None, description="Filter by template UUID")
    template_name: str | None = Field(None, description="Filter by template name")
    recipient: str | None = Field(None, description="Filter by recipient")
    status: MessageStatus | None = Field(None, description="Filter by status")
    skip: int = Field(0, ge=0, description="Number of records to skip (pagination)")
    limit: int = Field(100, ge=1, le=1000, description="Max number of records to return")
