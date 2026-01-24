"""
Message Sending Logic Layer - Core Orchestration with Batch Support.

This is the HEART of the message sending system.
Orchestrates template fetching, rendering ONCE, batch channel sending, and bulk history recording.
"""
import logging
from typing import Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.logic.logic_template import TemplateLogic
from src.das.da_message_history import MessageHistoryDA
from src.services.template_renderer import template_renderer
from src.services.channels.channel_factory import ChannelFactory
from src.models.enums import ChannelType, MessageStatus
from src.schemas.schema_message import (
    SendMessageRequest,
    SendMessageResponse,
    MessageRecipientResult
)
from src.schemas.schema_template import EmailTemplateOut, SMSTemplateOut

logger = logging.getLogger(__name__)


class MessageLogic:
    """
    Business Logic for Message Sending with BATCH OPTIMIZATION.
    
    Optimized Flow:
    1. Fetch template (by ID or name)
    2. Render template ONCE (not per recipient!)
    3. Send batch via channel (SendGrid native batch, Twilio concurrent)
    4. Bulk insert history records
    5. Return aggregated response
    
    Performance: 10-30x faster than one-by-one sending for identical content.
    """
    
    def __init__(self) -> None:
        """Initialize MessageLogic with dependencies."""
        self.template_logic: TemplateLogic = TemplateLogic()
        self.history_da: MessageHistoryDA = MessageHistoryDA()
        self.channel_factory: ChannelFactory = ChannelFactory()
        logger.debug("Initialized MessageLogic with batch support")
    
    async def send_messages(
        self,
        db: AsyncSession,
        request: SendMessageRequest
    ) -> SendMessageResponse:
        """
        Send messages to recipients using a template (BATCH OPTIMIZED).
        
        This method orchestrates the entire message sending flow:
        - Template fetching and validation
        - Template rendering ONCE with data
        - Batch channel selection and message sending
        - Bulk history recording for all attempts
        
        Args:
            db: Database session
            request: SendMessageRequest with template, data, and recipients
        
        Returns:
            SendMessageResponse with per-recipient results
        
        Raises:
            ValueError: Template not found or rendering errors
            Exception: Unexpected errors during sending
        """
        try:
            # Step 1: Fetch template by ID or name
            logger.info(f"Fetching template (id={request.template_id}, name={request.template_name})")
            
            if request.template_id:
                template = await self.template_logic.get_by_id(db=db, template_id=request.template_id)
            elif request.template_name:
                template = await self.template_logic.get_by_name(db=db, name=request.template_name)
            else:
                raise ValueError("Either template_id or template_name must be provided")
            
            if not template:
                raise ValueError("Template not found")
            
            if template.status == 'deleted':
                raise ValueError("Cannot send messages using a deleted template")
            
            logger.info(f"Found template: id={template.id}, name={template.name}, channel={template.channel_type.value}")
            
            # Extract template data
            template_id = template.id
            template_name = template.name
            channel_type = template.channel_type
            content = template.content
            subject = template.subject if isinstance(template, EmailTemplateOut) else None
            
            # Step 2: Render template ONCE (OPTIMIZATION: not per recipient!)
            logger.info("Rendering template ONCE for all recipients")
            try:
                rendered_content = template_renderer.render(content=content, data=request.data)
                rendered_subject = None
                
                if channel_type == ChannelType.EMAIL:
                    if not subject:
                        raise ValueError("Email template missing subject")
                    rendered_subject = template_renderer.render(content=subject, data=request.data)
                
                logger.debug(f"Template rendered successfully (content length: {len(rendered_content)})")
            except Exception as e:
                logger.error(f"Template rendering failed: {e}")
                raise ValueError(f"Template rendering error: {str(e)}")
            
            # Step 3: Get appropriate channel
            channel = self.channel_factory.get_channel(channel_type=channel_type)
            
            # Step 4: Send batch via channel (OPTIMIZATION: batch API call)
            logger.info(f"Sending batch to {len(request.to)} recipients via {channel_type.value}")
            batch_result = await channel.send_batch(
                recipients=request.to,
                content=rendered_content,
                subject=rendered_subject
            )
            
            logger.info(f"Batch send complete: {len(batch_result.successful_recipients)} succeeded, "
                       f"{len(batch_result.failed_recipients)} failed")
            
            # Step 5: Build history records for bulk insert (OPTIMIZATION: bulk DB insert)
            history_records = []
            
            # Successful recipients
            for recipient in batch_result.successful_recipients:
                external_id = batch_result.external_ids.get(recipient)
                record = {
                    'base_fields': {
                        'template_id': template_id,
                        'template_name': template_name,
                        'recipient': recipient,
                        'status': MessageStatus.SUCCESS,
                        'error_message': None
                    },
                    'channel_fields': {
                        'rendered_content': rendered_content,
                        'rendered_subject': rendered_subject if channel_type == ChannelType.EMAIL else None,
                        'external_message_id': external_id
                    }
                }
                history_records.append(record)
            
            # Failed recipients
            for recipient, error in batch_result.failed_recipients.items():
                record = {
                    'base_fields': {
                        'template_id': template_id,
                        'template_name': template_name,
                        'recipient': recipient,
                        'status': MessageStatus.FAILED,
                        'error_message': error
                    },
                    'channel_fields': {
                        'rendered_content': rendered_content,
                        'rendered_subject': rendered_subject if channel_type == ChannelType.EMAIL else None,
                        'external_message_id': None
                    }
                }
                history_records.append(record)
            
            # Bulk insert all history records
            await self.history_da.bulk_insert_with_channel_data(
                db=db,
                records=history_records,
                channel_type=channel_type
            )
            
            # Step 6: Commit all history records
            await db.commit()
            
            # Step 7: Build response with per-recipient results
            results = []
            
            for recipient in batch_result.successful_recipients:
                results.append(MessageRecipientResult(
                    recipient=recipient,
                    status="success",
                    error_message=None,
                    external_message_id=batch_result.external_ids.get(recipient)
                ))
            
            for recipient, error in batch_result.failed_recipients.items():
                results.append(MessageRecipientResult(
                    recipient=recipient,
                    status="failed",
                    error_message=error,
                    external_message_id=None
                ))
            
            response = SendMessageResponse(
                template_id=template_id,
                template_name=template_name,
                channel_type=channel_type,
                results=results,
                total_recipients=len(request.to),
                successful_count=len(batch_result.successful_recipients),
                failed_count=len(batch_result.failed_recipients)
            )
            
            logger.info(f"Message sending complete: {response.successful_count} succeeded, {response.failed_count} failed")
            return response
            
        except ValueError as e:
            logger.error(f"Validation error during message sending: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during message sending: {e}", exc_info=True)
            raise
