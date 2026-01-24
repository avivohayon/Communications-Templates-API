from typing import Dict, Any
from pydantic import BaseModel, Field

from src.models.enums import ChannelType


class TemplatePreviewRequest(BaseModel):
    """
    Schema for template preview requests.
    """
    data: Dict[str, Any] = Field(
        ...,
        description="Data to render template variables (Jinja2 context)",
        examples=[{"name": "John", "code": "123456"}]
    )


class EmailTemplatePreviewResponse(BaseModel):
    """
    Schema for email template preview responses.
    """
    rendered_content: str = Field(..., description="Rendered email HTML/text content")
    rendered_subject: str = Field(..., description="Rendered email subject")


class SMSTemplatePreviewResponse(BaseModel):
    """
    Schema for SMS template preview responses.
    """
    rendered_content: str = Field(..., description="Rendered SMS text content")


# Union for preview responses
TemplatePreviewResponse = EmailTemplatePreviewResponse | SMSTemplatePreviewResponse
