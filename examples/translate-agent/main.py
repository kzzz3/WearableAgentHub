"""Translate Agent — standalone A2A service for text translation.

Run:
    E:\Miniconda3\envs\expr\python.exe examples/translate-agent/main.py

Listens on port 8001 by default.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Load .env from project root (two levels up)
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simple dictionary-based translator (no external API needed for demo)
# ---------------------------------------------------------------------------

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "hello": {"zh": "你好", "es": "hola", "ja": "こんにちは", "fr": "bonjour", "de": "hallo"},
    "goodbye": {"zh": "再见", "es": "adiós", "ja": "さようなら", "fr": "au revoir", "de": "auf wiedersehen"},
    "thank you": {"zh": "谢谢", "es": "gracias", "ja": "ありがとう", "fr": "merci", "de": "danke"},
    "good morning": {"zh": "早上好", "es": "buenos días", "ja": "おはよう", "fr": "bonjour", "de": "guten morgen"},
    "how are you": {"zh": "你好吗", "es": "cómo estás", "ja": "お元気ですか", "fr": "comment allez-vous", "de": "wie geht es dir"},
    "i love you": {"zh": "我爱你", "es": "te quiero", "ja": "愛してる", "fr": "je t'aime", "de": "ich liebe dich"},
    "please": {"zh": "请", "es": "por favor", "ja": "お願いします", "fr": "s'il vous plaît", "de": "bitte"},
    "yes": {"zh": "是", "es": "sí", "ja": "はい", "fr": "oui", "de": "ja"},
    "no": {"zh": "不", "es": "no", "ja": "いいえ", "fr": "non", "de": "nein"},
    "sorry": {"zh": "对不起", "es": "lo siento", "ja": "ごめんなさい", "fr": "pardon", "de": "entschuldigung"},
    "world": {"zh": "世界", "es": "mundo", "ja": "世界", "fr": "monde", "de": "Welt"},
}

# Language name -> code mapping
_LANG_CODES: dict[str, str] = {
    "chinese": "zh", "中文": "zh", "zh": "zh",
    "spanish": "es", "español": "es", "es": "es",
    "japanese": "ja", "日语": "ja", "日文": "ja", "ja": "ja",
    "french": "fr", "法语": "fr", "法文": "fr", "fr": "fr",
    "german": "de", "德语": "de", "德文": "de", "de": "de",
}


def _detect_target_lang(text: str) -> str:
    """Detect target language from the request text."""
    lower = text.lower()
    for name, code in _LANG_CODES.items():
        if name in lower:
            return code
    return "zh"  # default to Chinese


def _extract_text_to_translate(request_text: str) -> str:
    """Extract the text to translate from natural language request.

    Examples:
        "translate hello world" -> "hello world"
        "把 hello 翻译成中文" -> "hello"
        "翻译 thank you" -> "thank you"
    """
    lower = request_text.lower().strip()

    # Strip common prefixes
    for prefix in ["translate ", "翻译 ", "翻译", "把 ", "用中文说 ", "用中文说"]:
        if lower.startswith(prefix):
            lower = lower[len(prefix):].strip()
            break

    # Strip "to chinese/spanish/..." suffixes
    for lang_name in _LANG_CODES:
        suffix = f" to {lang_name}"
        if lower.endswith(suffix):
            lower = lower[: -len(suffix)].strip()
            suffix2 = f"in {lang_name}"
            if lower.endswith(suffix2):
                lower = lower[: -len(suffix2)].strip()

    # Strip "成中文" etc.
    for suffix in ["成中文", "成日文", "成法文", "成德文", "成西班牙文"]:
        if lower.endswith(suffix):
            lower = lower[: -len(suffix)].strip()

    return lower.strip('"').strip("'")


def translate(text: str, target_lang: str = "zh") -> str:
    """Translate text using the dictionary lookup."""
    normalized = text.lower().strip()

    if normalized in _TRANSLATIONS:
        return _TRANSLATIONS[normalized].get(target_lang, f"[no {target_lang} translation]")

    # Try word-by-word
    words = normalized.split()
    if len(words) > 1:
        translated_parts = []
        for word in words:
            if word in _TRANSLATIONS:
                translated_parts.append(_TRANSLATIONS[word].get(target_lang, word))
            else:
                translated_parts.append(f"[{word}]")
        return " ".join(translated_parts)

    return f"[unknown: {text}]"


# ---------------------------------------------------------------------------
# A2A Agent Executor
# ---------------------------------------------------------------------------


def build_translate_agent_card() -> AgentCard:
    return AgentCard(
        name="translate-agent",
        description="Translates text between languages. Supports Chinese, Spanish, Japanese, French, German.",
        version="0.1.0",
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                name="translate",
                description="Translate text to another language (Chinese, Spanish, Japanese, French, German)",
            ),
        ],
    )


class TranslateAgentExecutor(AgentExecutor):
    """A2A executor for translation."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_text = context.get_user_input()
        task_id = context.task_id or ""
        context_id = context.context_id or ""
        updater = TaskUpdater(event_queue, task_id, context_id)

        if not user_text:
            err = updater.new_agent_message(parts=[Part(text="No text to translate")])
            await updater.failed(err)
            return

        logger.info("Translate request: %s", user_text[:100])

        target_lang = _detect_target_lang(user_text)
        text_to_translate = _extract_text_to_translate(user_text)
        translated = translate(text_to_translate, target_lang)

        reply = f"{text_to_translate} → {translated}"

        response_msg = updater.new_agent_message(
            parts=[Part(text=reply)],
            metadata={"source": "translate-agent", "target_lang": target_lang},
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
    logger.info("Translate Agent started on port %s", os.getenv("TRANSLATE_AGENT_PORT", "8001"))
    yield
    logger.info("Translate Agent shutting down")


app = FastAPI(
    title="Translate Agent",
    description="A2A translate agent for WearableAgent Hub",
    version="0.1.0",
    lifespan=lifespan,
)


def _mount():
    card = build_translate_agent_card()
    executor = TranslateAgentExecutor()
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
    return {"status": "ok", "agent": "translate-agent"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("TRANSLATE_AGENT_PORT", "8001"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
