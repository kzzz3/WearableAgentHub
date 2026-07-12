"""Agent core engine: receives user input, calls LLM, returns structured response."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from ..config import settings
from ..models.message import Message, Role
from ..x402.client import X402Client

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

INTENT_ROUTER_SYSTEM_PROMPT = (
    "You are a routing classifier for a wearable assistant. "
    "Decide how to handle the user message using exactly one tool call.\n\n"
    "Available tools:\n"
    "- delegate_translate: translate text between languages.\n"
    "- delegate_nav: search nearby places or give navigation-related results.\n"
    "- delegate_pay: use when the user asks for premium translation, premium navigation, health analysis, or another paid service.\n"
    "- direct_reply: answer directly without delegation.\n\n"
    "Rules:\n"
    "- Prefer delegation when the request clearly matches a tool.\n"
    "- Use direct_reply for general chat, weather, reminders, or unclear intent.\n"
    "- Do not explain. Only call one tool.\n"
)

INTENT_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "delegate_translate",
            "description": "Delegate the message to the translation agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Original user message"},
                },
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_nav",
            "description": "Delegate the message to the navigation / nearby-search agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Original user message"},
                },
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_pay",
            "description": "Delegate the message to a paid premium service via x402 payment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Original user message"},
                    "service": {
                        "type": "string",
                        "enum": ["translate", "premium-nav", "health-analysis"],
                        "description": "Target paid service slug",
                    },
                },
                "required": ["message", "service"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "direct_reply",
            "description": "Reply directly to the user without remote delegation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Original user message"},
                },
                "required": ["message"],
            },
        },
    },
]

INTENT_TOOL_NAMES = {t["function"]["name"] for t in INTENT_TOOLS}


class AgentEngine:
    """Core agent engine that processes user messages via LLM."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.sessions: dict[str, list[Message]] = {}
        self._a2a_client: Any | None = None
        self._x402_client: X402Client | None = None

    def set_a2a_client(self, client: Any) -> None:
        """Inject the A2A client wrapper for remote agent delegation."""
        self._a2a_client = client
        logger.info("A2A client wired into AgentEngine")

    def set_x402_client(self, client: X402Client) -> None:
        """Inject the x402 payment client for payment-aware processing."""
        self._x402_client = client
        logger.info("x402 payment client wired into AgentEngine")

    async def route_intent(self, user_input: str) -> tuple[str, dict[str, Any]]:
        """Use a single LLM tool call to determine intent routing.

        Returns (tool_name, tool_args). Falls back to direct_reply on ambiguity.
        """
        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": INTENT_ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input},
                ],
                tools=INTENT_TOOLS,
                tool_choice="auto",
                temperature=0,
                max_tokens=256,
            )

            message = response.choices[0].message
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                fn_name = tool_call.function.name
                if fn_name in INTENT_TOOL_NAMES:
                    try:
                        args = json.loads(tool_call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {"message": user_input}
                    return fn_name, args

        except Exception:
            logger.exception("LLM intent routing failed, falling back to direct_reply")

        return "direct_reply", {"message": user_input}

    async def _delegate_to_a2a(self, intent: str, user_input: str, session_id: str) -> dict[str, Any] | None:
        """Attempt to delegate to a remote A2A agent. Returns result dict or None on failure."""
        if self._a2a_client is None:
            return None

        try:
            result = await self._a2a_client.send_message(user_input)
            reply_text = result.get("reply", "")
            a2ui_messages = result.get("a2ui_messages", [])

            # Parse the reply into structured form if possible
            structured = self._parse_structured(reply_text) if reply_text else {
                "type": "text_reply",
                "content": "(A2A agent returned empty response)",
            }

            # If the remote agent provided A2UI messages, wrap them
            if a2ui_messages:
                structured["_a2ui_from_remote"] = True

            # Store in session history
            if session_id not in self.sessions:
                self.sessions[session_id] = []
            self.sessions[session_id].append(Message(role=Role.USER, content=user_input))
            self.sessions[session_id].append(Message(role=Role.AGENT, content=reply_text or "(A2A)"))

            return {
                "reply": reply_text,
                "structured": structured,
                "session_id": session_id,
                "source": "a2a",
                "a2ui_messages": a2ui_messages,
            }
        except Exception:
            logger.exception("A2A delegation failed for intent=%s", intent)
            return None

    async def _process_payment(self, service: str, user_input: str, session_id: str) -> dict[str, Any] | None:
        """Process payment via x402 client if available. Returns payment result or None."""
        if self._x402_client is None:
            logger.warning("x402 client not configured, skipping payment")
            return None

        try:
            payment_result = await self._x402_client.pay_and_settle(service)
            logger.info("Payment successful for service=%s: %s", service, payment_result)
            # Attach payment info to structured reply
            return {
                "payment": payment_result,
            }
        except Exception:
            logger.exception("Payment failed for service=%s", service)
            return None

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
        Process user input: use one LLM tool call to choose routing,
        optionally process payment and delegate via A2A, then fall back to local LLM.
        Returns structured response.
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        tool_name, tool_args = await self.route_intent(user_input)
        routed_input = tool_args.get("message", user_input)

        # Payment intent from classifier
        payment_service: str | None = None
        if tool_name == "delegate_pay":
            payment_service = tool_args.get("service", "translate")

        payment_info = None
        if payment_service:
            logger.info("Detected payment intent for service=%s", payment_service)
            payment_info = await self._process_payment(payment_service, routed_input, session_id)
            if payment_info is None:
                logger.warning("Payment processing failed or skipped, continuing without payment")

        # A2A delegation
        if tool_name in {"delegate_translate", "delegate_nav", "delegate_pay"}:
            intent = {
                "delegate_translate": "translate",
                "delegate_nav": "nav",
                "delegate_pay": "pay",
            }[tool_name]

            logger.info("Detected A2A intent: %s for input: %s", intent, user_input[:60])
            a2a_result = await self._delegate_to_a2a(intent, routed_input, session_id)
            if a2a_result is not None:
                if payment_info:
                    a2a_result["payment"] = payment_info.get("payment")
                return a2a_result

            logger.warning("A2A delegation failed for intent=%s, falling back to local LLM", intent)

        # Local LLM processing
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

        result = {
            "reply": raw_reply,
            "structured": structured,
            "session_id": session_id,
            "source": "local",
        }
        if payment_info:
            result["payment"] = payment_info.get("payment")
        return result

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
