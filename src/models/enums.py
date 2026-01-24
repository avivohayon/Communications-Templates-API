from enum import Enum


class ChannelType(str, Enum):
    """
    Enum for communication channel types.
    
    Maps to PostgreSQL ENUM in database.
    """
    EMAIL = "email"
    SMS = "sms"


class MessageStatus(str, Enum):
    """
    Enum for message delivery status.
    
    Maps to PostgreSQL ENUM in database.
    """
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
