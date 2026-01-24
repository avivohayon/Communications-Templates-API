"""
Unit tests for logic_message.py

Tests the full message sending orchestration flow with all dependencies mocked.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.logic.logic_message import MessageLogic
from src.schemas.schema_message import SendMessageRequest
from src.models.enums import ChannelType


class TestMessageSendingSuccess:
    """Test successful message sending scenarios."""
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_db):
        """Sending email with correct data should succeed."""
        logic = MessageLogic()
        
        # Mock template fetch
        from src.schemas.schema_template import EmailTemplateOut
        mock_template = EmailTemplateOut(
            id=uuid4(),
            name="welcome",
            channel_type=ChannelType.EMAIL,
            subject="Hi {{ name }}",
            content="Code: {{ code }}",
            status="active",
            creation_date=123,
            update_date=123
        )
        logic.template_logic.get_by_id = AsyncMock(return_value=mock_template)
        
        # Mock channel
        from tests.fixtures.mock_channels import MockEmailChannel
        mock_channel = MockEmailChannel(should_fail=False)
        logic.channel_factory.get_channel = MagicMock(return_value=mock_channel)
        
        # Mock history DA
        logic.history_da.insert_with_channel_data = AsyncMock()
        
        # Send message
        request = SendMessageRequest(
            template_id=mock_template.id,
            data={"name": "Aviv", "code": "123456"},
            to=["aviv@example.com"]
        )
        
        response = await logic.send_messages(mock_db, request)
        
        # Assertions
        assert response.successful_count == 1
        assert response.failed_count == 0
        assert len(response.results) == 1
        assert response.results[0].status == "success"
        assert response.results[0].recipient == "aviv@example.com"
        assert mock_channel.sent_messages[0]["subject"] == "Hi Aviv"
        assert "123456" in mock_channel.sent_messages[0]["content"]
    
    @pytest.mark.asyncio
    async def test_send_sms_success(self, mock_db):
        """Sending SMS with correct data should succeed."""
        logic = MessageLogic()
        
        # Mock template fetch
        from src.schemas.schema_template import SMSTemplateOut
        mock_template = SMSTemplateOut(
            id=uuid4(),
            name="otp",
            channel_type=ChannelType.SMS,
            content="OTP: {{ otp }}",
            status="active",
            creation_date=123,
            update_date=123
        )
        logic.template_logic.get_by_name = AsyncMock(return_value=mock_template)
        
        # Mock channel
        from tests.fixtures.mock_channels import MockSMSChannel
        mock_channel = MockSMSChannel(should_fail=False)
        logic.channel_factory.get_channel = MagicMock(return_value=mock_channel)
        
        # Mock history DA
        logic.history_da.insert_with_channel_data = AsyncMock()
        
        # Send message
        request = SendMessageRequest(
            template_name="otp",  # Test template_name instead of template_id
            data={"otp": "987654"},
            to=["+15005550006"]
        )
        
        response = await logic.send_messages(mock_db, request)
        
        # Assertions
        assert response.successful_count == 1
        assert response.results[0].status == "success"
        assert "987654" in mock_channel.sent_messages[0]["content"]
    
    @pytest.mark.asyncio
    async def test_send_to_multiple_recipients_all_succeed(self, mock_db):
        """Sending to multiple recipients should handle each independently."""
        logic = MessageLogic()
        
        # Mock template
        from src.schemas.schema_template import EmailTemplateOut
        mock_template = EmailTemplateOut(
            id=uuid4(),
            name="test",
            channel_type=ChannelType.EMAIL,
            subject="Hi",
            content="Test",
            status="active",
            creation_date=123,
            update_date=123
        )
        logic.template_logic.get_by_id = AsyncMock(return_value=mock_template)
        
        # Mock channel
        from tests.fixtures.mock_channels import MockEmailChannel
        mock_channel = MockEmailChannel(should_fail=False)
        logic.channel_factory.get_channel = MagicMock(return_value=mock_channel)
        logic.history_da.insert_with_channel_data = AsyncMock()
        
        # Send to 3 recipients
        request = SendMessageRequest(
            template_id=mock_template.id,
            data={},
            to=["user1@test.com", "user2@test.com", "user3@test.com"]
        )
        
        response = await logic.send_messages(mock_db, request)
        
        assert response.successful_count == 3
        assert response.failed_count == 0
        assert len(mock_channel.sent_messages) == 3


class TestMessageSendingFailures:
    """Test failure scenarios and error handling."""
    
    @pytest.mark.asyncio
    async def test_send_with_missing_variables_all_fail(self, mock_db):
        """
        CRITICAL: Missing variables should raise ValueError during rendering.
        
        Tests the exact scenario reported by the user where wrong variable
        names (name2 instead of name) should raise errors.
        Template rendering happens BEFORE individual sends, so it raises.
        """
        logic = MessageLogic()
        
        # Mock template with variables
        from src.schemas.schema_template import EmailTemplateOut
        mock_template = EmailTemplateOut(
            id=uuid4(),
            name="test",
            channel_type=ChannelType.EMAIL,
            subject="Hi {{ name }}",
            content="Code: {{ code }}",
            status="active",
            creation_date=123,
            update_date=123
        )
        logic.template_logic.get_by_id = AsyncMock(return_value=mock_template)
        
        # Send with wrong variable names
        request = SendMessageRequest(
            template_id=mock_template.id,
            data={"wrong_name": "Aviv", "wrong_code": "123"},  # Wrong keys!
            to=["user@test.com"]
        )
        
        # Should raise ValueError with clear message about missing variables
        with pytest.raises(ValueError) as exc_info:
            await logic.send_messages(mock_db, request)
        
        # Verify error message mentions the missing variable
        assert "rendering" in str(exc_info.value).lower() or "undefined" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_send_with_channel_failure(self, mock_db):
        """External API failure should be recorded properly."""
        logic = MessageLogic()
        
        # Mock template
        from src.schemas.schema_template import EmailTemplateOut
        mock_template = EmailTemplateOut(
            id=uuid4(),
            name="test",
            channel_type=ChannelType.EMAIL,
            subject="Hi",
            content="Test",
            status="active",
            creation_date=123,
            update_date=123
        )
        logic.template_logic.get_by_id = AsyncMock(return_value=mock_template)
        
        # Mock channel to fail
        from tests.fixtures.mock_channels import MockEmailChannel
        mock_channel = MockEmailChannel(should_fail=True)
        logic.channel_factory.get_channel = MagicMock(return_value=mock_channel)
        logic.history_da.insert_with_channel_data = AsyncMock()
        
        request = SendMessageRequest(
            template_id=mock_template.id,
            data={},
            to=["user@test.com"]
        )
        
        response = await logic.send_messages(mock_db, request)
        
        assert response.successful_count == 0
        assert response.failed_count == 1
        assert response.results[0].status == "failed"
        assert "Mock API error" in response.results[0].error_message
    
    @pytest.mark.asyncio
    async def test_send_template_not_found_raises_error(self, mock_db):
        """Non-existent template should raise clear error."""
        logic = MessageLogic()
        
        # Mock template not found
        logic.template_logic.get_by_id = AsyncMock(return_value=None)
        
        request = SendMessageRequest(
            template_id=uuid4(),
            data={},
            to=["user@test.com"]
        )
        
        with pytest.raises(ValueError) as exc_info:
            await logic.send_messages(mock_db, request)
        
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_send_partial_success_some_recipients_fail(self, mock_db):
        """Partial success: some recipients succeed, others fail."""
        logic = MessageLogic()
        
        # Mock template
        from src.schemas.schema_template import EmailTemplateOut
        mock_template = EmailTemplateOut(
            id=uuid4(),
            name="test",
            channel_type=ChannelType.EMAIL,
            subject="Hi",
            content="Test",
            status="active",
            creation_date=123,
            update_date=123
        )
        logic.template_logic.get_by_id = AsyncMock(return_value=mock_template)
        
        # Mock channel that alternates success/failure using a real mock channel
        from tests.fixtures.mock_channels import MockEmailChannel
        mock_channel = MockEmailChannel(should_fail=False)
        
        # Override send_batch to simulate partial failure
        original_send_batch = mock_channel.send_batch
        call_count = [0]
        
        async def partial_fail_send(recipient, content, subject=None):
            call_count[0] += 1
            from src.services.channels.base_channel import MessageSendResult
            if call_count[0] % 2 == 0:  # Fail every other
                return MessageSendResult(success=False, error="API limit")
            return MessageSendResult(success=True, external_id=f"msg-{call_count[0]}")
        
        mock_channel.send = partial_fail_send
        
        logic.channel_factory.get_channel = MagicMock(return_value=mock_channel)
        logic.history_da.insert_with_channel_data = AsyncMock()
        
        request = SendMessageRequest(
            template_id=mock_template.id,
            data={},
            to=["user1@test.com", "user2@test.com", "user3@test.com"]
        )
        
        response = await logic.send_messages(mock_db, request)
        
        # Partial success
        assert response.successful_count == 2  # 1st and 3rd succeeded
        assert response.failed_count == 1  # 2nd failed
        assert len(response.results) == 3
