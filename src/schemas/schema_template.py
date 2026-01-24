from uuid import UUID
from typing import Literal
from pydantic import Field, field_validator

from src.schemas.base_schema import AppBaseSchema, AppSchemaIn, AppSchemaOut, AppSchemaUpdate
from src.models.enums import ChannelType


# ============================================================
# TEMPLATE BASE SCHEMAS
# ============================================================

class TemplateBase(AppBaseSchema):
    """
    Base schema with fields shared by all template types.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique template name",
        examples=["welcome_email", "verification_sms"]
    )
    channel_type: ChannelType = Field(
        ...,
        description="Channel type: email or sms"
    )


class TemplateOut(TemplateBase, AppSchemaOut):
    """
    Base output schema for templates.
    Includes all base template fields + common fields from AppSchemaOut.
    """
    pass


# ============================================================
# EMAIL TEMPLATE SCHEMAS
# ============================================================

class EmailTemplateIn(TemplateBase, AppSchemaIn):
    """
    Schema for creating email templates.
    
    Validation:
    - channel_type must be 'email'
    - subject is required
    - content is required
    """
    channel_type: Literal[ChannelType.EMAIL] = Field(
        default=ChannelType.EMAIL,
        description="Must be 'email'"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Email template content (HTML or plain text with Jinja2 variables)",
        examples=["<h1>Hello {{name}}</h1><p>Welcome to our service!</p>"]
    )
    subject: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Email subject line (can include Jinja2 variables)",
        examples=["Welcome {{name}}!"]
    )


class EmailTemplateOut(TemplateOut):
    """
    Schema for email template responses.
    """
    content: str
    subject: str


class EmailTemplateUpdate(AppSchemaUpdate):
    """
    Schema for updating email templates.
    All fields are optional.
    """
    name: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = Field(None, min_length=1)
    subject: str | None = Field(None, min_length=1, max_length=500)


# ============================================================
# SMS TEMPLATE SCHEMAS
# ============================================================

class SMSTemplateIn(TemplateBase, AppSchemaIn):
    """
    Schema for creating SMS templates.
    
    Validation:
    - channel_type must be 'sms'
    - content is required
    """
    channel_type: Literal[ChannelType.SMS] = Field(
        default=ChannelType.SMS,
        description="Must be 'sms'"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="SMS template content (plain text with Jinja2 variables)",
        examples=["Hi {{name}}! Your code is {{code}}."]
    )


class SMSTemplateOut(TemplateOut):
    """
    Schema for SMS template responses.
    """
    content: str


class SMSTemplateUpdate(AppSchemaUpdate):
    """
    Schema for updating SMS templates.
    All fields are optional.
    """
    name: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = Field(None, min_length=1)


# ============================================================
# POLYMORPHIC UNIONS
# ============================================================

# Discriminated union for template input (FastAPI will handle based on channel_type)
TemplateIn = EmailTemplateIn | SMSTemplateIn

# Union for template output
TemplateOut = EmailTemplateOut | SMSTemplateOut

# Union for template update
TemplateUpdate = EmailTemplateUpdate | SMSTemplateUpdate
