from typing import Dict, Any
from pydantic import BaseModel, Field


class TemplatePreviewRequest(BaseModel):
    """
    Schema for template preview requests.
    """
    data: Dict[str, Any] = Field(
        ...,
        description="Data to render template variables (Jinja2 context)",
        examples=[{"name": "John", "code": "123456"}]
    )


class TemplatePreviewResponse(BaseModel):
    """
    Schema for template preview responses.
    Works for both email and SMS templates.
    """
    rendered_content: str = Field(..., description="Rendered content (HTML for email, text for SMS)")
    rendered_subject: str | None = Field(None, description="Rendered subject (email only)")

