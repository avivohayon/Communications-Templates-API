"""
Unit tests for logic_template.py

Tests template business logic including Jinja2 validation and template preview.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.logic.logic_template import TemplateLogic
from src.schemas.schema_template import EmailTemplateIn, SMSTemplateIn, EmailTemplateUpdate
from src.models.enums import ChannelType


class TestTemplateLogicValidation:
    """Test Jinja2 validation in template creation/update."""
    
    @pytest.mark.asyncio
    async def test_create_email_template_valid_syntax(self, mock_db):
        """Creating template with valid Jinja2 should succeed."""
        logic = TemplateLogic()
        
        # Mock DA insert to return fake models with real values
        template_id = uuid4()
        mock_base = MagicMock()
        mock_base.id = template_id
        mock_base.name = "test_template"
        mock_base.channel_type = ChannelType.EMAIL
        mock_base.status = "active"
        mock_base.creation_date = 123456
        mock_base.update_date = 123456
        
        mock_specific = MagicMock()
        mock_specific.content = "Hello {{ name }}, code: {{ code }}"
        mock_specific.subject = "Welcome {{ name }}"
        
        logic.da.insert = AsyncMock(return_value=(mock_base, mock_specific))
        
        schema = EmailTemplateIn(
            name="test_template",
            channel_type=ChannelType.EMAIL,
            subject="Welcome {{ name }}",
            content="Hello {{ name }}, code: {{ code }}"
        )
        
        result = await logic.create(mock_db, schema)
        assert result is not None
        assert result.name == "test_template"
        logic.da.insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_template_invalid_content_syntax_raises_error(self, mock_db):
        """Creating template with invalid content syntax should raise ValueError."""
        logic = TemplateLogic()
        
        schema = EmailTemplateIn(
            name="bad_template",
            channel_type=ChannelType.EMAIL,
            subject="Valid",
            content="Hello {{ name"  # Missing closing bracket
        )
        
        with pytest.raises(ValueError) as exc_info:
            await logic.create(mock_db, schema)
        
        assert "syntax" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_email_template_invalid_subject_syntax_raises_error(self, mock_db):
        """Email template with invalid subject syntax should raise ValueError."""
        logic = TemplateLogic()
        
        schema = EmailTemplateIn(
            name="bad_subject",
            channel_type=ChannelType.EMAIL,
            subject="Welcome {% invalid %}",  # Invalid tag
            content="Valid content"
        )
        
        with pytest.raises(ValueError) as exc_info:
            await logic.create(mock_db, schema)
        
        assert "subject" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_update_template_validates_new_content(self, mock_db):
        """Updating template content should validate new Jinja2 syntax."""
        logic = TemplateLogic()
        
        # Mock get_by_id to return existing template
        mock_base = MagicMock(id=uuid4(), channel_type=ChannelType.EMAIL)
        mock_specific = MagicMock(content="old", subject="old")
        logic.da.get_by_id = AsyncMock(return_value=(mock_base, mock_specific))
        
        update = EmailTemplateUpdate(
            content="New {{ invalid_syntax"  # Invalid!
        )
        
        with pytest.raises(ValueError) as exc_info:
            await logic.update(mock_db, mock_base.id, update)
        
        assert "syntax" in str(exc_info.value).lower()


class TestTemplateLogicPreview:
    """Test template preview with data rendering."""
    
    @pytest.mark.asyncio
    async def test_preview_renders_correctly(self, mock_db):
        """Preview should render template with provided data."""
        logic = TemplateLogic()
        
        # Mock get_by_id to return template
        from src.schemas.schema_template import EmailTemplateOut
        mock_template = EmailTemplateOut(
            id=uuid4(),
            name="test",
            channel_type=ChannelType.EMAIL,
            subject="Hi {{ name }}",
            content="Code: {{ code }}",
            status="active",
            creation_date=123,
            update_date=123
        )
        logic.get_by_id = AsyncMock(return_value=mock_template)
        
        result = await logic.preview(mock_db, mock_template.id, {
            "name": "Aviv",
            "code": "123456"
        })
        
        assert result.rendered_content == "Code: 123456"
        assert result.rendered_subject == "Hi Aviv"
    
    @pytest.mark.asyncio
    async def test_preview_with_missing_variables_raises_error(self, mock_db):
        """CRITICAL: Preview with missing variables should raise ValueError."""
        logic = TemplateLogic()
        
        from src.schemas.schema_template import EmailTemplateOut
        mock_template = EmailTemplateOut(
            id=uuid4(),
            name="test",
            channel_type=ChannelType.EMAIL,
            subject="Hi {{ name }}",
            content="Code: {{ code }}",
            status="active",
            creation_date=123,
            update_date=123
        )
        logic.get_by_id = AsyncMock(return_value=mock_template)
        
        # Missing 'code' variable
        with pytest.raises(ValueError) as exc_info:
            await logic.preview(mock_db, mock_template.id, {"name": "Aviv"})
        
        assert "code" in str(exc_info.value).lower()
