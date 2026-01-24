"""
SendGrid Email Channel Implementation.

Sends emails via SendGrid API (v3).
API Documentation: https://docs.sendgrid.com/api-reference/mail-send/mail-send
"""
import logging
import httpx

from src.config import settings
from src.services.channels.base_channel import MessageChannel, MessageSendResult

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
