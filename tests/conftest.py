"""
Pytest fixtures for unit tests.

Provides common mocks and sample data for all tests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.fixture
def mock_db():
    """
    Mock database session for unit tests.
    
    Mocks all async database operations to avoid real DB connections.
    """
    db = AsyncMock()
    db.add = MagicMock()
    db.add_all = MagicMock()  # For bulk inserts
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_template_id():
    """Generate a sample UUID for testing."""
    return uuid4()


@pytest.fixture
def sample_email_template(sample_template_id):
    """
    Sample email template data for testing.
    
    Contains Jinja2 variables: name, code
    """
    return {
        "id": sample_template_id,
        "name": "welcome_email",
        "channel_type": "email",
        "subject": "Welcome {{ name }}!",
        "content": "Hello {{ name }}, your code is {{ code }}.",
        "status": "active",
        "creation_date": 1234567890,
        "update_date": 1234567890
    }


@pytest.fixture
def sample_sms_template(sample_template_id):
    """
    Sample SMS template data for testing.
    
    Contains Jinja2 variables: otp, minutes
    """
    return {
        "id": sample_template_id,
        "name": "otp_sms",
        "channel_type": "sms",
        "content": "Your OTP is {{ otp }}. Valid for {{ minutes }} minutes.",
        "status": "active",
        "creation_date": 1234567890,
        "update_date": 1234567890
    }
