"""WearableAgent Hub - FastAPI backend entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .a2a.client_wrapper import A2AClientWrapper
from .a2a.executor import WearableAgentExecutor
from .a2a.server_routes import mount_a2a_routes
from .a2ui.generator import A2UIGenerator
from .config import settings
from .engine.agent_engine import AgentEngine
from .models.message import ChatRequest
from .ws.manager import manager
from .x402.client import X402Client
from .x402.routes import router as x402_router
from .voice.routes import router as voice_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Shared instances
agent_engine: AgentEngine | None = None
a2ui_generator = A2UIGenerator()
a2a_executor: WearableAgentExecutor | None = None
a2a_client: A2AClientWrapper | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    """Application lifespan: startup and shutdown."""
    global agent_engine, a2a_executor, a2a_client

    # Initialize x402 payment client and store in app.state
    x402_client = X402Client(settings.x402_base_url)
    app.state.x402_client = x402_client

    agent_engine = AgentEngine()

    # Mount A2A server routes (adds /.well-known/agent-card.json + /a2a)
    a2a_executor = WearableAgentExecutor(agent_engine, a2ui_generator)
    mount_a2a_routes(app, a2a_executor)

    # Create A2A client for calling remote agents
    a2a_client = A2AClientWrapper(settings.a2a_base_url)

    # Wire clients into the agent engine
    agent_engine.set_a2a_client(a2a_client)
    agent_engine.set_x402_client(x402_client)

    logger.info(
        "WearableAgent Hub started — provider_type=%s, model=%s, base_url=%s, a2a=%s, x402=%s",
        settings.provider_type,
        settings.openai_model,
        settings.openai_base_url,
        settings.a2a_base_url,
        settings.x402_base_url,
    )
    yield

    if a2a_client:
        await a2a_client.close()
    if hasattr(app.state, "x402_client"):
        await app.state.x402_client.close()
    logger.info("WearableAgent Hub shutting down")


app = FastAPI(
    title="WearableAgent Hub",
    description="PC wearable device AI Agent simulator + A2A hub",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# x402 payment routes
app.include_router(x402_router)
app.include_router(voice_router)


def _resolve_a2ui(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve A2UI messages from agent result.

    Priority:
      1. Remote A2A agent provided A2UI messages directly (rich format).
      2. Locally generated from structured data (always works).
    """
    remote_a2ui = result.get("a2ui_messages")
    if remote_a2ui and isinstance(remote_a2ui, list) and len(remote_a2ui) > 0:
        logger.info("Using remote A2UI messages (%d items)", len(remote_a2ui))
        return remote_a2ui
    return a2ui_generator.generate(result["structured"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "model": settings.openai_model,
        "a2a_url": settings.a2a_base_url,
        "x402_url": settings.x402_base_url,
    }


class ChatAPIResponse(BaseModel):
    reply: str
    a2ui_messages: list[dict[str, Any]]
    session_id: str
    source: str = "local"
    payment: dict[str, Any] | None = None


@app.post("/chat", response_model=ChatAPIResponse)
async def chat(request: ChatRequest) -> ChatAPIResponse:
    """
    REST endpoint for chat. Processes user message through LLM,
    generates A2UI messages, and also pushes them via WebSocket.
    """
    if agent_engine is None:
        return ChatAPIResponse(
            reply="Agent engine not initialized",
            a2ui_messages=[],
            session_id=request.session_id,
        )

    result = await agent_engine.process(request.message, request.session_id)
    a2ui_messages = _resolve_a2ui(result)
    await manager.send_a2ui(request.session_id, a2ui_messages)

    return ChatAPIResponse(
        reply=result["reply"],
        a2ui_messages=a2ui_messages,
        session_id=request.session_id,
        source=result.get("source", "local"),
        payment=result.get("payment"),
    )


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    """
    WebSocket endpoint for real-time communication.
    Clients send text messages, server processes through agent and returns A2UI.
    """
    await manager.connect(websocket, session_id)
    await manager.send_event(session_id, "connected", {"session_id": session_id})

    try:
        while True:
            data = await websocket.receive_text()

            if agent_engine is None:
                await manager.send_event(session_id, "error", {"message": "Agent engine not ready"})
                continue

            await manager.send_event(session_id, "processing", {"status": "thinking"})

            result = await agent_engine.process(data, session_id)
            a2ui_messages = _resolve_a2ui(result)

            await manager.send_a2ui(session_id, a2ui_messages)
            await manager.send_event(session_id, "reply", {
                "content": result["reply"],
                "session_id": session_id,
                "source": result.get("source", "local"),
                "payment": result.get("payment"),
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception:
        logger.exception("WebSocket error")
        manager.disconnect(websocket, session_id)
