"""
Unit tests for template_renderer.py

Tests Jinja2 syntax validation and StrictUndefined behavior for catching missing variables.
"""
import pytest
from src.services.template_renderer import template_renderer


class TestTemplateRendererSyntaxValidation:
    """Test Jinja2 syntax validation during template creation."""
    
    def test_validate_valid_template(self):
        """Valid template should pass validation."""
        is_valid, error = template_renderer.validate_syntax("Hello {{ name }}")
        assert is_valid is True
        assert error is None
    
    def test_validate_invalid_syntax_unclosed_bracket(self):
        """Template with unclosed bracket should fail."""
        is_valid, error = template_renderer.validate_syntax("Hello {{ name")
        assert is_valid is False
        assert "unexpected end" in error.lower()
    
    def test_validate_invalid_syntax_bad_tag(self):
        """Template with invalid tag should fail."""
        is_valid, error = template_renderer.validate_syntax("{% invalid_tag %}")
        assert is_valid is False
    
    def test_validate_complex_template(self):
        """Complex valid template should pass."""
        template = "{% if premium %}VIP: {{ name }}{% else %}User: {{ name }}{% endif %}"
        is_valid, error = template_renderer.validate_syntax(template)
        assert is_valid is True


class TestTemplateRendererStrictUndefined:
    """
    Test StrictUndefined behavior - missing variables should raise errors.
    
    CRITICAL: These tests validate the bug fix where missing variables were
    silently rendered as empty strings instead of raising errors.
    """
    
    def test_render_with_all_variables_provided(self):
        """Rendering with all variables should succeed."""
        content = "Hello {{ name }}, code: {{ code }}"
        data = {"name": "Aviv", "code": "123456"}
        
        result = template_renderer.render(content, data)
        assert result == "Hello Aviv, code: 123456"
    
    def test_render_with_missing_variable_raises_error(self):
        """CRITICAL: Missing variable should raise ValueError (StrictUndefined)."""
        content = "Hello {{ name }}, code: {{ code }}"
        data = {"name": "Aviv"}  # Missing 'code'
        
        with pytest.raises(ValueError) as exc_info:
            template_renderer.render(content, data)
        
        assert "code" in str(exc_info.value).lower()
        assert "undefined" in str(exc_info.value).lower()
    
    def test_render_with_wrong_variable_name_raises_error(self):
        """
        CRITICAL: Wrong variable names should raise ValueError.
        
        This tests the exact scenario reported by the user:
        Template expects {{ name }} but data has {"name2": "Aviv"}
        """
        content = "Hello {{ name }}"
        data = {"name2": "Aviv"}  # Wrong key - should fail!
        
        with pytest.raises(ValueError) as exc_info:
            template_renderer.render(content, data)
        
        assert "name" in str(exc_info.value).lower()
    
    def test_render_with_empty_data_raises_error(self):
        """Empty data dict should fail if template has variables."""
        content = "Hello {{ name }}"
        data = {}
        
        with pytest.raises(ValueError) as exc_info:
            template_renderer.render(content, data)
        
        assert "name" in str(exc_info.value).lower()
    
    def test_render_safe_returns_error_for_missing_variable(self):
        """render_safe should return error tuple instead of raising."""
        content = "Hello {{ name }}"
        data = {}
        
        success, result = template_renderer.render_safe(content, data)
        assert success is False
        assert "name" in result.lower()


class TestTemplateRendererEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_render_template_without_variables(self):
        """Static template (no variables) should render as-is."""
        content = "Hello world!"
        result = template_renderer.render(content, {})
        assert result == "Hello world!"
    
    def test_render_with_filters(self):
        """Jinja2 filters should work correctly."""
        content = "Hello {{ name|upper }}"
        data = {"name": "aviv"}
        result = template_renderer.render(content, data)
        assert result == "Hello AVIV"
    
    def test_render_with_conditionals(self):
        """Conditional logic should work."""
        content = "{% if premium %}VIP{% else %}Regular{% endif %}"
        
        result1 = template_renderer.render(content, {"premium": True})
        assert result1 == "VIP"
        
        result2 = template_renderer.render(content, {"premium": False})
        assert result2 == "Regular"
