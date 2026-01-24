"""
Message History Logic Layer with CTI and polymorphic schema conversion.

This logic layer INHERITS from BaseLogic but overrides for CTI handling.
Read-only operations (no creation/update via API).
"""
import logging
from typing import Optional, List, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.das.da_message_history import MessageHistoryDA
from src.logic.base_logic import BaseLogic
from src.models.models import MessageHistory, EmailMessageHistory, SMSMessageHistory
from src.models.enums import ChannelType, MessageStatus
from src.schemas.schema_message_history import (
    EmailMessageHistoryOut,
    SMSMessageHistoryOut,
    MessageHistoryFilter
)

logger = logging.getLogger(__name__)


class MessageHistoryLogic(BaseLogic[
    None,  # No create schema (read-only)
    Union[EmailMessageHistoryOut, SMSMessageHistoryOut],
    None   # No update schema (read-only)
]):
    """
    Business Logic for MessageHistory entities with CTI support.
    
    INHERITS from BaseLogic but overrides for CTI handling.
    READ-ONLY: No create/update/delete via API.
    
    Responsibilities:
    - Convert CTI model tuples → polymorphic Pydantic schemas
    - Handle filtering and queries
    - Determine correct schema type based on channel_type
    
    Inheritance:
    - OVERRIDES: get_by_id() (returns polymorphic schema)
    - NEW METHOD: get_by_filters()
    - NOT IMPLEMENTED: create, update, delete (read-only)
    """
    
    def __init__(self):
        """Initialize MessageHistoryLogic with MessageHistoryDA."""
        # Cannot call super().__init__() because we need MessageHistoryDA (CTI-aware)
        self.da: MessageHistoryDA = MessageHistoryDA()
        self.entity_name = "MessageHistory"
        logger.debug("Initialized MessageHistoryLogic with CTI support (read-only)")
    
    def _model_to_schema(
        self,
        base: MessageHistory,
        specific: Union[EmailMessageHistory, SMSMessageHistory]
    ) -> Union[EmailMessageHistoryOut, SMSMessageHistoryOut]:
        """
        Convert CTI models to appropriate polymorphic Pydantic schema.
        
        Args:
            base: MessageHistory model (base table)
            specific: EmailMessageHistory or SMSMessageHistory model
        
        Returns:
            EmailMessageHistoryOut or SMSMessageHistoryOut based on channel_type
        """
        try:
            channel_type = ChannelType(base.channel_type)
            
            # Common fields from base model
            base_data = {
                'id': base.id,
                'template_id': base.template_id,
                'template_name': base.template_name,
                'recipient': base.recipient,
                'channel_type': channel_type,
                'status': MessageStatus(base.status),
                'error_message': base.error_message,
                'creation_date': base.creation_date,
                'update_date': base.update_date,
                'status': base.status  # Override - status field from BaseModel
            }
            
            # Add channel-specific fields and create appropriate schema
            if channel_type == ChannelType.EMAIL:
                email_data = {
                    **base_data,
                    'rendered_content': specific.rendered_content,
                    'rendered_subject': specific.rendered_subject,
                    'external_message_id': specific.external_message_id
                }
                return EmailMessageHistoryOut(**email_data)
            else:  # SMS
                sms_data = {
                    **base_data,
                    'rendered_content': specific.rendered_content,
                    'external_message_id': specific.external_message_id
                }
                return SMSMessageHistoryOut(**sms_data)
                
        except Exception as e:
            logger.error(f"Error converting MessageHistory models to schema: {e}")
            raise
    
    async def get_by_id(
        self,
        db: AsyncSession,
        id: UUID
    ) -> Optional[Union[EmailMessageHistoryOut, SMSMessageHistoryOut]]:
        """
        Get message history by ID.
        
        Args:
            db: Database session
            id: MessageHistory UUID
        
        Returns:
            EmailMessageHistoryOut or SMSMessageHistoryOut, or None if not found
        """
        try:
            result = await self.da.get_by_id(db, id)
            
            if not result:
                logger.debug(f"MessageHistory with id={id} not found")
                return None
            
            base, specific = result
            schema = self._model_to_schema(base, specific)
            
            logger.debug(f"Retrieved MessageHistory id={id}, channel={schema.channel_type.value}")
            return schema
            
        except Exception as e:
            logger.error(f"Error getting MessageHistory by id={id}: {e}")
            raise
    
    async def get_by_filters(
        self,
        db: AsyncSession,
        filters: MessageHistoryFilter
    ) -> List[Union[EmailMessageHistoryOut, SMSMessageHistoryOut]]:
        """
        Query message history with filters.
        
        Args:
            db: Database session
            filters: MessageHistoryFilter with optional query parameters
        
        Returns:
            List of EmailMessageHistoryOut or SMSMessageHistoryOut
        """
        try:
            # Call DA with filter parameters
            results = await self.da.get_by_filters(
                db=db,
                template_id=filters.template_id,
                template_name=filters.template_name,
                recipient=filters.recipient,
                channel_type=filters.channel_type,
                status=filters.status,
                skip=filters.skip,
                limit=filters.limit
            )
            
            # Convert all model tuples to schemas
            schemas = []
            for base, specific in results:
                schema = self._model_to_schema(base, specific)
                schemas.append(schema)
            
            logger.debug(f"Retrieved {len(schemas)} MessageHistory records with filters")
            return schemas
            
        except Exception as e:
            logger.error(f"Error querying MessageHistory with filters: {e}")
            raise
