import uuid
from datetime import datetime

from src.db.models import User, Conversation, ChatMessage, UserRole, ConversationStatus


def test_user_model_fields():
    user = User(
        google_id="google_123",
        email="test@example.com",
        name="Test User",
        role=UserRole.CUSTOMER,
    )
    assert user.google_id == "google_123"
    assert user.role == UserRole.CUSTOMER


def test_conversation_model_fields():
    conv = Conversation(
        user_id=uuid.uuid4(),
        status="active",
        current_phase="intake",
        langgraph_thread_id="thread_abc",
    )
    assert conv.status == "active"
    assert conv.langgraph_thread_id == "thread_abc"


def test_chat_message_model_fields():
    msg = ChatMessage(
        conversation_id=uuid.uuid4(),
        role="assistant",
        content="Hello",
        tool_name=None,
        tool_data=None,
    )
    assert msg.role == "assistant"
    assert msg.content == "Hello"


def test_user_role_enum():
    assert UserRole.CUSTOMER.value == "customer"
    assert UserRole.OFFICER.value == "officer"


def test_conversation_status_enum():
    assert ConversationStatus.ACTIVE.value == "active"
    assert ConversationStatus.COMPLETED.value == "completed"
    assert ConversationStatus.PAUSED.value == "paused"
