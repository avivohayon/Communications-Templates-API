"""
Channel Factory for selecting message channels.

Returns the appropriate channel (Email/SMS) based on channel type.
"""
import logging

from src.models.enums import ChannelType
from src.services.channels.base_channel import MessageChannel
from src.services.channels.sendgrid_channel import SendGridChannel
from src.services.channels.twilio_channel import TwilioChannel

logger = logging.getLogger(__name__)


class ChannelFactory:
    """
    Factory for creating message channel instances.
    
    Design Pattern: Factory Pattern
    - Decouples channel selection from business logic
    - Easy to add new channels (WhatsApp, Slack, etc.)
    - Centralized channel configuration
    """
    
    @staticmethod
    def get_channel(channel_type: ChannelType) -> MessageChannel:
        """
        Get the appropriate channel instance based on channel type.
        
        Args:
            channel_type: Email or SMS
        
        Returns:
            MessageChannel instance (SendGridChannel or TwilioChannel)
        
        Raises:
            ValueError: If channel_type is not supported
        
        Examples:
            >>> factory = ChannelFactory()
            >>> email_channel = factory.get_channel(ChannelType.EMAIL)
            >>> sms_channel = factory.get_channel(ChannelType.SMS)
        """
        if channel_type == ChannelType.EMAIL:
            logger.debug("Creating SendGrid email channel")
            return SendGridChannel()
        elif channel_type == ChannelType.SMS:
            logger.debug("Creating Twilio SMS channel")
            return TwilioChannel()
        else:
            error = f"Unsupported channel type: {channel_type}"
            logger.error(error)
            raise ValueError(error)
