"""Tests for message models."""
from src.models.message import Message, Role, ChatRequest, ChatResponse


def test_message_creation():
    msg = Message(role=Role.USER, content="hello")
    assert msg.role == Role.USER
    assert msg.content == "hello"
    assert msg.id
    assert msg.timestamp


def test_chat_request():
    req = ChatRequest(message="test", session_id="s1")
    assert req.message == "test"
    assert req.session_id == "s1"


def test_chat_request_default_session():
    req = ChatRequest(message="test")
    assert req.session_id == "default"


def test_chat_response():
    resp = ChatResponse(reply="ok", a2ui_messages=[{"type": "test"}], session_id="s1")
    assert resp.reply == "ok"
    assert len(resp.a2ui_messages) == 1
