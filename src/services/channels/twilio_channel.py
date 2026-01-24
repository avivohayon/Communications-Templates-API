"""
Twilio SMS Channel Implementation.

Sends SMS messages via Twilio API.
API Documentation: https://www.twilio.com/docs/sms/api/message-resource
"""
import logging
import base64
import httpx

from src.config import settings
from src.services.channels.base_channel import MessageChannel, MessageSendResult

logger = logging.getLogger(__name__)


class TwilioChannel(MessageChannel):
    """
    Twilio SMS channel implementation.
    
    Configuration:
    - Account SID: from settings.TWILIO_ACCOUNT_SID
    - Auth Token: from settings.TWILIO_AUTH_TOKEN
    - From Number: from settings.TWILIO_FROM_NUMBER
    
    API Endpoint: https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json
    """
    
    BASE_URL = "https://api.twilio.com/2010-04-01"
    
    async def send(
        self,
        recipient: str,
        content: str,
        subject: str | None = None
    ) -> MessageSendResult:
        """
        Send SMS via Twilio API.
        
        Args:
            recipient: Recipient phone number (E.164 format: +15005550006)
            content: SMS text content
            subject: Ignored for SMS (optional parameter)
        
        Returns:
            MessageSendResult with success status and Twilio message SID
        """
        # Build Twilio API URL
        url = f"{self.BASE_URL}/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
        
        # Build request payload (form-encoded)
        data = {
            "To": recipient,
            "From": settings.TWILIO_FROM_NUMBER,
            "Body": content
        }
        
        # Twilio uses HTTP Basic Auth (AccountSID:AuthToken)
        auth_string = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data=data,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    # Twilio returns 201 Created with message details
                    response_data = response.json()
                    message_sid = response_data.get("sid", "unknown")
                    logger.info(f"✅ SMS sent to {recipient} (Twilio SID: {message_sid})")
                    return MessageSendResult(
                        success=True,
                        external_id=message_sid
                    )
                else:
                    error = f"Twilio API error: {response.status_code} - {response.text}"
                    logger.error(error)
                    return MessageSendResult(success=False, error=error)
                    
        except httpx.TimeoutException:
            error = "Twilio API timeout"
            logger.error(error)
            return MessageSendResult(success=False, error=error)
            
        except Exception as e:
            error = f"Twilio error: {str(e)}"
            logger.error(error, exc_info=True)
            return MessageSendResult(success=False, error=error)
