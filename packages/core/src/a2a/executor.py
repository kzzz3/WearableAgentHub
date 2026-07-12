"""WearableAgent Hub main A2A executor.

Implements the a2a-sdk AgentExecutor interface so the core engine
can be reached via the A2A JSON-RPC protocol.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    Message as A2AMessage,
    Part,
    Role,
)

from ..engine.agent_engine import AgentEngine
from ..a2ui.generator import A2UIGenerator

logger = logging.getLogger(__name__)


def build_agent_card() -> AgentCard:
    """Build the AgentCard for the WearableAgent Hub main agent."""
    return AgentCard(
        name="wearable-agent-hub",
        description=(
            "AI assistant for wearable devices. Answers questions and renders "
            "results as HUD-style A2UI components on smart glasses / watches."
        ),
        version="0.2.0",
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                name="general-qa",
                description="Answer general questions concisely for a wearable HUD display",
            ),
            AgentSkill(
                name="nearby-search",
                description="Search for nearby places (cafes, restaurants, etc.)",
            ),
        ],
    )


class WearableAgentExecutor(AgentExecutor):
    """A2A executor backed by the existing AgentEngine + A2UIGenerator."""

    def __init__(self, engine: AgentEngine, a2ui: A2UIGenerator) -> None:
        self.engine = engine
        self.a2ui = a2ui

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Process an A2A request and publish the result to the event queue."""
        user_text = context.get_user_input()
        task_id = context.task_id or ""
        context_id = context.context_id or ""

        updater = TaskUpdater(event_queue, task_id, context_id)

        if not user_text:
            err_msg = updater.new_agent_message(parts=[Part(text="No text content in request")])
            await updater.failed(err_msg)
            return

        logger.info("A2A execute: task=%s text=%s", task_id, user_text[:80])

        try:
            result = await self.engine.process(user_text, session_id=f"a2a-{task_id}")

            reply_text = result.get("reply", "")
            structured = result.get("structured", {})

            a2ui_messages = self.a2ui.generate(structured)
            a2ui_json = json.dumps(a2ui_messages, ensure_ascii=False)

            # Build response message with two parts: text + A2UI data
            parts = [
                Part(text=reply_text),
                Part(
                    text=a2ui_json,
                    metadata={"content_type": "application/a2ui+json"},
                ),
            ]

            response_msg = updater.new_agent_message(parts=parts)

            await updater.complete(response_msg)
            logger.info("A2A execute complete: task=%s", task_id)

        except Exception as exc:
            logger.exception("A2A execute failed: task=%s", task_id)
            err_msg = updater.new_agent_message(parts=[Part(text=f"Agent error: {exc}")])
            await updater.failed(err_msg)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel is not supported for this agent."""
        task_id = context.task_id or "unknown"
        logger.warning("Cancel requested for task=%s (not supported)", task_id)
        updater = TaskUpdater(event_queue, task_id, context.context_id or "")
        err_msg = updater.new_agent_message(parts=[Part(text="Cancellation not supported")])
        await updater.cancel(err_msg)
