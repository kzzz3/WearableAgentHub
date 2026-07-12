"""A2A protocol integration for WearableAgent Hub."""

from .client_wrapper import A2AClientWrapper
from .executor import WearableAgentExecutor, build_agent_card
from .server_routes import mount_a2a_routes

__all__ = [
    "A2AClientWrapper",
    "WearableAgentExecutor",
    "build_agent_card",
    "mount_a2a_routes",
]
