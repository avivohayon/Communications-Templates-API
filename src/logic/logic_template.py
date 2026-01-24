"""
Template Logic Layer with CTI and Jinja2 validation.

This logic layer does NOT inherit from BaseLogic because CTI requires custom handling:
- Must work with TWO models (base + specific)
- Must determine correct schema type based on channel_type
- Must validate Jinja2 syntax before saving
"""
import logging
from typing import Optional, List, Union, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.das.da_template import TemplateDA
from src.models.enums import ChannelType
from src.schemas.schema_template import (
    EmailTemplateIn, SMSTemplateIn,
    EmailTemplateOut, SMSTemplateOut,
    EmailTemplateUpdate, SMSTemplateUpdate
)
from src.schemas.schema_preview import TemplatePreviewResponse
from src.services.template_renderer import template_renderer

logger = logging.getLogger(__name__)


class TemplateLogic:
    """
    Business Logic for Template entities with CTI support.
    
    Responsibilities:
    - Validate Jinja2 template syntax before saving
    - Convert between schemas and DA layer dicts
    - Handle CTI model pairs → correct schema type
    - Business rules (name uniqueness, etc.)
    """
    
    def __init__(self):
        """Initialize TemplateLogic with TemplateDA."""
        self.da: TemplateDA = TemplateDA()  # Explicit type hint for IDE
        logger.debug("Initialized TemplateLogic")
    
    async def create(
        self,
        db: AsyncSession,
        schema: Union[EmailTemplateIn, SMSTemplateIn]
    ) -> Union[EmailTemplateOut, SMSTemplateOut]:
        """
        Create a new template with Jinja2 validation.
        
        Flow:
        1. Validate Jinja2 syntax (early rejection)
        2. Convert schema to dict
        3. Call DA to insert (CTI: 2 tables)
        4. Convert models back to appropriate Out schema
        
        Args:
            db: Database session
            schema: EmailTemplateIn or SMSTemplateIn
        
        Returns:
            EmailTemplateOut or SMSTemplateOut (based on channel_type)
        
        Raises:
            ValueError: Invalid Jinja2 syntax or business rule violation
        """
        try:
            # Validate Jinja2 syntax
            is_valid, error_msg = template_renderer.validate_syntax(schema.content)
            if not is_valid:
                logger.error(f"Template validation failed: {error_msg}")
                raise ValueError(f"Invalid template syntax: {error_msg}")
            
            # Validate subject if email
            if schema.channel_type == ChannelType.EMAIL:
                is_valid, error_msg = template_renderer.validate_syntax(schema.subject)
                if not is_valid:
                    logger.error(f"Subject validation failed: {error_msg}")
                    raise ValueError(f"Invalid subject syntax: {error_msg}")
            
            # Convert schema to dict
            template_data = schema.model_dump()
            channel_type = template_data.pop('channel_type')  # Remove for DA
            
            logger.info(f"Creating {channel_type.value} template: {schema.name}")
            
            # Call DA (returns tuple of base + specific models)
            base_model, specific_model = await self.da.insert(
                db, template_data, channel_type
            )
            
            # Convert models to appropriate Out schema
            result = self._models_to_schema(base_model, specific_model)
            
            logger.info(f"Created template id={base_model.id}, name={base_model.name}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise
    
    async def get_by_id(
        self,
        db: AsyncSession,
        template_id: UUID
    ) -> Optional[Union[EmailTemplateOut, SMSTemplateOut]]:
        """
        Get template by ID.
        
        Args:
            db: Database session
            template_id: Template UUID
        
        Returns:
            EmailTemplateOut or SMSTemplateOut, or None if not found
        """
        try:
            result = await self.da.get_by_id(db, template_id)
            if not result:
                return None
            
            base_model, specific_model = result
            return self._models_to_schema(base_model, specific_model)
            
        except Exception as e:
            logger.error(f"Error getting template id={template_id}: {e}")
            raise
    
    async def get_by_name(
        self,
        db: AsyncSession,
        name: str
    ) -> Optional[Union[EmailTemplateOut, SMSTemplateOut]]:
        """
        Get template by name.
        
        Args:
            db: Database session
            name: Template name (unique)
        
        Returns:
            EmailTemplateOut or SMSTemplateOut, or None if not found
        """
        try:
            result = await self.da.get_by_name(db, name)
            if not result:
                return None
            
            base_model, specific_model = result
            return self._models_to_schema(base_model, specific_model)
            
        except Exception as e:
            logger.error(f"Error getting template name={name}: {e}")
            raise
    
    async def get_by_id_or_name(
        self,
        db: AsyncSession,
        template_id: UUID | None = None,
        template_name: str | None = None
    ) -> Optional[Union[EmailTemplateOut, SMSTemplateOut]]:
        """
        Get template by ID or name (priority: ID > name).
        
        Args:
            db: Database session
            template_id: Template UUID (priority)
            template_name: Template name (fallback)
        
        Returns:
            EmailTemplateOut or SMSTemplateOut, or None if not found
        """
        result = await self.da.get_by_id_or_name(db, template_id, template_name)
        if not result:
            return None
        
        base_model, specific_model = result
        return self._models_to_schema(base_model, specific_model)
    
    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Union[EmailTemplateOut, SMSTemplateOut]]:
        """
        Get all templates with pagination.
        
        Args:
            db: Database session
            skip: Pagination offset
            limit: Max results
        
        Returns:
            List of EmailTemplateOut or SMSTemplateOut
        """
        try:
            results = await self.da.get_all(db, skip, limit)
            
            # Convert each (base, specific) tuple to schema
            schemas = [
                self._models_to_schema(base, specific)
                for base, specific in results
            ]
            
            logger.debug(f"Retrieved {len(schemas)} templates")
            return schemas
            
        except Exception as e:
            logger.error(f"Error getting all templates: {e}")
            raise
    
    async def update(
        self,
        db: AsyncSession,
        template_id: UUID,
        schema: Union[EmailTemplateUpdate, SMSTemplateUpdate]
    ) -> Optional[Union[EmailTemplateOut, SMSTemplateOut]]:
        """
        Update template with Jinja2 validation.
        
        Args:
            db: Database session
            template_id: Template UUID
            schema: EmailTemplateUpdate or SMSTemplateUpdate
        
        Returns:
            Updated EmailTemplateOut or SMSTemplateOut, or None if not found
        """
        try:
            # Get existing to determine channel_type
            existing = await self.da.get_by_id(db, template_id)
            if not existing:
                return None
            
            base_model, _ = existing
            channel_type = base_model.channel_type
            
            # Convert schema to dict (exclude unset)
            update_data = schema.model_dump(exclude_unset=True)
            
            if not update_data:
                logger.warning("No fields provided for update")
                return await self.get_by_id(db, template_id)
            
            # Validate Jinja2 if content or subject updated
            if 'content' in update_data:
                is_valid, error_msg = template_renderer.validate_syntax(update_data['content'])
                if not is_valid:
                    raise ValueError(f"Invalid template syntax: {error_msg}")
            
            if 'subject' in update_data:
                is_valid, error_msg = template_renderer.validate_syntax(update_data['subject'])
                if not is_valid:
                    raise ValueError(f"Invalid subject syntax: {error_msg}")
            
            logger.info(f"Updating template id={template_id}")
            
            # Call DA
            result = await self.da.update(db, template_id, update_data, channel_type)
            if not result:
                return None
            
            base_model, specific_model = result
            return self._models_to_schema(base_model, specific_model)
            
        except Exception as e:
            logger.error(f"Error updating template id={template_id}: {e}")
            raise
    
    async def delete(
        self,
        db: AsyncSession,
        template_id: UUID
    ) -> bool:
        """
        Soft delete template.
        
        Args:
            db: Database session
            template_id: Template UUID
        
        Returns:
            True if deleted, False if not found
        """
        try:
            logger.info(f"Deleting template id={template_id}")
            result = await self.da.delete(db, template_id)
            
            if result:
                logger.info(f"Deleted template id={template_id}")
            else:
                logger.warning(f"Template id={template_id} not found for delete")
            
            return result
            
        except Exception as e:
            logger.error(f"Error deleting template id={template_id}: {e}")
            raise
    
    def _models_to_schema(
        self,
        base_model,
        specific_model
    ) -> Union[EmailTemplateOut, SMSTemplateOut]:
        """
        Convert CTI models to appropriate Out schema.
        
        Args:
            base_model: Template (base)
            specific_model: EmailTemplate or SMSTemplate
        
        Returns:
            EmailTemplateOut or SMSTemplateOut
        """
        # Combine base + specific data
        data = {
            # From base model
            'id': base_model.id,
            'name': base_model.name,
            'channel_type': base_model.channel_type,
            'creation_date': base_model.creation_date,
            'update_date': base_model.update_date,
            'status': base_model.status,
            # From specific model
            'content': specific_model.content
        }
        
        # Add subject if email
        if base_model.channel_type == ChannelType.EMAIL:
            data['subject'] = specific_model.subject
            return EmailTemplateOut(**data)
        else:
            return SMSTemplateOut(**data)
    
    async def preview(
        self,
        db: AsyncSession,
        template_id: UUID,
        data: Dict[str, Any]
    ) -> Optional[TemplatePreviewResponse]:
        """
        Render template with provided data without sending (preview).
        
        This allows users to test template rendering before actually sending messages.
        
        Args:
            db: Database session
            template_id: Template UUID
            data: Dictionary of variables to inject into template
        
        Returns:
            TemplatePreviewResponse with rendered content and subject (if email)
            None if template not found
        
        Raises:
            ValueError: Template rendering errors (invalid syntax, missing variables)
        """
        try:
            logger.info(f"Generating preview for template id={template_id}")
            
            # Fetch template
            template = await self.get_by_id(db, template_id)
            if not template:
                logger.warning(f"Template id={template_id} not found for preview")
                return None
            
            # Render content
            rendered_content = template_renderer.render(template.content, data)
            logger.debug(f"Template content rendered successfully (length: {len(rendered_content)})")
            
            # Render subject if email
            rendered_subject = None
            if template.channel_type == ChannelType.EMAIL:
                if not template.subject:
                    raise ValueError("Email template missing subject")
                rendered_subject = template_renderer.render(template.subject, data)
                logger.debug(f"Template subject rendered successfully")
            
            # Build response
            response = TemplatePreviewResponse(
                rendered_content=rendered_content,
                rendered_subject=rendered_subject
            )
            
            logger.info(f"Preview generated successfully for template id={template_id}")
            return response
            
        except ValueError as e:
            logger.error(f"Template rendering error during preview: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating preview for template id={template_id}: {e}")
            raise
