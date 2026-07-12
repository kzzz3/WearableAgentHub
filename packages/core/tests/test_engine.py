"""Tests for AgentEngine."""
import pytest
import json
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


class TestAgentEngine:
    @pytest.mark.asyncio
    async def test_process_returns_structured(self, engine):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "type": "text_reply",
            "content": "Hello!"
        })
        engine.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await engine.process("hi")
        assert result["structured"]["type"] == "text_reply"
        assert result["structured"]["content"] == "Hello!"

    @pytest.mark.asyncio
    async def test_process_handles_llm_error(self, engine):
        engine.client.chat.completions.create = AsyncMock(side_effect=Exception("API down"))

        result = await engine.process("hi")
        assert result["structured"]["type"] == "text_reply"
        assert "error" in result["structured"]["content"].lower()

    @pytest.mark.asyncio
    async def test_session_history(self, engine):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "type": "text_reply",
            "content": "reply"
        })
        engine.client.chat.completions.create = AsyncMock(return_value=mock_response)

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
