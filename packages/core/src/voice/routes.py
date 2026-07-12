"""Voice WebSocket routes for real-time voice interaction with wearable agents.

Exposes /voice/{session_id} WebSocket endpoint that accepts:
- JSON text messages: {"type": "text", "content": "..."}
- Binary audio frames: raw PCM16 audio (future: forward to STT service)

Returns:
- {"type": "transcript", "content": "..."} — what the user said
- {"type": "reply", "content": "...", "source": "local"|"a2a"} — agent response
- {"type": "a2ui", "messages": [...]} — A2UI render messages
- {"type": "payment", "receipt": {...}} — payment receipt if applicable
- {"type": "status", "state": "listening"|"thinking"|"speaking"} — state updates
- {"type": "error", "message": "..."} — error
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice"])


@router.websocket("/voice/{session_id}")
async def voice_session(websocket: WebSocket, session_id: str) -> None:
    """WebSocket endpoint for voice interaction.

    Accepts text messages and audio frames, processes through agent engine,
    returns structured responses for TTS and HUD display.
    """
    from ..main import agent_engine, a2ui_generator
    from ..ws.manager import manager

    await websocket.accept()
    logger.info("Voice session opened: %s", session_id)

    try:
        # Send initial status
        await websocket.send_text(json.dumps({
            "type": "status",
            "state": "listening",
        }))

        while True:
            data = await websocket.receive()

            if "text" in data:
                try:
                    msg = json.loads(data["text"])
                except json.JSONDecodeError:
                    # Treat raw text as voice transcript
                    msg = {"type": "text", "content": data["text"]}

                msg_type = msg.get("type", "text")

                if msg_type == "text":
                    content = msg.get("content", "")
                    if not content.strip():
                        continue

                    # Echo transcript back
                    await websocket.send_text(json.dumps({
                        "type": "transcript",
                        "content": content,
                    }))

                    # Signal thinking state
                    await websocket.send_text(json.dumps({
                        "type": "status",
                        "state": "thinking",
                    }))

                    if agent_engine is None:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Agent engine not ready",
                        }))
                        continue

                    # Process through agent engine
                    result = await agent_engine.process(content, session_id)

                    # Generate A2UI messages
                    a2ui_messages = a2ui_generator.generate(result["structured"])

                    # Send A2UI
                    await websocket.send_text(json.dumps({
                        "type": "a2ui",
                        "messages": a2ui_messages,
                    }))

                    # Send reply
                    await websocket.send_text(json.dumps({
                        "type": "reply",
                        "content": result["reply"],
                        "source": result.get("source", "local"),
                    }))

                    # Send payment info if present
                    if result.get("payment"):
                        await websocket.send_text(json.dumps({
                            "type": "payment",
                            "receipt": result["payment"],
                        }))

                    # Also broadcast to main WS session for glasses-sim sync
                    await manager.send_a2ui(session_id, a2ui_messages)
                    await manager.send_event(session_id, "reply", {
                        "content": result["reply"],
                        "session_id": session_id,
                        "source": result.get("source", "local"),
                        "payment": result.get("payment"),
                    })

                    # Return to listening state
                    await websocket.send_text(json.dumps({
                        "type": "status",
                        "state": "listening",
                    }))

                elif msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

            elif "bytes" in data:
                # Audio frame received — in a real setup, forward to STT
                # For now, acknowledge receipt
                logger.debug("Audio frame received: %d bytes", len(data["bytes"]))

    except WebSocketDisconnect:
        logger.info("Voice session closed: %s", session_id)
    except Exception:
        logger.exception("Voice session error: %s", session_id)