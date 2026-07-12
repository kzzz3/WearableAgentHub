"""WebSocket connection manager for real-time frontend communication."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections from frontend clients."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str = "default") -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info("Client connected: session=%s, total=%d", session_id, len(self.active_connections[session_id]))

    def disconnect(self, websocket: WebSocket, session_id: str = "default") -> None:
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            conns = self.active_connections[session_id]
            if websocket in conns:
                conns.remove(websocket)
            if not conns:
                del self.active_connections[session_id]
        logger.info("Client disconnected: session=%s", session_id)

    async def send_a2ui(self, session_id: str, messages: list[dict[str, Any]]) -> None:
        """Send A2UI message sequence to all clients in a session."""
        if session_id not in self.active_connections:
            return

        payload = json.dumps({
            "channel": "a2ui",
            "messages": messages,
        })

        disconnected: list[WebSocket] = []
        for ws in self.active_connections[session_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws, session_id)

    async def send_event(self, session_id: str, event_type: str, data: dict[str, Any]) -> None:
        """Send a generic event to all clients in a session."""
        if session_id not in self.active_connections:
            return

        payload = json.dumps({
            "channel": "event",
            "type": event_type,
            "data": data,
        })

        for ws in self.active_connections[session_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                pass


manager = ConnectionManager()