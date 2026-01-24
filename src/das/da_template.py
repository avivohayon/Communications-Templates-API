"""
Template Data Access Layer with Class Table Inheritance (CTI) support.

This DA does NOT inherit from BaseDA because CTI requires custom logic:
- Templates are split across multiple tables (templates + email_templates/sms_templates)
- Need to handle JOIN operations
- Need to insert into TWO tables in a transaction
- Need to return BOTH base and specific models
"""
import logging
from typing import Optional, Tuple, List, Union
from uuid import UUID, uuid4

from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.models import Template, EmailTemplate, SMSTemplate
from src.models.enums import ChannelType
from src.das.base_da import get_utc_timestamp

logger = logging.getLogger(__name__)


class TemplateDA:
    """
    Data Access Layer for Template entities with CTI support.
    
    CTI Design:
    - Base template metadata in 'templates' table
    - Channel-specific data in 'email_templates' or 'sms_templates' tables
    - All operations require handling both tables
    """
    
    async def insert(
        self,
        db: AsyncSession,
        template_data: dict,
        channel_type: ChannelType
    ) -> Tuple[Template, Union[EmailTemplate, SMSTemplate]]:
        """
        Insert a new template (CTI: inserts into TWO tables).
        
        Transaction Flow:
        1. Insert into 'templates' table (base metadata)
        2. Insert into 'email_templates' or 'sms_templates' (channel-specific data)
        3. Return both models
        
        Args:
            db: Database session
            template_data: Dict with 'name', 'content', and optionally 'subject'
            channel_type: Email or SMS
        
        Returns:
            Tuple of (Template, EmailTemplate/SMSTemplate)
        """
        try:
            # Generate IDs
            template_id = uuid4()
            specific_id = uuid4()
            timestamp = get_utc_timestamp()
            
            # Step 1: Insert into base 'templates' table
            base_template = Template(
                id=template_id,
                name=template_data['name'],
                channel_type=channel_type,
                creation_date=timestamp,
                update_date=timestamp,
                status='active'
            )
            db.add(base_template)
            await db.flush()  # Flush to get the ID for FK
            
            # Step 2: Insert into channel-specific table
            if channel_type == ChannelType.EMAIL:
                specific_template = EmailTemplate(
                    id=specific_id,
                    template_id=template_id,
                    content=template_data['content'],
                    subject=template_data['subject']
                )
            else:  # ChannelType.SMS
                specific_template = SMSTemplate(
                    id=specific_id,
                    template_id=template_id,
                    content=template_data['content']
                )
            
            db.add(specific_template)
            await db.flush()
            
            logger.info(f"Inserted Template (CTI) with id={template_id}, channel={channel_type.value}")
            return base_template, specific_template
            
        except Exception as e:
            logger.error(f"Error inserting Template: {e}")
            raise
    
    async def get_by_id(
        self,
        db: AsyncSession,
        template_id: UUID,
        include_deleted: bool = False
    ) -> Optional[Tuple[Template, Union[EmailTemplate, SMSTemplate]]]:
        """
        Get template by ID (CTI: JOINs base + specific table).
        
        Args:
            db: Database session
            template_id: Template UUID
            include_deleted: Include soft-deleted templates
        
        Returns:
            Tuple of (Template, EmailTemplate/SMSTemplate) or None
        """
        try:
            # Get base template first
            stmt = select(Template).where(Template.id == template_id)
            if not include_deleted:
                stmt = stmt.where(Template.status != 'deleted')
            
            result = await db.execute(stmt)
            base_template = result.scalar_one_or_none()
            
            if not base_template:
                logger.debug(f"Template with id={template_id} not found")
                return None
            
            # Get channel-specific data based on channel_type
            if base_template.channel_type == ChannelType.EMAIL:
                stmt = select(EmailTemplate).where(EmailTemplate.template_id == template_id)
                result = await db.execute(stmt)
                specific_template = result.scalar_one_or_none()
            else:  # SMS
                stmt = select(SMSTemplate).where(SMSTemplate.template_id == template_id)
                result = await db.execute(stmt)
                specific_template = result.scalar_one_or_none()
            
            if not specific_template:
                logger.error(f"CTI integrity error: found base template but not specific for id={template_id}")
                return None
            
            logger.debug(f"Found Template (CTI) with id={template_id}")
            return base_template, specific_template
            
        except Exception as e:
            logger.error(f"Error getting Template by id={template_id}: {e}")
            raise
    
    async def get_by_name(
        self,
        db: AsyncSession,
        name: str,
        include_deleted: bool = False
    ) -> Optional[Tuple[Template, Union[EmailTemplate, SMSTemplate]]]:
        """
        Get template by name (CTI: JOINs base + specific table).
        
        Args:
            db: Database session
            name: Template name (unique)
            include_deleted: Include soft-deleted templates
        
        Returns:
            Tuple of (Template, EmailTemplate/SMSTemplate) or None
        """
        try:
            # Get base template by name
            stmt = select(Template).where(Template.name == name)
            if not include_deleted:
                stmt = stmt.where(Template.status != 'deleted')
            
            result = await db.execute(stmt)
            base_template = result.scalar_one_or_none()
            
            if not base_template:
                logger.debug(f"Template with name={name} not found")
                return None
            
            # Get specific data
            return await self.get_by_id(db, base_template.id, include_deleted)
            
        except Exception as e:
            logger.error(f"Error getting Template by name={name}: {e}")
            raise
    
    async def get_by_id_or_name(
        self,
        db: AsyncSession,
        template_id: UUID | None = None,
        template_name: str | None = None
    ) -> Optional[Tuple[Template, Union[EmailTemplate, SMSTemplate]]]:
        """
        Get template by ID or name (priority: ID > name).
        
        Args:
            db: Database session
            template_id: Template UUID (priority)
            template_name: Template name (fallback)
        
        Returns:
            Tuple of (Template, EmailTemplate/SMSTemplate) or None
        """
        if template_id:
            return await self.get_by_id(db, template_id)
        elif template_name:
            return await self.get_by_name(db, template_name)
        else:
            logger.warning("get_by_id_or_name called with neither id nor name")
            return None
    
    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Tuple[Template, Union[EmailTemplate, SMSTemplate]]]:
        """
        Get all templates with pagination (CTI: multiple queries).
        
        Args:
            db: Database session
            skip: Pagination offset
            limit: Max results
            include_deleted: Include soft-deleted templates
        
        Returns:
            List of tuples (Template, EmailTemplate/SMSTemplate)
        """
        try:
            # Get base templates
            stmt = select(Template)
            if not include_deleted:
                stmt = stmt.where(Template.status != 'deleted')
            stmt = stmt.offset(skip).limit(limit)
            
            result = await db.execute(stmt)
            base_templates = result.scalars().all()
            
            # Get specific data for each
            results = []
            for base_template in base_templates:
                specific_result = await self.get_by_id(db, base_template.id, include_deleted)
                if specific_result:
                    results.append(specific_result)
            
            logger.debug(f"Found {len(results)} Templates (CTI)")
            return results
            
        except Exception as e:
            logger.error(f"Error getting all Templates: {e}")
            raise
    
    async def update(
        self,
        db: AsyncSession,
        template_id: UUID,
        template_data: dict,
        channel_type: ChannelType
    ) -> Optional[Tuple[Template, Union[EmailTemplate, SMSTemplate]]]:
        """
        Update template (CTI: updates BOTH tables).
        
        Args:
            db: Database session
            template_id: Template UUID
            template_data: Dict with fields to update
            channel_type: Channel type (for specific table)
        
        Returns:
            Tuple of (Template, EmailTemplate/SMSTemplate) or None
        """
        try:
            # Check if exists
            existing = await self.get_by_id(db, template_id)
            if not existing:
                return None
            
            timestamp = get_utc_timestamp()
            
            # Update base template if name changed
            if 'name' in template_data:
                stmt = (
                    sql_update(Template)
                    .where(Template.id == template_id)
                    .values(name=template_data['name'], update_date=timestamp)
                )
                await db.execute(stmt)
            
            # Update specific template
            update_fields = {}
            if 'content' in template_data:
                update_fields['content'] = template_data['content']
            if channel_type == ChannelType.EMAIL and 'subject' in template_data:
                update_fields['subject'] = template_data['subject']
            
            if update_fields:
                if channel_type == ChannelType.EMAIL:
                    stmt = (
                        sql_update(EmailTemplate)
                        .where(EmailTemplate.template_id == template_id)
                        .values(**update_fields)
                    )
                else:
                    stmt = (
                        sql_update(SMSTemplate)
                        .where(SMSTemplate.template_id == template_id)
                        .values(**update_fields)
                    )
                await db.execute(stmt)
            
            await db.flush()
            
            # Fetch updated
            return await self.get_by_id(db, template_id)
            
        except Exception as e:
            logger.error(f"Error updating Template id={template_id}: {e}")
            raise
    
    async def delete(
        self,
        db: AsyncSession,
        template_id: UUID
    ) -> bool:
        """
        Soft delete template (CASCADE handles specific table automatically).
        
        Args:
            db: Database session
            template_id: Template UUID
        
        Returns:
            True if deleted, False if not found
        """
        try:
            # Check if exists
            existing = await self.get_by_id(db, template_id)
            if not existing:
                return False
            
            # Soft delete base template (CASCADE handles specific table)
            timestamp = get_utc_timestamp()
            stmt = (
                sql_update(Template)
                .where(Template.id == template_id)
                .values(status='deleted', update_date=timestamp)
            )
            await db.execute(stmt)
            await db.flush()
            
            logger.info(f"Soft deleted Template id={template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting Template id={template_id}: {e}")
            raise
