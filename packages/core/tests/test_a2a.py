"""Tests for A2A integration: executor, client wrapper, and intent delegation."""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.engine.agent_engine import AgentEngine


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


class TestIntentDetection:
    @pytest.mark.asyncio
    async def test_translate_intent(self, engine):
        engine.client.chat.completions.create = AsyncMock(
            return_value=_mock_tool_message("delegate_translate", {"message": "translate hello"})
        )
        name, args = await engine.route_intent("translate hello")
        assert name == "delegate_translate"

    @pytest.mark.asyncio
    async def test_nav_intent(self, engine):
        engine.client.chat.completions.create = AsyncMock(
            return_value=_mock_tool_message("delegate_nav", {"message": "nearby cafes"})
        )
        name, args = await engine.route_intent("nearby cafes")
        assert name == "delegate_nav"

    @pytest.mark.asyncio
    async def test_pay_intent(self, engine):
        engine.client.chat.completions.create = AsyncMock(
            return_value=_mock_tool_message("delegate_pay", {"message": "premium translation", "service": "translate"})
        )
        name, args = await engine.route_intent("premium translation")
        assert name == "delegate_pay"
        assert args["service"] == "translate"

    @pytest.mark.asyncio
    async def test_direct_reply_intent(self, engine):
        engine.client.chat.completions.create = AsyncMock(
            return_value=_mock_tool_message("direct_reply", {"message": "what's the weather"})
        )
        name, args = await engine.route_intent("what's the weather")
        assert name == "direct_reply"


class TestA2ADelegation:
    @pytest.mark.asyncio
    async def test_delegates_to_a2a_on_translate(self, engine):
        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value={
            "reply": "hello → 你好",
            "a2ui_messages": [],
            "raw_parts": [],
        })
        engine.set_a2a_client(mock_client)
        engine.route_intent = AsyncMock(return_value=("delegate_translate", {"message": "translate hello"}))

        result = await engine.process("translate hello", session_id="test")

        assert result["source"] == "a2a"
        assert result["reply"] == "hello → 你好"
        mock_client.send_message.assert_called_once_with("translate hello")

    @pytest.mark.asyncio
    async def test_falls_back_to_local_on_a2a_failure(self, engine):
        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(side_effect=Exception("connection failed"))
        engine.set_a2a_client(mock_client)
        engine.route_intent = AsyncMock(return_value=("delegate_translate", {"message": "translate hello"}))
        engine.client.chat.completions.create = AsyncMock(
            return_value=_mock_text_message({"type": "text_reply", "content": "local fallback"})
        )

        result = await engine.process("translate hello", session_id="test")

        assert result["source"] == "local"
        assert result["structured"]["content"] == "local fallback"

    @pytest.mark.asyncio
    async def test_no_delegation_without_a2a_client(self, engine):
        engine.route_intent = AsyncMock(return_value=("delegate_translate", {"message": "translate hello"}))
        engine.client.chat.completions.create = AsyncMock(
            return_value=_mock_text_message({"type": "text_reply", "content": "local only"})
        )

        result = await engine.process("translate hello", session_id="test")

        assert result["source"] == "local"

    @pytest.mark.asyncio
    async def test_no_delegation_for_general_input(self, engine):
        mock_client = AsyncMock()
        engine.set_a2a_client(mock_client)
        engine.route_intent = AsyncMock(return_value=("direct_reply", {"message": "what is the weather"}))
        engine.client.chat.completions.create = AsyncMock(
            return_value=_mock_text_message({"type": "text_reply", "content": "general reply"})
        )

        result = await engine.process("what is the weather", session_id="test")

        assert result["source"] == "local"
        mock_client.send_message.assert_not_called()


class TestSetA2AClient:
    def test_set_client(self, engine):
        assert engine._a2a_client is None
        mock_client = MagicMock()
        engine.set_a2a_client(mock_client)
        assert engine._a2a_client is mock_client


class TestWearableAgentExecutor:
    @pytest.mark.asyncio
    async def test_execute_success(self):
        from src.a2a.executor import WearableAgentExecutor

        mock_engine = AsyncMock()
        mock_engine.process = AsyncMock(return_value={
            "reply": "test reply",
            "structured": {"type": "text_reply", "content": "test reply"},
        })

        mock_a2ui = MagicMock()
        mock_a2ui.generate = MagicMock(return_value=[{"type": "createSurface", "surfaceId": "test"}])

        executor = WearableAgentExecutor(mock_engine, mock_a2ui)

        mock_context = MagicMock()
        mock_context.get_user_input.return_value = "hello"
        mock_context.task_id = "task-1"
        mock_context.context_id = "ctx-1"

        mock_queue = AsyncMock()
        mock_queue.enqueue_event = AsyncMock()

        await executor.execute(mock_context, mock_queue)

        mock_engine.process.assert_called_once_with("hello", session_id="a2a-task-1")
        assert mock_queue.enqueue_event.call_count >= 1

    @pytest.mark.asyncio
    async def test_execute_empty_input(self):
        from src.a2a.executor import WearableAgentExecutor

        mock_engine = AsyncMock()
        mock_a2ui = MagicMock()
        executor = WearableAgentExecutor(mock_engine, mock_a2ui)

        mock_context = MagicMock()
        mock_context.get_user_input.return_value = ""
        mock_context.task_id = "task-2"
        mock_context.context_id = "ctx-2"

        mock_queue = AsyncMock()
        mock_queue.enqueue_event = AsyncMock()

        await executor.execute(mock_context, mock_queue)

        mock_engine.process.assert_not_called()


class TestBuildAgentCard:
    def test_agent_card_fields(self):
        from src.a2a.executor import build_agent_card

        card = build_agent_card()
        assert card.name == "wearable-agent-hub"
        assert card.version == "0.2.0"
        assert len(card.skills) >= 2
