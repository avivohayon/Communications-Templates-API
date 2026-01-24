from uuid import UUID
from typing import Dict, Any, List
from pydantic import BaseModel, Field, model_validator

from src.models.enums import ChannelType


class SendMessageRequest(BaseModel):
    """
    Schema for sending messages via templates.
    
    Validation:
    - At least one of template_id or template_name must be provided
    - If both provided, template_id takes priority
    """
    template_id: UUID | None = Field(
        None,
        description="Template UUID (takes priority over template_name)"
    )
    template_name: str | None = Field(
        None,
        description="Template name (used if template_id not provided)"
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Data to render template variables (Jinja2 context)",
        examples=[{"name": "John", "code": "123456"}]
    )
    to: List[str] = Field(
        ...,
        min_length=1,
        description="List of recipient email addresses or phone numbers",
        examples=[["user@example.com"], ["+15005550006"]]
    )
    
    @model_validator(mode='after')
    def check_template_identifier(self):
        """Ensure at least one of template_id or template_name is provided."""
        if not self.template_id and not self.template_name:
            raise ValueError("At least one of template_id or template_name must be provided")
        return self


class MessageRecipientResult(BaseModel):
    """
    Schema for per-recipient message send result.
    """
    recipient: str = Field(..., description="Recipient address (email or phone)")
    status: str = Field(..., description="Status: 'success' or 'failed'")
    error_message: str | None = Field(None, description="Error message if status='failed'")
    external_message_id: str | None = Field(
        None,
        description="External API message ID (SendGrid message ID or Twilio SID)"
    )


class SendMessageResponse(BaseModel):
    """
    Schema for send message response.
    
    Supports partial success: Some recipients may succeed while others fail.
    """
    template_id: UUID = Field(..., description="Template UUID that was used")
    template_name: str = Field(..., description="Template name that was used")
    channel_type: ChannelType = Field(..., description="Channel type (email or sms)")
    results: List[MessageRecipientResult] = Field(
        ...,
        description="Per-recipient results"
    )
    total_recipients: int = Field(..., description="Total number of recipients")
    successful_count: int = Field(..., description="Number of successful sends")
    failed_count: int = Field(..., description="Number of failed sends")
