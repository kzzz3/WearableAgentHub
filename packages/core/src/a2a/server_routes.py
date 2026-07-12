"""A2A route mounting utilities for FastAPI integration."""

from __future__ import annotations

import logging

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI

from .executor import WearableAgentExecutor, build_agent_card

logger = logging.getLogger(__name__)


def mount_a2a_routes(app: FastAPI, executor: WearableAgentExecutor) -> None:
    """Mount A2A protocol routes onto the FastAPI application.

    This adds:
      - /.well-known/agent-card.json  (Agent Card discovery)
      - /a2a  (JSON-RPC endpoint for message/send)
    """
    agent_card = build_agent_card()
    task_store = InMemoryTaskStore()

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
        agent_card=agent_card,
    )

    card_routes = create_agent_card_routes(agent_card)
    jsonrpc_routes = create_jsonrpc_routes(request_handler, rpc_url="/a2a")

    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=card_routes,
        jsonrpc_routes=jsonrpc_routes,
    )

    logger.info("A2A routes mounted: /.well-known/agent-card.json + /a2a")
