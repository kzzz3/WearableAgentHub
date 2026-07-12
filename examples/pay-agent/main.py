"""Pay Agent — A2A service that demonstrates x402 payment integration.

Run:
    E:/Miniconda3/envs/expr/python.exe examples/pay-agent/main.py

Listens on port 8004 by default.
Routes paid service requests through the x402 payment microservice.
"""

from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path

_env_path = Path(__file__).resolve().parents[2] / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Part,
)
from openai import AsyncOpenAI
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

X402_BASE_URL = os.getenv("X402_BASE_URL", "http://localhost:8002")

# ---------------------------------------------------------------------------
# LLM client (optional — falls back to keyword matching if unavailable)
# ---------------------------------------------------------------------------

def _get_llm() -> AsyncOpenAI | None:
    """Create LLM client if API key is configured."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return AsyncOpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL"),
    )


# ---------------------------------------------------------------------------
# LLM intent detection via tool-call
# ---------------------------------------------------------------------------

_PAID_INTENT_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "intent_translate",
            "description": "User wants paid/premium translation service",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The text or translation request"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "intent_premium_nav",
            "description": "User wants premium navigation or paid POI search",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The navigation request"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "intent_health_analysis",
            "description": "User wants paid health data analysis or health report",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The health analysis request"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "intent_none",
            "description": "User does not want any paid service",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

_PAID_INTENT_SYSTEM_PROMPT = (
    "You are a paid service intent classifier for a wearable assistant. "
    "The Pay Agent handles three paid services: translate, premium-nav, and health-analysis. "
    "Given a user message, select the appropriate service using exactly one tool call. "
    "If the message does not clearly request a paid service, call intent_none."
)

_INTENT_MAP = {
    "intent_translate": "translate",
    "intent_premium_nav": "premium-nav",
    "intent_health_analysis": "health-analysis",
    "intent_none": None,
}


async def _llm_detect_paid_intent(text: str) -> str | None:
    """Use LLM tool-call to detect paid service intent. Returns service key or None."""
    llm = _get_llm()
    if llm is None:
        return None
    try:
        resp = await llm.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": _PAID_INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            tools=_PAID_INTENT_TOOLS,
            tool_choice="auto",
            temperature=0,
        )
        choice = resp.choices[0]
        if choice.message.tool_calls:
            fn_name = choice.message.tool_calls[0].function.name
            return _INTENT_MAP.get(fn_name)
        return None
    except Exception as e:
        logger.warning("LLM paid intent detection failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Keyword fallback for paid intent
# ---------------------------------------------------------------------------

def _keyword_detect_paid_intent(text: str) -> str | None:
    """Fallback keyword-based paid intent detection."""
    lower = text.lower()

    if any(kw in lower for kw in ["premium nav", "付费导航", "高级导航"]):
        return "premium-nav"
    if any(kw in lower for kw in ["health analysis", "健康分析", "健康报告"]):
        return "health-analysis"
    if any(kw in lower for kw in ["paid translate", "付费翻译", "高级翻译", "premium translate"]):
        return "translate"

    return None


async def detect_paid_intent(text: str) -> str | None:
    """Detect paid service intent: try LLM first, fall back to keywords."""
    llm_result = await _llm_detect_paid_intent(text)
    if llm_result is not None:
        return llm_result
    return _keyword_detect_paid_intent(text)


# ---------------------------------------------------------------------------
# LLM-based POI response generation for premium nav
# ---------------------------------------------------------------------------

_PREMIUM_NAV_SYSTEM_PROMPT = (
    "You are a premium navigation assistant for wearable devices. "
    "Given a user request, return a JSON array of nearby POIs (realistic mock data). "
    "Each POI: {name, distance, rating, highlight}. "
    "Return 2-3 POIs. Use realistic names and details. "
    "Return ONLY valid JSON array, no markdown."
)


async def _llm_generate_premium_nav(query: str) -> list[dict]:
    """Use LLM to generate contextual premium nav POIs."""
    llm = _get_llm()
    if llm is None:
        return []
    try:
        resp = await llm.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": _PREMIUM_NAV_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        content = resp.choices[0].message.content or "[]"
        # Strip markdown fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(content)
    except Exception as e:
        logger.warning("LLM premium nav generation failed: %s", e)
        return []


# ---------------------------------------------------------------------------
# Keyword fallback for premium nav
# ---------------------------------------------------------------------------

_POI_FALLBACKS: dict[str, list[dict]] = {
    "cafe": [
        {"name": "☕ Starbucks Reserve", "distance": "120m", "rating": "4.8★", "highlight": "特调手冲 ¥38起, 预计等位5min"},
        {"name": "☕ % Arabica", "distance": "350m", "rating": "4.6★", "highlight": "网红打卡, 西班牙拿铁 ¥35"},
    ],
    "restaurant": [
        {"name": "🍜 鼎泰丰", "distance": "200m", "rating": "4.9★", "highlight": "小笼包招牌, 预计等位15min"},
        {"name": "🍕 Shake Shack", "distance": "380m", "rating": "4.5★", "highlight": "汉堡 ¥48起, 免排队"},
    ],
    "hospital": [
        {"name": "🏥 协和医院", "distance": "800m", "rating": "4.9★", "highlight": "三甲综合, 挂号等候约30min"},
    ],
    "pharmacy": [
        {"name": "💊 屈臣氏", "distance": "150m", "rating": "4.3★", "highlight": "24h营业, 医保可用"},
    ],
    "default": [
        {"name": "📍 附近热门地点", "distance": "200m", "rating": "4.5★", "highlight": "根据您的需求推荐"},
    ],
}


def _keyword_premium_nav(text: str) -> list[dict]:
    """Fallback keyword-based POI generation."""
    lower = text.lower()
    for key, words in [("cafe", ["coffee", "咖啡", "cafe"]),
                        ("restaurant", ["food", "eat", "餐厅", "吃饭"]),
                        ("hospital", ["hospital", "医院", "doctor"]),
                        ("pharmacy", ["pharmacy", "药房", "药店"])]:
        if any(w in lower for w in words):
            return _POI_FALLBACKS[key]
    return _POI_FALLBACKS["default"]


async def premium_nav_response(text: str) -> str:
    """Generate premium nav response: LLM first, keyword fallback."""
    pois = await _llm_generate_premium_nav(text)
    if not pois:
        pois = _keyword_premium_nav(text)

    lines = ["🌟 Premium Navigation\n"]
    for i, poi in enumerate(pois, 1):
        name = poi.get("name", "Unknown")
        dist = poi.get("distance", "")
        rating = poi.get("rating", "")
        highlight = poi.get("highlight", "")
        lines.append(f"{i}. {name} — {dist}, {rating}")
        if highlight:
            lines.append(f"   📍 {highlight}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Simple translation dictionary (subset)
# ---------------------------------------------------------------------------

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "hello": {"zh": "你好", "es": "hola", "ja": "こんにちは", "fr": "bonjour", "de": "hallo"},
    "goodbye": {"zh": "再见", "es": "adiós", "ja": "さようなら", "fr": "au revoir", "de": "auf wiedersehen"},
    "thank you": {"zh": "谢谢", "es": "gracias", "ja": "ありがとう", "fr": "merci", "de": "danke"},
    "good morning": {"zh": "早上好", "es": "buenos días", "ja": "おはよう", "fr": "bonjour", "de": "guten morgen"},
    "how are you": {"zh": "你好吗", "es": "cómo estás", "ja": "お元気ですか", "fr": "comment allez-vous", "de": "wie geht es dir"},
    "i love you": {"zh": "我爱你", "es": "te quiero", "ja": "愛してる", "fr": "je t'aime", "de": "ich liebe dich"},
    "world": {"zh": "世界", "es": "mundo", "ja": "世界", "fr": "monde", "de": "Welt"},
}

_LANG_CODES: dict[str, str] = {
    "chinese": "zh", "中文": "zh", "zh": "zh",
    "spanish": "es", "español": "es", "es": "es",
    "japanese": "ja", "日语": "ja", "日文": "ja", "ja": "ja",
    "french": "fr", "法语": "fr", "法文": "fr", "fr": "fr",
    "german": "de", "德语": "de", "德文": "de", "de": "de",
}


def _detect_target_lang(text: str) -> str:
    lower = text.lower()
    for name, code in _LANG_CODES.items():
        if name in lower:
            return code
    return "zh"


def _translate(text: str, target_lang: str = "zh") -> str:
    normalized = text.lower().strip()
    if normalized in _TRANSLATIONS:
        return _TRANSLATIONS[normalized].get(target_lang, f"[no {target_lang} translation]")
    words = normalized.split()
    if len(words) > 1:
        parts = []
        for w in words:
            if w in _TRANSLATIONS:
                parts.append(_TRANSLATIONS[w].get(target_lang, w))
            else:
                parts.append(f"[{w}]")
        return " ".join(parts)
    return f"[unknown: {text}]"


def _extract_text_to_translate(text: str) -> str:
    lower = text.lower().strip()
    for prefix in ["paid translate ", "付费翻译 ", "高级翻译 ", "premium translate ", "pro翻译 ", "翻译 ", "translate "]:
        if lower.startswith(prefix):
            return lower[len(prefix):].strip()
    return lower


def _health_analysis_response() -> str:
    return (
        "🏥 Premium Health Analysis Report\n\n"
        "📊 Heart Rate: 72 bpm (Normal)\n"
        "🫁 Blood Oxygen: 98% (Excellent)\n"
        "😴 Sleep Score: 85/100 (Good)\n"
        "🏃 Activity: 6,200 steps today\n\n"
        "💡 Recommendation: Increase water intake, maintain current activity level."
    )


# ---------------------------------------------------------------------------
# x402 Payment Client
# ---------------------------------------------------------------------------


async def _call_x402_pay(service: str) -> dict:
    """Call the x402 payment microservice."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{X402_BASE_URL}/pay",
            json={"service": service, "amount": "0.001"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# A2A Agent Card
# ---------------------------------------------------------------------------


def build_pay_agent_card() -> AgentCard:
    return AgentCard(
        name="pay-agent",
        description="Payment-enabled agent for premium services via x402.",
        version="0.1.0",
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                name="premium-translate",
                description="Premium translation with higher accuracy (x402)",
            ),
            AgentSkill(
                name="premium-nav",
                description="Navigation with ratings and wait times (x402)",
            ),
            AgentSkill(
                name="health-analysis",
                description="Wearable health data analysis report (x402)",
            ),
        ],
    )


class PayAgentExecutor(AgentExecutor):
    """A2A executor that handles paid services via x402."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_text = context.get_user_input()
        task_id = context.task_id or ""
        context_id = context.context_id or ""
        updater = TaskUpdater(event_queue, task_id, context_id)

        if not user_text:
            err = updater.new_agent_message(parts=[Part(text="No input provided")])
            await updater.failed(err)
            return

        logger.info("Pay-agent request: %s", user_text[:100])

        # LLM-based intent detection (falls back to keywords if no LLM)
        service = await detect_paid_intent(user_text)

        if service is None:
            reply = (
                "Pay Agent 可处理以下付费服务:\n"
                "1. 💬 付费翻译 — 说 \"付费翻译 hello\"\n"
                "2. 🌟 高级导航 — 说 \"premium导航 咖啡\"\n"
                "3. 🏥 健康分析 — 说 \"健康分析\"\n\n"
                "所有服务通过 x402 微支付结算。"
            )
            msg = updater.new_agent_message(parts=[Part(text=reply)])
            await updater.complete(msg)
            return

        # Step 1: Call x402 to pay
        try:
            receipt = await _call_x402_pay(service)
        except Exception as e:
            logger.error("x402 payment failed: %s", e)
            err = updater.new_agent_message(
                parts=[Part(text=f"Payment failed: {e}")],
            )
            await updater.failed(err)
            return

        # Step 2: Generate service-specific response
        if service == "translate":
            text_to_translate = _extract_text_to_translate(user_text)
            target_lang = _detect_target_lang(user_text)
            translated = _translate(text_to_translate, target_lang)
            service_result = f"🌐 Premium Translation\n\n{text_to_translate} → {translated}"
        elif service == "premium-nav":
            service_result = await premium_nav_response(user_text)
        elif service == "health-analysis":
            service_result = _health_analysis_response()
        else:
            service_result = f"Service '{service}' completed."

        # Step 3: Combine receipt + result
        tx_id = receipt.get("transactionId", "N/A")
        amount = receipt.get("amount", "N/A")
        full_reply = (
            f"{service_result}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💳 Payment Receipt\n"
            f"├ Service: {service}\n"
            f"├ Amount: {amount} ETH\n"
            f"├ TxID: {tx_id}\n"
            f"└ Status: ✅ Settled"
        )

        response_msg = updater.new_agent_message(
            parts=[Part(text=full_reply)],
            metadata={
                "source": "pay-agent",
                "service": service,
                "transaction_id": tx_id,
                "paid": True,
            },
        )
        await updater.complete(response_msg)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id or "unknown"
        updater = TaskUpdater(event_queue, task_id, context.context_id or "")
        err = updater.new_agent_message(parts=[Part(text="Cancel not supported")])
        await updater.cancel(err)


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Pay Agent started on port %s", os.getenv("PAY_AGENT_PORT", "8004"))
    yield
    logger.info("Pay Agent shutting down")


app = FastAPI(
    title="Pay Agent",
    description="A2A payment-enabled agent for WearableAgent Hub",
    version="0.1.0",
    lifespan=lifespan,
)


def _mount():
    card = build_pay_agent_card()
    executor = PayAgentExecutor()
    store = InMemoryTaskStore()
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=store,
        agent_card=card,
    )
    card_routes = create_agent_card_routes(card)
    rpc_routes = create_jsonrpc_routes(handler, rpc_url="/a2a")
    add_a2a_routes_to_fastapi(app, agent_card_routes=card_routes, jsonrpc_routes=rpc_routes)


_mount()


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "pay-agent"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PAY_AGENT_PORT", "8004"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
