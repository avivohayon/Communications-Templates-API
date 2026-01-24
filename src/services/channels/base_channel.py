"""
Base MessageChannel interface for sending messages.

This abstract class defines the contract for all message channels (Email, SMS, etc.).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MessageSendResult:
    """
    Result of a message send operation.
    
    Attributes:
        success: True if message sent successfully
        external_id: External API message ID (SendGrid ID, Twilio SID, etc.)
        error: Error message if failed
    """
    success: bool
    external_id: str | None = None
    error: str | None = None


@dataclass
class BatchMessageSendResult:
    """
    Result of a batch message send operation.
    
    Attributes:
        successful_recipients: List of recipients that received the message successfully
        failed_recipients: Dictionary mapping failed recipients to their error messages
        external_ids: Dictionary mapping recipients to their external message IDs
    """
    successful_recipients: list[str]
    failed_recipients: dict[str, str]  # recipient -> error
    external_ids: dict[str, str]  # recipient -> external_id


class MessageChannel(ABC):
    """
    Abstract base class for message channels.
    
    All channel implementations (Email, SMS, WhatsApp, etc.) must inherit from this
    and implement the `send` method.
    
    Design Pattern: Template Method / Strategy Pattern
    - Each channel implements its own send logic
    - Consumers don't need to know implementation details
    """
    
    @abstractmethod
    async def send(
        self,
        recipient: str,
        content: str,
        subject: str | None = None
    ) -> MessageSendResult:
        """
        Send a message via this channel.
        
        Args:
            recipient: Recipient address (email or phone number)
            content: Message content (HTML for email, text for SMS)
            subject: Message subject (required for email, ignored for SMS)
        
        Returns:
            MessageSendResult with success status and external ID
        
        Raises:
            Exception: Channel-specific errors (API failures, network issues, etc.)
        """
        pass
