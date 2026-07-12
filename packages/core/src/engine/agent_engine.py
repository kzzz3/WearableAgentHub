"""Agent core engine: receives user input, calls LLM, returns structured response."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from ..config import settings
from ..models.message import Message, Role

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI assistant for wearable devices (smart glasses and smartwatch).
You respond concisely and helpfully. Your responses will be rendered on a small HUD display.

When the user asks for information, respond with a JSON object in the following format:
{
  "type": "info_card",
  "title": "short title",
  "subtitle": "optional subtitle",
  "items": ["item 1", "item 2", "item 3"],
  "summary": "one-line summary"
}

When the user asks a general question, respond with:
{
  "type": "text_reply",
  "content": "your concise answer"
}

When the user asks for directions or location-based info, respond with:
{
  "type": "location_list",
  "title": "Nearby Places",
  "places": [
    {"name": "Place Name", "distance": "200m", "rating": "4.5"}
  ]
}

Always respond ONLY with valid JSON. No markdown, no explanation outside the JSON.
Keep responses short and suitable for a small wearable display.
"""

ROLE_MAP = {
    Role.USER: "user",
    Role.AGENT: "assistant",
}


class AgentEngine:
    """Core agent engine that processes user messages via LLM."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.sessions: dict[str, list[Message]] = {}

    def _build_messages(self, session_id: str, user_input: str) -> list[dict[str, str]]:
        """Build the full message list for the LLM call."""
        history: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        for msg in self.sessions.get(session_id, []):
            history.append({"role": ROLE_MAP[msg.role], "content": msg.content})
        history.append({"role": "user", "content": user_input})
        return history

    async def process(self, user_input: str, session_id: str = "default") -> dict[str, Any]:
        """
        Process user input through LLM and return structured response.
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        messages = self._build_messages(session_id, user_input)

        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
            raw_reply = response.choices[0].message.content or ""
        except Exception as e:
            logger.exception("LLM call failed")
            raw_reply = json.dumps({
                "type": "text_reply",
                "content": f"Sorry, I encountered an error: {e!s}",
            })

        structured = self._parse_structured(raw_reply)

        self.sessions[session_id].append(Message(role=Role.USER, content=user_input))
        self.sessions[session_id].append(Message(role=Role.AGENT, content=raw_reply))

        return {
            "reply": raw_reply,
            "structured": structured,
            "session_id": session_id,
        }

    def _parse_structured(self, raw: str) -> dict[str, Any]:
        """Try to parse LLM response as structured JSON."""
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "type" in data:
                return data
        except json.JSONDecodeError:
            pass

        if "```" in raw:
            try:
                start = raw.index("{")
                end = raw.rindex("}") + 1
                data = json.loads(raw[start:end])
                if isinstance(data, dict) and "type" in data:
                    return data
            except (ValueError, json.JSONDecodeError):
                pass

        return {"type": "text_reply", "content": raw}