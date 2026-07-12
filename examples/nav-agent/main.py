"""Nav Agent — A2A service that provides navigation and nearby search.

Run:
    E:/Miniconda3/envs/expr/python.exe examples/nav-agent/main.py

Listens on port 8003 by default.
Provides nearby POI search for wearable devices.
"""

from __future__ import annotations

import logging
import os
import random

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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

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
# LLM category classification via tool-call
# ---------------------------------------------------------------------------

_CATEGORY_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_cafe",
            "description": "Search for cafes or coffee shops",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_restaurant",
            "description": "Search for restaurants",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_hospital",
            "description": "Search for hospitals or medical facilities",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_pharmacy",
            "description": "Search for pharmacies",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_hotel",
            "description": "Search for hotels",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_park",
            "description": "Search for parks",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_gas_station",
            "description": "Search for gas stations",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_atm",
            "description": "Search for ATMs or banks",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        },
    },
]

_CATEGORY_SYSTEM_PROMPT = (
    "You are a navigation intent classifier. "
    "Given a user request, select the most appropriate search category using exactly one tool call. "
    "If no category fits, call search_restaurant as the general default."
)

# LLM category name → internal key
_CATEGORY_MAP = {
    "search_cafe": "cafe",
    "search_restaurant": "restaurant",
    "search_hospital": "hospital",
    "search_pharmacy": "pharmacy",
    "search_hotel": "hotel",
    "search_park": "park",
    "search_gas_station": "gas_station",
    "search_atm": "atm",
}


async def _llm_classify_category(text: str) -> str | None:
    """Use LLM tool-call to classify POI category. Returns category key or None on error."""
    llm = _get_llm()
    if llm is None:
        return None
    try:
        resp = await llm.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": _CATEGORY_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            tools=_CATEGORY_TOOLS,
            tool_choice="auto",
            temperature=0,
        )
        choice = resp.choices[0]
        if choice.message.tool_calls:
            fn_name = choice.message.tool_calls[0].function.name
            return _CATEGORY_MAP.get(fn_name)
        return None
    except Exception as e:
        logger.warning("LLM category classification failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Keyword fallback (used when LLM is unavailable)
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "cafe": ["coffee", "cafe", "咖啡", "茶", "tea", "咖啡馆"],
    "restaurant": ["food", "eat", "restaurant", "餐厅", "吃饭", "美食"],
    "hospital": ["hospital", "doctor", "医院", "看病", "诊所", "clinic"],
    "pharmacy": ["pharmacy", "drugstore", "药房", "药店", "medicine"],
    "hotel": ["hotel", "住宿", "酒店", "宾馆", "旅馆"],
    "park": ["park", "公园", "playground", "garden"],
    "gas_station": ["gas", "fuel", "加油站", "petrol"],
    "atm": ["atm", "bank", "银行", "取钱", "cash"],
}


def _keyword_detect_category(text: str) -> str:
    """Fallback keyword-based category detection."""
    lower = text.lower()
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return cat
    return "restaurant"  # default


async def detect_category(text: str) -> str:
    """Detect POI category: try LLM first, fall back to keywords."""
    llm_result = await _llm_classify_category(text)
    if llm_result is not None:
        return llm_result
    return _keyword_detect_category(text)


# ---------------------------------------------------------------------------
# Mock POI data per category
# ---------------------------------------------------------------------------

_POIS: dict[str, list[dict]] = {
    "cafe": [
        {"name": "Starbucks Reserve", "distance": "120m", "rating": "4.8"},
        {"name": "Blue Bottle Coffee", "distance": "350m", "rating": "4.7"},
        {"name": "% Arabica", "distance": "500m", "rating": "4.6"},
    ],
    "restaurant": [
        {"name": "鼎泰丰", "distance": "200m", "rating": "4.9"},
        {"name": "海底捞", "distance": "450m", "rating": "4.7"},
        {"name": "Shake Shack", "distance": "380m", "rating": "4.5"},
    ],
    "hospital": [
        {"name": "协和医院", "distance": "800m", "rating": "4.9"},
        {"name": "同仁医院", "distance": "1.2km", "rating": "4.8"},
    ],
    "pharmacy": [
        {"name": "屈臣氏", "distance": "150m", "rating": "4.3"},
        {"name": "国大药房", "distance": "300m", "rating": "4.5"},
    ],
    "hotel": [
        {"name": "W Hotel", "distance": "600m", "rating": "4.8"},
        {"name": "全季酒店", "distance": "400m", "rating": "4.4"},
    ],
    "park": [
        {"name": "中央公园", "distance": "250m", "rating": "4.9"},
        {"name": "城市花园", "distance": "500m", "rating": "4.6"},
    ],
    "gas_station": [
        {"name": "中石化加油站", "distance": "1km", "rating": "4.2"},
        {"name": "Shell", "distance": "1.5km", "rating": "4.3"},
    ],
    "atm": [
        {"name": "工商银行 ATM", "distance": "100m", "rating": "4.0"},
        {"name": "招商银行", "distance": "250m", "rating": "4.2"},
    ],
}


def _search_pois(category: str, query: str) -> list[dict]:
    """Return mock POI list for a category with slight random variation."""
    pois = _POIS.get(category, _POIS["restaurant"])
    # Add slight distance variation to simulate "real" search
    results = []
    for poi in pois:
        results.append({
            "name": poi["name"],
            "distance": poi["distance"],
            "rating": poi["rating"],
        })
    return results


# ---------------------------------------------------------------------------
# A2A Agent Executor
# ---------------------------------------------------------------------------


def build_nav_agent_card() -> AgentCard:
    return AgentCard(
        name="nav-agent",
        description="Provides nearby navigation and POI search for wearable devices.",
        version="0.1.0",
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                name="nearby-search",
                description="Search for nearby points of interest (restaurants, cafes, hospitals, etc.)",
            ),
        ],
    )


class NavAgentExecutor(AgentExecutor):
    """A2A executor for navigation search."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_text = context.get_user_input()
        task_id = context.task_id or ""
        context_id = context.context_id or ""
        updater = TaskUpdater(event_queue, task_id, context_id)

        if not user_text:
            err = updater.new_agent_message(parts=[Part(text="No search query provided")])
            await updater.failed(err)
            return

        logger.info("Nav-agent request: %s", user_text[:100])

        # LLM-based category detection (falls back to keywords if no LLM)
        category = await detect_category(user_text)
        pois = _search_pois(category, user_text)

        # Format as location_list for A2UI
        places = [
            {"name": p["name"], "distance": p["distance"], "rating": p["rating"]}
            for p in pois
        ]

        import json

        a2ui_payload = {
            "type": "location_list",
            "title": f"Nearby {category.title()}",
            "places": places,
        }

        reply = json.dumps(a2ui_payload, ensure_ascii=False)

        response_msg = updater.new_agent_message(
            parts=[Part(text=reply)],
            metadata={
                "source": "nav-agent",
                "category": category,
                "result_count": len(places),
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
    logger.info("Nav Agent started on port %s", os.getenv("NAV_AGENT_PORT", "8003"))
    yield
    logger.info("Nav Agent shutting down")


app = FastAPI(
    title="Nav Agent",
    description="A2A navigation agent for WearableAgent Hub",
    version="0.1.0",
    lifespan=lifespan,
)


def _mount():
    card = build_nav_agent_card()
    executor = NavAgentExecutor()
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
    return {"status": "ok", "agent": "nav-agent"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("NAV_AGENT_PORT", "8003"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
