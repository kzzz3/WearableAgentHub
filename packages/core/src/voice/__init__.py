"""Voice session management for wearable devices.

Provides a WebSocket-based voice interaction endpoint.
Since OpenAI Realtime API requires a browser-side WebRTC connection,
this module acts as a relay/session-manager that:
1. Manages voice session state
2. Transcribes text from voice input (or accepts text directly)
3. Routes through AgentEngine for processing
4. Returns text + A2UI for TTS/display on the client side
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)