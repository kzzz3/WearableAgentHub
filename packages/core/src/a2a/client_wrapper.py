"""A2A Client wrapper for calling remote A2A agents from the core engine."""

from __future__ import annotations

import json
import logging
from typing import Any

from a2a.client.client_factory import create_client
from a2a.client.client import Client
from a2a.types import Message as A2AMessage, Part, Role, SendMessageRequest

logger = logging.getLogger(__name__)


class A2AClientWrapper:
    """Thin wrapper around the a2a-sdk client for calling remote agents."""

    def __init__(self, agent_url: str) -> None:
        self.agent_url = agent_url
        self._client: Client | None = None

    async def _get_client(self) -> Client:
        if self._client is None:
            self._client = await create_client(self.agent_url)
        return self._client

    async def send_message(
        self, text: str, task_id: str = "", context_id: str = ""
    ) -> dict[str, Any]:
        """Send a text message to a remote A2A agent and return the result.

        Returns:
            dict with keys: reply (str), a2ui_messages (list), raw_parts (list)
        """
        client = await self._get_client()

        msg = A2AMessage(
            role=Role.ROLE_USER,
            parts=[Part(text=text)],
            message_id=f"client-msg-{task_id}" if task_id else "",
            task_id=task_id,
            context_id=context_id,
        )
        request = SendMessageRequest(message=msg)

        reply_text = ""
        a2ui_messages: list[dict[str, Any]] = []
        raw_parts: list[dict[str, Any]] = []

        try:
            async for stream_event in client.send_message(request):
                # StreamResponse is a protobuf oneof with fields:
                #   task, message, status_update, artifact_update
                oneof_field = stream_event.WhichOneof("payload")

                if oneof_field == "message":
                    # Direct message response
                    resp_msg = stream_event.message
                    for part in resp_msg.parts:
                        if part.text:
                            meta = dict(part.metadata) if part.metadata else {}
                            if meta.get("content_type") == "application/a2ui+json":
                                try:
                                    a2ui_messages = json.loads(part.text)
                                except json.JSONDecodeError:
                                    pass
                            elif not reply_text:
                                reply_text = part.text
                            raw_parts.append({"text": part.text, "metadata": meta})

                elif oneof_field == "task":
                    # Task object — extract status message if present
                    task = stream_event.task
                    if task.HasField("status") and task.status.HasField("message"):
                        for part in task.status.message.parts:
                            if part.text and not reply_text:
                                reply_text = part.text

                elif oneof_field == "status_update":
                    # Status update event — check for agent message
                    update = stream_event.status_update
                    if update.HasField("status") and update.status.HasField("message"):
                        for part in update.status.message.parts:
                            if part.text:
                                meta = dict(part.metadata) if part.metadata else {}
                                if meta.get("content_type") == "application/a2ui+json":
                                    try:
                                        a2ui_messages = json.loads(part.text)
                                    except json.JSONDecodeError:
                                        pass
                                elif not reply_text:
                                    reply_text = part.text
                                raw_parts.append({"text": part.text, "metadata": meta})

                elif oneof_field == "artifact_update":
                    # Artifact — extract text from parts
                    artifact = stream_event.artifact_update
                    for part in artifact.artifact.parts:
                        if part.text:
                            meta = dict(part.metadata) if part.metadata else {}
                            if not reply_text:
                                reply_text = part.text
                            raw_parts.append({"text": part.text, "metadata": meta})

        except Exception as exc:
            logger.exception("A2A client call failed: %s", self.agent_url)
            reply_text = f"A2A call failed: {exc}"

        return {
            "reply": reply_text,
            "a2ui_messages": a2ui_messages,
            "raw_parts": raw_parts,
        }

    async def close(self) -> None:
        """Clean up the client."""
        self._client = None
