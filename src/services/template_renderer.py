"""
Template Renderer Service using Jinja2.

Responsibilities:
- Validate Jinja2 template syntax
- Render templates with data (variables)
- Handle rendering errors gracefully
"""
import logging
from typing import Dict, Any

from jinja2 import Environment, Template, TemplateSyntaxError, UndefinedError

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """
    Service for rendering Jinja2 templates.
    
    Jinja2 Features Used:
    - Variable substitution: {{ variable_name }}
    - Filters: {{ name|upper }}
    - Control structures: {% if condition %} {% for item in list %}
    - Template inheritance (if needed in future)
    
    Example Template:
    ```
    Hello {{ name }}!
    Your verification code is {{ code }}.
    ```
    
    Example Data:
    ```python
    {"name": "John", "code": "123456"}
    ```
    
    Result:
    ```
    Hello John!
    Your verification code is 123456.
    ```
    """
    
    def __init__(self):
        """
        Initialize Jinja2 environment.
        
        Configuration:
        - autoescape=False: Don't auto-escape HTML (we handle plain text and HTML explicitly)
        - trim_blocks=True: Remove first newline after block
        - lstrip_blocks=True: Strip leading whitespace from blocks
        """
        self.env = Environment(
            autoescape=False,  # No auto-escaping (manual control)
            trim_blocks=True,
            lstrip_blocks=True
        )
        logger.debug("TemplateRenderer initialized with Jinja2")
    
    def validate_syntax(self, content: str) -> tuple[bool, str | None]:
        """
        Validate Jinja2 template syntax.
        
        This is used during template creation to catch syntax errors early.
        
        Args:
            content: Template content to validate
        
        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, error_message) if invalid
        
        Examples:
            >>> renderer = TemplateRenderer()
            >>> renderer.validate_syntax("Hello {{ name }}")
            (True, None)
            >>> renderer.validate_syntax("Hello {{ name")
            (False, "unexpected end of template...")
        """
        try:
            # Try to parse the template
            self.env.from_string(content)
            logger.debug("Template syntax validation: PASSED")
            return True, None
            
        except TemplateSyntaxError as e:
            error_msg = f"Template syntax error at line {e.lineno}: {e.message}"
            logger.warning(f"Template syntax validation: FAILED - {error_msg}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error during syntax validation: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def render(self, content: str, data: Dict[str, Any]) -> str:
        """
        Render template with provided data.
        
        Args:
            content: Template content (Jinja2 syntax)
            data: Dictionary of variables to inject into template
        
        Returns:
            Rendered content as string
        
        Raises:
            TemplateSyntaxError: If template has syntax errors
            UndefinedError: If required variables are missing
            Exception: Other rendering errors
        
        Examples:
            >>> renderer = TemplateRenderer()
            >>> renderer.render("Hello {{ name }}!", {"name": "John"})
            'Hello John!'
            >>> renderer.render("Code: {{ code }}", {"code": 123456})
            'Code: 123456'
        """
        try:
            # Create template from string
            template = self.env.from_string(content)
            
            # Render with data
            rendered = template.render(**data)
            
            logger.debug(f"Template rendered successfully (length: {len(rendered)})")
            return rendered
            
        except TemplateSyntaxError as e:
            error_msg = f"Template syntax error at line {e.lineno}: {e.message}"
            logger.error(f"Rendering failed: {error_msg}")
            raise ValueError(error_msg)
            
        except UndefinedError as e:
            error_msg = f"Missing required variable: {str(e)}"
            logger.error(f"Rendering failed: {error_msg}")
            raise ValueError(error_msg)
            
        except Exception as e:
            error_msg = f"Template rendering error: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def render_safe(self, content: str, data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Render template with error handling (no exceptions).
        
        This is useful for preview/testing scenarios where you want to catch errors
        without raising exceptions.
        
        Args:
            content: Template content
            data: Variables to inject
        
        Returns:
            Tuple of (success, result_or_error)
            - (True, rendered_content) if successful
            - (False, error_message) if failed
        
        Examples:
            >>> renderer = TemplateRenderer()
            >>> renderer.render_safe("Hello {{ name }}", {"name": "John"})
            (True, 'Hello John')
            >>> renderer.render_safe("Hello {{ name }}", {})
            (False, "Missing required variable: 'name'...")
        """
        try:
            rendered = self.render(content, data)
            return True, rendered
        except Exception as e:
            return False, str(e)


# Global instance for convenience
template_renderer = TemplateRenderer()
