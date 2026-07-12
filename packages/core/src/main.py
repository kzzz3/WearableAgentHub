"""WearableAgent Hub - FastAPI backend entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load .env from project root
_env_path = Path(__file__).resolve().parents[3] / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

from .a2ui.generator import A2UIGenerator
from .config import settings
from .engine.agent_engine import AgentEngine
from .models.message import ChatRequest
from .ws.manager import manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Shared instances
agent_engine: AgentEngine | None = None
a2ui_generator = A2UIGenerator()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    """Application lifespan: startup and shutdown."""
    global agent_engine
    agent_engine = AgentEngine()
    logger.info(
        "WearableAgent Hub started — model=%s, base_url=%s",
        settings.openai_model,
        settings.openai_base_url,
    )
    yield
    logger.info("WearableAgent Hub shutting down")


app = FastAPI(
    title="WearableAgent Hub",
    description="PC wearable device AI Agent simulator",
    version="0.1.0",
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


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "model": settings.openai_model}


class ChatAPIResponse(BaseModel):
    reply: str
    a2ui_messages: list[dict[str, Any]]
    session_id: str


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

    # Process through agent engine
    result = await agent_engine.process(request.message, request.session_id)

    # Generate A2UI messages from structured response
    a2ui_messages = a2ui_generator.generate(result["structured"])

    # Push to WebSocket clients
    await manager.send_a2ui(request.session_id, a2ui_messages)

    return ChatAPIResponse(
        reply=result["reply"],
        a2ui_messages=a2ui_messages,
        session_id=request.session_id,
    )


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    """
    WebSocket endpoint for real-time communication.
    Clients send text messages, server processes through agent and returns A2UI.
    """
    await manager.connect(websocket, session_id)

    # Notify client of successful connection
    await manager.send_event(session_id, "connected", {"session_id": session_id})

    try:
        while True:
            data = await websocket.receive_text()

            if agent_engine is None:
                await manager.send_event(session_id, "error", {"message": "Agent engine not ready"})
                continue

            # Notify client that agent is processing
            await manager.send_event(session_id, "processing", {"status": "thinking"})

            # Process through agent engine
            result = await agent_engine.process(data, session_id)

            # Generate A2UI messages
            a2ui_messages = a2ui_generator.generate(result["structured"])

            # Send A2UI messages to client
            await manager.send_a2ui(session_id, a2ui_messages)

            # Send the raw reply as well
            await manager.send_event(session_id, "reply", {
                "content": result["reply"],
                "session_id": session_id,
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception:
        logger.exception("WebSocket error")
        manager.disconnect(websocket, session_id)