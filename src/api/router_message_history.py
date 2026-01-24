"""
Message History API Router.

Provides endpoints for querying message history (read-only).
"""
import logging
from typing import List, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.logic.logic_message_history import MessageHistoryLogic
from src.schemas.schema_message_history import (
    EmailMessageHistoryOut,
    SMSMessageHistoryOut,
    MessageHistoryFilter
)
from src.models.enums import ChannelType, MessageStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["Message History"])


@router.get(
    "/{history_id}",
    response_model=Union[EmailMessageHistoryOut, SMSMessageHistoryOut],
    summary="Get message history by ID"
)
async def get_message_history_by_id(
    history_id: UUID,
    db: AsyncSession = Depends(get_db),
    history_logic: MessageHistoryLogic = Depends(MessageHistoryLogic)
):
    """
    Retrieve a single message history record by its UUID.
    
    Returns polymorphic response:
    - EmailMessageHistoryOut for email messages
    - SMSMessageHistoryOut for SMS messages
    """
    logger.info(f"Received request to get message history by ID: {history_id}")
    
    try:
        history = await history_logic.get_by_id(db, history_id)
        
        if not history:
            logger.warning(f"Message history with ID {history_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message history with ID {history_id} not found"
            )
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving message history {history_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "",
    response_model=List[Union[EmailMessageHistoryOut, SMSMessageHistoryOut]],
    summary="Query message history with filters"
)
async def query_message_history(
    template_id: UUID | None = Query(None, description="Filter by template UUID"),
    template_name: str | None = Query(None, description="Filter by template name (case-insensitive)"),
    recipient: str | None = Query(None, description="Filter by recipient (case-insensitive)"),
    channel_type: ChannelType | None = Query(None, description="Filter by channel type (email or sms)"),
    status: MessageStatus | None = Query(None, description="Filter by message status"),
    skip: int = Query(0, ge=0, description="Number of records to skip (pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    history_logic: MessageHistoryLogic = Depends(MessageHistoryLogic)
):
    """
    Query message history with optional filters.
    
    All filters are optional. If no filters are provided, returns all message history records
    (with pagination).
    
    Returns a list of polymorphic responses:
    - EmailMessageHistoryOut for email messages
    - SMSMessageHistoryOut for SMS messages
    
    Results are ordered by creation_date descending (newest first).
    """
    logger.info(f"Received request to query message history with filters: "
                f"template_id={template_id}, template_name={template_name}, "
                f"recipient={recipient}, channel_type={channel_type}, "
                f"status={status}, skip={skip}, limit={limit}")
    
    try:
        # Build filter object
        filters = MessageHistoryFilter(
            template_id=template_id,
            template_name=template_name,
            recipient=recipient,
            channel_type=channel_type,
            status=status,
            skip=skip,
            limit=limit
        )
        
        # Query with filters
        results = await history_logic.get_by_filters(db, filters)
        
        logger.info(f"Returning {len(results)} message history records")
        return results
        
    except Exception as e:
        logger.error(f"Error querying message history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
