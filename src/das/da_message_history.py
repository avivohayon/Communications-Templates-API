"""
Message History Data Access Layer with Class Table Inheritance (CTI) support.

This DA INHERITS from BaseDA but overrides/extends for CTI:
- MessageHistory is split across multiple tables (message_history + email/sms_message_history)
- Need to handle JOIN operations
- Need to insert into TWO tables in a transaction
- Need to return BOTH base and specific models
"""
import logging
from typing import Optional, Tuple, List, Union
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.models import MessageHistory, EmailMessageHistory, SMSMessageHistory
from src.models.enums import ChannelType, MessageStatus
from src.das.base_da import BaseDA, get_utc_timestamp

logger = logging.getLogger(__name__)


class MessageHistoryDA(BaseDA):
    """
    Data Access Layer for MessageHistory entities with CTI support.
    
    INHERITS from BaseDA and adds CTI-specific methods.
    
    CTI Design:
    - Base message metadata in 'message_history' table
    - Channel-specific data in 'email_message_history' or 'sms_message_history' tables
    - All operations require handling both tables
    
    Inheritance:
    - OVERRIDES: get_by_id()
    - NEW METHOD: insert_with_channel_data() (doesn't override base insert)
    - NEW METHOD: get_by_filters()
    - CAN USE BASE: insert, get_all, update, delete (if needed in future)
    """
    
    def __init__(self):
        """Initialize MessageHistoryDA with MessageHistory model and CTI-specific models."""
        super().__init__(MessageHistory)  # Call parent with base model
        self.email_history_model = EmailMessageHistory
        self.sms_history_model = SMSMessageHistory
        logger.debug("Initialized MessageHistoryDA with CTI support")
    
    async def insert_with_channel_data(
        self,
        db: AsyncSession,
        base_fields: dict,
        channel_fields: dict,
        channel_type: ChannelType
    ) -> Tuple[MessageHistory, Union[EmailMessageHistory, SMSMessageHistory]]:
        """
        Insert a new message history record (CTI: inserts into TWO tables).
        
        Transaction Flow:
        1. Insert into 'message_history' table (base metadata)
        2. Insert into 'email_message_history' or 'sms_message_history' (channel-specific data)
        3. Return both models
        
        Args:
            db: Database session
            base_fields: Dict with template_id, template_name, recipient, status, error_message
            channel_fields: Dict with rendered_content, rendered_subject (email), external_message_id
            channel_type: Email or SMS
        
        Returns:
            Tuple of (MessageHistory, EmailMessageHistory/SMSMessageHistory)
        """
        try:
            # Generate IDs
            history_id = uuid4()
            specific_id = uuid4()
            timestamp = get_utc_timestamp()
            
            # Step 1: Insert into base 'message_history' table
            base_history = MessageHistory(
                id=history_id,
                template_id=base_fields['template_id'],
                template_name=base_fields['template_name'],
                recipient=base_fields['recipient'],
                channel_type=channel_type.value,  # Store enum value as string
                status=base_fields['status'].value if isinstance(base_fields['status'], MessageStatus) else base_fields['status'],
                error_message=base_fields.get('error_message'),
                creation_date=timestamp,
                update_date=timestamp
            )
            db.add(base_history)
            await db.flush()  # Flush to get the ID for FK
            
            # Step 2: Insert into channel-specific table
            if channel_type == ChannelType.EMAIL:
                specific_history = EmailMessageHistory(
                    id=specific_id,
                    message_history_id=history_id,
                    rendered_content=channel_fields['rendered_content'],
                    rendered_subject=channel_fields['rendered_subject'],
                    external_message_id=channel_fields.get('external_message_id')
                )
            else:  # ChannelType.SMS
                specific_history = SMSMessageHistory(
                    id=specific_id,
                    message_history_id=history_id,
                    rendered_content=channel_fields['rendered_content'],
                    external_message_id=channel_fields.get('external_message_id')
                )
            
            db.add(specific_history)
            await db.flush()
            
            logger.info(f"Inserted MessageHistory (CTI) with id={history_id}, channel={channel_type.value}, status={base_fields['status']}")
            return base_history, specific_history
            
        except Exception as e:
            logger.error(f"Error inserting MessageHistory: {e}")
            raise
    
    async def get_by_id(
        self,
        db: AsyncSession,
        id: UUID
    ) -> Optional[Tuple[MessageHistory, Union[EmailMessageHistory, SMSMessageHistory]]]:
        """
        Get message history by ID with CTI data.
        
        Uses selectinload to eagerly load the channel-specific data.
        
        Args:
            db: Database session
            id: MessageHistory UUID
        
        Returns:
            Tuple of (MessageHistory, EmailMessageHistory/SMSMessageHistory) or None
        """
        try:
            # Query with eager loading of relationships
            stmt = (
                select(MessageHistory)
                .where(MessageHistory.id == id)
                .options(
                    selectinload(MessageHistory.email_detail),
                    selectinload(MessageHistory.sms_detail)
                )
            )
            
            result = await db.execute(stmt)
            base_history = result.scalar_one_or_none()
            
            if not base_history:
                logger.debug(f"MessageHistory with id={id} not found")
                return None
            
            # Determine which specific table has the data
            channel_type = ChannelType(base_history.channel_type)
            if channel_type == ChannelType.EMAIL:
                specific_history = base_history.email_detail
            else:
                specific_history = base_history.sms_detail
            
            if not specific_history:
                logger.error(f"MessageHistory id={id} missing channel-specific data!")
                return None
            
            logger.debug(f"Found MessageHistory with id={id}, channel={channel_type.value}")
            return base_history, specific_history
            
        except Exception as e:
            logger.error(f"Error getting MessageHistory by id={id}: {e}")
            raise
    
    async def get_by_filters(
        self,
        db: AsyncSession,
        template_id: Optional[UUID] = None,
        template_name: Optional[str] = None,
        recipient: Optional[str] = None,
        channel_type: Optional[ChannelType] = None,
        status: Optional[MessageStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Tuple[MessageHistory, Union[EmailMessageHistory, SMSMessageHistory]]]:
        """
        Query message history with optional filters.
        
        Args:
            db: Database session
            template_id: Filter by template UUID
            template_name: Filter by template name (case-insensitive)
            recipient: Filter by recipient (case-insensitive)
            channel_type: Filter by channel type
            status: Filter by message status
            skip: Pagination offset
            limit: Max results
        
        Returns:
            List of tuples (MessageHistory, EmailMessageHistory/SMSMessageHistory)
        """
        try:
            # Build query with filters
            stmt = select(MessageHistory).options(
                selectinload(MessageHistory.email_detail),
                selectinload(MessageHistory.sms_detail)
            )
            
            # Apply filters
            conditions = []
            
            if template_id:
                conditions.append(MessageHistory.template_id == template_id)
            
            if template_name:
                conditions.append(MessageHistory.template_name.ilike(f"%{template_name}%"))
            
            if recipient:
                conditions.append(MessageHistory.recipient.ilike(f"%{recipient}%"))
            
            if channel_type:
                conditions.append(MessageHistory.channel_type == channel_type.value)
            
            if status:
                conditions.append(MessageHistory.status == status.value)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # Order by creation_date descending (newest first)
            stmt = stmt.order_by(MessageHistory.creation_date.desc())
            
            # Apply pagination
            stmt = stmt.offset(skip).limit(limit)
            
            # Execute query
            result = await db.execute(stmt)
            base_histories = result.scalars().all()
            
            # Build result tuples
            results = []
            for base_history in base_histories:
                channel_type_val = ChannelType(base_history.channel_type)
                if channel_type_val == ChannelType.EMAIL:
                    specific_history = base_history.email_detail
                else:
                    specific_history = base_history.sms_detail
                
                if specific_history:
                    results.append((base_history, specific_history))
                else:
                    logger.warning(f"MessageHistory id={base_history.id} missing channel-specific data!")
            
            logger.debug(f"Found {len(results)} MessageHistory records with filters")
            return results
            
        except Exception as e:
            logger.error(f"Error querying MessageHistory with filters: {e}")
            raise
