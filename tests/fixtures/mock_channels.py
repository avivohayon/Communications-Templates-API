"""
Mock channel implementations for testing.

These mocks replace real SendGrid/Twilio API calls for fast, reliable unit testing.
"""
from src.services.channels.base_channel import MessageChannel, MessageSendResult, BatchMessageSendResult


class MockEmailChannel(MessageChannel):
    """
    Mock SendGrid channel for testing.
    
    Tracks all sent messages and can simulate success/failure scenarios.
    """
    
    def __init__(self, should_fail=False):
        """
        Initialize mock email channel.
        
        Args:
            should_fail: If True, all sends will fail with mock error
        """
        self.should_fail = should_fail
        self.sent_messages = []  # Track all sent messages for assertions
    
    async def send(self, recipient: str, content: str, subject: str | None = None) -> MessageSendResult:
        """
        Mock send operation - tracks message but doesn't actually send.
        
        Args:
            recipient: Email address
            content: Email body
            subject: Email subject
        
        Returns:
            MessageSendResult with success/failure based on should_fail flag
        """
        self.sent_messages.append({
            "recipient": recipient,
            "content": content,
            "subject": subject
        })
        
        if self.should_fail:
            return MessageSendResult(
                success=False,
                error="Mock API error"
            )
        
        return MessageSendResult(
            success=True,
            external_id=f"mock-email-{len(self.sent_messages)}"
        )
    
    async def send_batch(
        self,
        recipients: list[str],
        content: str,
        subject: str | None = None
    ) -> BatchMessageSendResult:
        """
        Mock batch send operation.
        
        Args:
            recipients: List of email addresses
            content: Email body
            subject: Email subject
        
        Returns:
            BatchMessageSendResult with success/failure per recipient
        """
        successful_recipients = []
        failed_recipients = {}
        external_ids = {}
        
        for recipient in recipients:
            result = await self.send(recipient, content, subject)
            if result.success:
                successful_recipients.append(recipient)
                external_ids[recipient] = result.external_id
            else:
                failed_recipients[recipient] = result.error
        
        return BatchMessageSendResult(
            successful_recipients=successful_recipients,
            failed_recipients=failed_recipients,
            external_ids=external_ids
        )


class MockSMSChannel(MessageChannel):
    """
    Mock Twilio channel for testing.
    
    Tracks all sent messages and can simulate success/failure scenarios.
    """
    
    def __init__(self, should_fail=False):
        """
        Initialize mock SMS channel.
        
        Args:
            should_fail: If True, all sends will fail with mock error
        """
        self.should_fail = should_fail
        self.sent_messages = []  # Track all sent messages for assertions
    
    async def send(self, recipient: str, content: str, subject: str | None = None) -> MessageSendResult:
        """
        Mock send operation - tracks message but doesn't actually send.
        
        Args:
            recipient: Phone number
            content: SMS body
            subject: Ignored for SMS
        
        Returns:
            MessageSendResult with success/failure based on should_fail flag
        """
        self.sent_messages.append({
            "recipient": recipient,
            "content": content
        })
        
        if self.should_fail:
            return MessageSendResult(
                success=False,
                error="Mock SMS error"
            )
        
        return MessageSendResult(
            success=True,
            external_id=f"mock-sms-{len(self.sent_messages)}"
        )
    
    async def send_batch(
        self,
        recipients: list[str],
        content: str,
        subject: str | None = None
    ) -> BatchMessageSendResult:
        """
        Mock batch send operation.
        
        Args:
            recipients: List of phone numbers
            content: SMS body
            subject: Ignored for SMS
        
        Returns:
            BatchMessageSendResult with success/failure per recipient
        """
        successful_recipients = []
        failed_recipients = {}
        external_ids = {}
        
        for recipient in recipients:
            result = await self.send(recipient, content, subject)
            if result.success:
                successful_recipients.append(recipient)
                external_ids[recipient] = result.external_id
            else:
                failed_recipients[recipient] = result.error
        
        return BatchMessageSendResult(
            successful_recipients=successful_recipients,
            failed_recipients=failed_recipients,
            external_ids=external_ids
        )
