"""
Message Sending Logic Layer - Core Orchestration.

This is the HEART of the message sending system.
Orchestrates template fetching, rendering, channel selection, sending, and history recording.
"""
import logging
from typing import Dict, Any

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
    Business Logic for Message Sending with full orchestration.
    
    Orchestration Flow:
    1. Fetch template (by ID or name)
    2. For each recipient:
        a. Render template content and subject
        b. Get appropriate channel (SendGrid/Twilio)
        c. Send message via channel
        d. Record result in message history
    3. Build and return response with per-recipient results
    """
    
    def __init__(self):
        """Initialize MessageLogic with dependencies."""
        self.template_logic = TemplateLogic()
        self.history_da = MessageHistoryDA()
        self.channel_factory = ChannelFactory()
        logger.debug("Initialized MessageLogic")
    
    async def send_messages(
        self,
        db: AsyncSession,
        request: SendMessageRequest
    ) -> SendMessageResponse:
        """
        Send messages to recipients using a template.
        
        This method orchestrates the entire message sending flow:
        - Template fetching and validation
        - Template rendering with data
        - Channel selection and message sending
        - History recording for each attempt
        
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
                template = await self.template_logic.get_by_id(db, request.template_id)
            elif request.template_name:
                template = await self.template_logic.get_by_name(db, request.template_name)
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
            
            # Step 2: Process each recipient
            results = []
            successful_count = 0
            failed_count = 0
            
            for recipient in request.to:
                logger.info(f"Processing recipient: {recipient}")
                
                try:
                    # Step 2a: Render template with data
                    rendered_content = template_renderer.render(content, request.data)
                    rendered_subject = None
                    
                    if channel_type == ChannelType.EMAIL:
                        if not subject:
                            raise ValueError("Email template missing subject")
                        rendered_subject = template_renderer.render(subject, request.data)
                    
                    logger.debug(f"Template rendered for {recipient}")
                    
                    # Step 2b: Get appropriate channel
                    channel = self.channel_factory.get_channel(channel_type)
                    
                    # Step 2c: Send message via channel
                    send_result = await channel.send(
                        recipient=recipient,
                        content=rendered_content,
                        subject=rendered_subject
                    )
                    
                    # Step 2d: Record result in message history
                    if send_result.success:
                        # Success
                        logger.info(f"✅ Message sent successfully to {recipient}, external_id={send_result.external_id}")
                        
                        await self._record_history(
                            db=db,
                            template_id=template_id,
                            template_name=template_name,
                            recipient=recipient,
                            channel_type=channel_type,
                            status=MessageStatus.SUCCESS,
                            rendered_content=rendered_content,
                            rendered_subject=rendered_subject,
                            external_message_id=send_result.external_id,
                            error_message=None
                        )
                        
                        results.append(MessageRecipientResult(
                            recipient=recipient,
                            status="success",
                            error_message=None,
                            external_message_id=send_result.external_id
                        ))
                        successful_count += 1
                    else:
                        # Failure from channel
                        logger.error(f"❌ Message send failed for {recipient}: {send_result.error}")
                        
                        await self._record_history(
                            db=db,
                            template_id=template_id,
                            template_name=template_name,
                            recipient=recipient,
                            channel_type=channel_type,
                            status=MessageStatus.FAILED,
                            rendered_content=rendered_content,
                            rendered_subject=rendered_subject,
                            external_message_id=None,
                            error_message=send_result.error
                        )
                        
                        results.append(MessageRecipientResult(
                            recipient=recipient,
                            status="failed",
                            error_message=send_result.error,
                            external_message_id=None
                        ))
                        failed_count += 1
                
                except Exception as e:
                    # Exception during rendering or sending
                    error_msg = str(e)
                    logger.error(f"❌ Exception while processing {recipient}: {error_msg}", exc_info=True)
                    
                    try:
                        # Try to record failure in history
                        await self._record_history(
                            db=db,
                            template_id=template_id,
                            template_name=template_name,
                            recipient=recipient,
                            channel_type=channel_type,
                            status=MessageStatus.FAILED,
                            rendered_content="",  # Empty if rendering failed
                            rendered_subject=None,
                            external_message_id=None,
                            error_message=error_msg
                        )
                    except Exception as history_error:
                        logger.error(f"Failed to record history for {recipient}: {history_error}")
                    
                    results.append(MessageRecipientResult(
                        recipient=recipient,
                        status="failed",
                        error_message=error_msg,
                        external_message_id=None
                    ))
                    failed_count += 1
            
            # Step 3: Commit all history records
            await db.commit()
            
            # Step 4: Build response
            response = SendMessageResponse(
                template_id=template_id,
                template_name=template_name,
                channel_type=channel_type,
                results=results,
                total_recipients=len(request.to),
                successful_count=successful_count,
                failed_count=failed_count
            )
            
            logger.info(f"Message sending complete: {successful_count} succeeded, {failed_count} failed")
            return response
            
        except ValueError as e:
            logger.error(f"Validation error during message sending: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during message sending: {e}", exc_info=True)
            raise
    
    async def _record_history(
        self,
        db: AsyncSession,
        template_id: Any,
        template_name: str,
        recipient: str,
        channel_type: ChannelType,
        status: MessageStatus,
        rendered_content: str,
        rendered_subject: str | None,
        external_message_id: str | None,
        error_message: str | None
    ):
        """
        Record a message send attempt in history.
        
        Args:
            db: Database session
            template_id: Template UUID
            template_name: Template name
            recipient: Recipient address
            channel_type: Email or SMS
            status: Success or Failed
            rendered_content: Rendered message content
            rendered_subject: Rendered subject (email only)
            external_message_id: SendGrid/Twilio ID
            error_message: Error message if failed
        """
        try:
            # Prepare base fields
            base_fields = {
                'template_id': template_id,
                'template_name': template_name,
                'recipient': recipient,
                'status': status,
                'error_message': error_message
            }
            
            # Prepare channel-specific fields
            if channel_type == ChannelType.EMAIL:
                channel_fields = {
                    'rendered_content': rendered_content,
                    'rendered_subject': rendered_subject or "",
                    'external_message_id': external_message_id
                }
            else:  # SMS
                channel_fields = {
                    'rendered_content': rendered_content,
                    'external_message_id': external_message_id
                }
            
            # Insert into history (CTI)
            await self.history_da.insert_with_channel_data(
                db=db,
                base_fields=base_fields,
                channel_fields=channel_fields,
                channel_type=channel_type
            )
            
            logger.debug(f"Recorded message history for {recipient}, status={status.value}")
            
        except Exception as e:
            logger.error(f"Error recording message history: {e}")
            raise
