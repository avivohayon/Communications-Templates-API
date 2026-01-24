"""
Twilio SMS Channel Implementation.

Sends SMS messages via Twilio API.
API Documentation: https://www.twilio.com/docs/sms/api/message-resource
"""
import logging
import base64
import httpx
import asyncio

from src.config import settings
from src.services.channels.base_channel import MessageChannel, MessageSendResult, BatchMessageSendResult

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
    
    async def send_batch(
        self,
        recipients: list[str],
        content: str,
        subject: str | None = None
    ) -> BatchMessageSendResult:
        """
        Send SMS to multiple recipients concurrently.
        
        Twilio does not support native batch sending, so we send
        to multiple recipients concurrently using asyncio.gather.
        This is much faster than sequential sending.
        
        Args:
            recipients: List of recipient phone numbers (E.164 format)
            content: SMS text content
            subject: Ignored for SMS
        
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
        
        logger.info(f"Sending SMS batch to {len(recipients)} recipients concurrently")
        
        # Send to all recipients concurrently
        tasks = [
            self.send(recipient=r, content=content, subject=subject)
            for r in recipients
        ]
        
        # Gather results, don't stop on exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        successful = []
        failed = {}
        external_ids = {}
        
        for recipient, result in zip(recipients, results):
            if isinstance(result, Exception):
                # Exception during send
                error_msg = str(result)
                failed[recipient] = error_msg
                logger.error(f"❌ Exception sending to {recipient}: {error_msg}")
            elif result.success:
                # Success
                successful.append(recipient)
                external_ids[recipient] = result.external_id
                logger.debug(f"✅ Sent to {recipient}, SID: {result.external_id}")
            else:
                # Failed with error
                failed[recipient] = result.error
                logger.error(f"❌ Failed to send to {recipient}: {result.error}")
        
        logger.info(f"Batch send complete: {len(successful)} succeeded, {len(failed)} failed")
        
        return BatchMessageSendResult(
            successful_recipients=successful,
            failed_recipients=failed,
            external_ids=external_ids
        )