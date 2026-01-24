"""
SendGrid Email Channel Implementation.

Sends emails via SendGrid API (v3).
API Documentation: https://docs.sendgrid.com/api-reference/mail-send/mail-send
"""
import logging
import httpx

from src.config import settings
from src.services.channels.base_channel import MessageChannel, MessageSendResult, BatchMessageSendResult

logger = logging.getLogger(__name__)


class SendGridChannel(MessageChannel):
    """
    SendGrid email channel implementation.
    
    Configuration:
    - API Key: from settings.SENDGRID_API_KEY
    - From Email: from settings.SENDGRID_FROM_EMAIL
    - Sandbox Mode: Enabled (for testing without actual sends)
    
    API Endpoint: https://api.sendgrid.com/v3/mail/send
    """
    
    API_URL = "https://api.sendgrid.com/v3/mail/send"
    
    async def send(
        self,
        recipient: str,
        content: str,
        subject: str | None = None
    ) -> MessageSendResult:
        """
        Send email via SendGrid API.
        
        Args:
            recipient: Recipient email address
            content: Email content (HTML or plain text)
            subject: Email subject (required for email)
        
        Returns:
            MessageSendResult with success status and SendGrid message ID
        """
        if not subject:
            error = "Subject is required for email messages"
            logger.error(error)
            return MessageSendResult(success=False, error=error)
        
        # Build SendGrid API payload
        payload = {
            "personalizations": [
                {
                    "to": [{"email": recipient}],
                    "subject": subject
                }
            ],
            "from": {"email": settings.SENDGRID_FROM_EMAIL},
            "content": [
                {
                    "type": "text/html",
                    "value": content
                }
            ],
            # Sandbox mode: Email won't actually be sent
            # Remove this in production!
            "mail_settings": {
                "sandbox_mode": {
                    "enable": True
                }
            }
        }
        
        headers = {
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.API_URL,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code in [200, 202]:
                    # SendGrid returns 202 Accepted
                    message_id = response.headers.get("X-Message-Id", "unknown")
                    logger.info(f"✅ Email sent to {recipient} (SendGrid ID: {message_id})")
                    return MessageSendResult(
                        success=True,
                        external_id=message_id
                    )
                else:
                    error = f"SendGrid API error: {response.status_code} - {response.text}"
                    logger.error(error)
                    return MessageSendResult(success=False, error=error)
                    
        except httpx.TimeoutException:
            error = "SendGrid API timeout"
            logger.error(error)
            return MessageSendResult(success=False, error=error)
            
        except Exception as e:
            error = f"SendGrid error: {str(e)}"
            logger.error(error, exc_info=True)
            return MessageSendResult(success=False, error=error)
    
    async def send_batch(
        self,
        recipients: list[str],
        content: str,
        subject: str | None = None
    ) -> BatchMessageSendResult:
        """
        Send email to multiple recipients in a single API call.
        
        SendGrid supports batch sending via the personalizations array.
        This allows sending to up to 1000 recipients in one request.
        
        Args:
            recipients: List of recipient email addresses
            content: Email content (HTML or plain text)
            subject: Email subject (required for email)
        
        Returns:
            BatchMessageSendResult with per-recipient success/failure status
        """
        if not recipients:
            logger.warning("send_batch called with empty recipients list")
            return BatchMessageSendResult(
                successful_recipients=[],
                failed_recipients={},
                external_ids={}
            )
        
        if not subject:
            error = "Subject is required for email messages"
            logger.error(error)
            # All recipients fail
            return BatchMessageSendResult(
                successful_recipients=[],
                failed_recipients={r: error for r in recipients},
                external_ids={}
            )
        
        # Build personalizations for all recipients
        # Each recipient gets the same content but in separate "to" field
        personalizations = [
            {
                "to": [{"email": recipient}],
                "subject": subject
            }
            for recipient in recipients
        ]
        
        payload = {
            "personalizations": personalizations,
            "from": {"email": settings.SENDGRID_FROM_EMAIL},
            "content": [
                {
                    "type": "text/html",
                    "value": content
                }
            ],
            # Sandbox mode: Email won't actually be sent
            # Remove this in production!
            "mail_settings": {
                "sandbox_mode": {
                    "enable": True
                }
            }
        }
        
        headers = {
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=self.API_URL,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code in [200, 202]:
                    # SendGrid returns 202 Accepted for batch sends
                    # Note: SendGrid returns a single message ID for the batch
                    # We use it for all recipients
                    message_id = response.headers.get("X-Message-Id", "batch_unknown")
                    
                    logger.info(f"✅ Batch email sent to {len(recipients)} recipients (SendGrid ID: {message_id})")
                    
                    # All recipients succeeded
                    return BatchMessageSendResult(
                        successful_recipients=recipients.copy(),
                        failed_recipients={},
                        external_ids={r: message_id for r in recipients}
                    )
                else:
                    # Batch failed entirely
                    error = f"SendGrid API error: {response.status_code} - {response.text}"
                    logger.error(f"Batch send failed: {error}")
                    
                    return BatchMessageSendResult(
                        successful_recipients=[],
                        failed_recipients={r: error for r in recipients},
                        external_ids={}
                    )
                    
        except httpx.TimeoutException:
            error = "SendGrid API timeout"
            logger.error(f"Batch send timeout for {len(recipients)} recipients")
            return BatchMessageSendResult(
                successful_recipients=[],
                failed_recipients={r: error for r in recipients},
                external_ids={}
            )
            
        except Exception as e:
            error = f"SendGrid error: {str(e)}"
            logger.error(f"Batch send error: {error}", exc_info=True)
            return BatchMessageSendResult(
                successful_recipients=[],
                failed_recipients={r: error for r in recipients},
                external_ids={}
            )