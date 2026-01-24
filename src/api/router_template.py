"""
Template API Router - CRUD endpoints for message templates.

Endpoints:
- POST /templates/ - Create template
- GET /templates/{id} - Get template by ID
- GET /templates/ - Get all templates (with pagination)
- GET /templates/by-name/{name} - Get template by name
- PUT /templates/{id} - Update template
- DELETE /templates/{id} - Soft delete template
"""
import logging
from typing import Union, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.logic.logic_template import TemplateLogic
from src.schemas.schema_template import (
    EmailTemplateIn, SMSTemplateIn,
    EmailTemplateOut, SMSTemplateOut,
    EmailTemplateUpdate, SMSTemplateUpdate
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])
template_logic = TemplateLogic()


@router.post(
    "/",
    response_model=Union[EmailTemplateOut, SMSTemplateOut],
    status_code=201,
    summary="Create a new template"
)
async def create_template(
    template: Union[EmailTemplateIn, SMSTemplateIn],
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new template (Email or SMS).
    
    **Email Template:**
    - Requires: name, channel_type='email', content, subject
    - Content and subject can use Jinja2 variables: {{ variable_name }}
    
    **SMS Template:**
    - Requires: name, channel_type='sms', content
    - Content can use Jinja2 variables: {{ variable_name }}
    
    **Validation:**
    - Template syntax is validated before saving
    - Name must be unique
    """
    try:
        result = await template_logic.create(db, template)
        logger.info(f"Created template: {result.name}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{template_id}",
    response_model=Union[EmailTemplateOut, SMSTemplateOut],
    summary="Get template by ID"
)
async def get_template_by_id(
    template_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a template by its UUID.
    
    Returns EmailTemplateOut or SMSTemplateOut based on channel_type.
    """
    try:
        result = await template_logic.get_by_id(db, template_id)
        if not result:
            raise HTTPException(status_code=404, detail="Template not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/by-name/{name}",
    response_model=Union[EmailTemplateOut, SMSTemplateOut],
    summary="Get template by name"
)
async def get_template_by_name(
    name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a template by its unique name.
    
    Returns EmailTemplateOut or SMSTemplateOut based on channel_type.
    """
    try:
        result = await template_logic.get_by_name(db, name)
        if not result:
            raise HTTPException(status_code=404, detail="Template not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/",
    response_model=List[Union[EmailTemplateOut, SMSTemplateOut]],
    summary="Get all templates"
)
async def get_all_templates(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all templates with pagination.
    
    Returns a list of EmailTemplateOut and SMSTemplateOut objects.
    """
    try:
        results = await template_logic.get_all(db, skip=skip, limit=limit)
        return results
    except Exception as e:
        logger.error(f"Error getting all templates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put(
    "/{template_id}",
    response_model=Union[EmailTemplateOut, SMSTemplateOut],
    summary="Update template"
)
async def update_template(
    template_id: UUID,
    template: Union[EmailTemplateUpdate, SMSTemplateUpdate],
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing template.
    
    **Updatable fields:**
    - name (must remain unique)
    - content (will be validated)
    - subject (email only, will be validated)
    
    **Note:** Cannot update deleted templates.
    """
    try:
        result = await template_logic.update(db, template_id, template)
        if not result:
            raise HTTPException(status_code=404, detail="Template not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/{template_id}",
    status_code=204,
    summary="Delete template"
)
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a template.
    
    **Note:**
    - This is a soft delete (sets status='deleted')
    - Template data is preserved for audit trails
    - Deleted templates cannot be retrieved via normal queries
    """
    try:
        result = await template_logic.delete(db, template_id)
        if not result:
            raise HTTPException(status_code=404, detail="Template not found")
        return None  # 204 No Content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
