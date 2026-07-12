"""Tests for AgentEngine."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.engine.agent_engine import AgentEngine, SYSTEM_PROMPT


@pytest.fixture
def engine():
    with patch("src.engine.agent_engine.settings") as mock_settings:
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_base_url = "http://localhost"
        mock_settings.openai_model = "test-model"
        eng = AgentEngine()
        return eng


def _mock_tool_message(name: str, arguments: dict):
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.tool_calls = [MagicMock()]
    mock_message.tool_calls[0].function.name = name
    mock_message.tool_calls[0].function.arguments = json.dumps(arguments)
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = mock_message
    return mock_response


def _mock_text_message(payload: dict):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(payload)
    return mock_response


class TestAgentEngine:
    @pytest.mark.asyncio
    async def test_process_returns_structured(self, engine):
        engine.route_intent = AsyncMock(return_value=("direct_reply", {"message": "hi"}))
        engine.client.chat.completions.create = AsyncMock(
            return_value=_mock_text_message({"type": "text_reply", "content": "Hello!"})
        )

        result = await engine.process("hi")
        assert result["structured"]["type"] == "text_reply"
        assert result["structured"]["content"] == "Hello!"
        assert result["source"] == "local"

    @pytest.mark.asyncio
    async def test_process_handles_llm_error(self, engine):
        engine.route_intent = AsyncMock(return_value=("direct_reply", {"message": "hi"}))
        engine.client.chat.completions.create = AsyncMock(side_effect=Exception("API down"))

        result = await engine.process("hi")
        assert result["structured"]["type"] == "text_reply"
        assert "error" in result["structured"]["content"].lower()

    @pytest.mark.asyncio
    async def test_session_history(self, engine):
        engine.route_intent = AsyncMock(return_value=("direct_reply", {"message": "x"}))
        engine.client.chat.completions.create = AsyncMock(
            return_value=_mock_text_message({"type": "text_reply", "content": "reply"})
        )

        await engine.process("msg1", session_id="test")
        await engine.process("msg2", session_id="test")

        assert len(engine.sessions["test"]) == 4
        last_call = engine.client.chat.completions.create.call_args
        messages = last_call.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[-1]["content"] == "msg2"

    def test_parse_structured_valid_json(self, engine):
        result = engine._parse_structured('{"type": "text_reply", "content": "hi"}')
        assert result["type"] == "text_reply"

    def test_parse_structured_fallback(self, engine):
        result = engine._parse_structured("just plain text")
        assert result["type"] == "text_reply"
        assert "just plain text" in result["content"]

    def test_build_messages_uses_system_role(self, engine):
        messages = engine._build_messages("default", "test input")
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "test input"

    @pytest.mark.asyncio
    async def test_route_intent_returns_direct_reply_on_failure(self, engine):
        engine.client.chat.completions.create = AsyncMock(side_effect= Exception("routing failed"))

        name, args = await engine.route_intent("hello")
        assert name == "direct_reply"
        assert args["message"] == "hello"

    @pytest.mark.asyncio
    async def test_route_intent_parses_tool_call(self, engine):
        engine.client.chat.completions.create = AsyncMock(
            return_value=_mock_tool_message("delegate_translate", {"message": "translate hi"})
        )

        name, args = await engine.route_intent("translate hi")
        assert name == "delegate_translate"
        assert args["message"] == "translate hi"
