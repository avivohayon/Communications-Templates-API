"""
Message Sending API Router.

Provides endpoint for sending messages via templates.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.logic.logic_message import MessageLogic
from src.schemas.schema_message import SendMessageRequest, SendMessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Messages"])


@router.post(
    "/send",
    response_model=SendMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Send messages via template"
)
async def send_messages(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    message_logic: MessageLogic = Depends(MessageLogic)
):
    """
    Send messages to one or more recipients using a template.
    
    **Flow:**
    1. Fetch template by ID or name
    2. Render template content with provided data
    3. Send message via appropriate channel (SendGrid for email, Twilio for SMS)
    4. Record result in message history
    5. Return per-recipient results
    
    **Partial Success:**
    - If some recipients succeed and others fail, returns 200 OK with detailed results
    - Check `successful_count` and `failed_count` in response
    - Inspect `results` array for per-recipient status
    
    **Examples:**
    
    Send email using template name:
    ```json
    {
      "template_name": "welcome_email",
      "data": {"name": "John", "code": "123456"},
      "to": ["user@example.com"]
    }
    ```
    
    Send SMS using template ID:
    ```json
    {
      "template_id": "550e8400-e29b-41d4-a716-446655440000",
      "data": {"code": "123456"},
      "to": ["+15005550006", "+15005550007"]
    }
    ```
    """
    logger.info(f"Received send message request for template_id={request.template_id}, "
                f"template_name={request.template_name}, recipients={len(request.to)}")
    
    try:
        # Call message logic to orchestrate sending
        response = await message_logic.send_messages(db, request)
        
        logger.info(f"Message sending completed: {response.successful_count} succeeded, "
                   f"{response.failed_count} failed out of {response.total_recipients}")
        
        return response
        
    except ValueError as e:
        # Template not found, rendering errors, validation errors
        logger.warning(f"Validation error during message sending: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error sending messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while sending messages"
        )
