import re
from uuid import UUID
from typing import Dict, Any, List
from pydantic import BaseModel, Field, model_validator, field_validator

from src.models.enums import ChannelType


class SendMessageRequest(BaseModel):
    """
    Schema for sending messages via templates.
    
    Validation:
    - At least one of template_id or template_name must be provided
    - If both provided, template_id takes priority
    - Recipients must be valid email addresses OR phone numbers
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
    
    @field_validator('to')
    @classmethod
    def validate_recipients(cls, recipients: List[str]) -> List[str]:
        """
        Validate that each recipient is either a valid email or phone number.
        
        Email format: standard email validation
        Phone format: E.164 format (+[country code][number], 7-15 digits)
        
        Raises:
            ValueError: If any recipient is invalid
        """
        # Email regex (basic but covers most cases)
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        # Phone regex (E.164 format: +[1-9][0-9]{6,14})
        # Examples: +15005550006, +972501234567, +441234567890
        phone_pattern = re.compile(
            r'^\+[1-9]\d{6,14}$'
        )
        
        invalid_recipients = []
        
        for recipient in recipients:
            recipient = recipient.strip()
            
            # Check if valid email
            is_valid_email = email_pattern.match(recipient)
            
            # Check if valid phone (E.164 format)
            is_valid_phone = phone_pattern.match(recipient)
            
            if not is_valid_email and not is_valid_phone:
                invalid_recipients.append(recipient)
        
        if invalid_recipients:
            raise ValueError(
                f"Invalid recipient(s): {', '.join(invalid_recipients)}. "
                f"Recipients must be valid email addresses (e.g., user@example.com) "
                f"or phone numbers in E.164 format (e.g., +15005550006)"
            )
        
        return recipients
    
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
