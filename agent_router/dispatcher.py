"""
Dispatcher — routes a request to the correct agent based on a RoutingDecision.
"""

from __future__ import annotations

import anthropic

from .router import RoutingDecision
from .config import ROUTE_EXPENSIVE, ROUTE_CHEAP_MCP, ROUTE_CHEAP_SKILLS
from .agents import expensive, cheap_mcp, cheap_skills


def dispatch(
    user_message: str,
    decision: RoutingDecision,
    client: anthropic.Anthropic,
    conversation_history: list[dict] | None = None,
) -> str:
    """Call the correct agent and return its text response."""
    if decision.route == ROUTE_EXPENSIVE:
        return expensive.run(user_message, client, conversation_history)

    if decision.route == ROUTE_CHEAP_MCP:
        return cheap_mcp.run(
            user_message,
            client,
            tools_requested=decision.tools,
            conversation_history=conversation_history,
        )

    # Default: cheap_skills
    return cheap_skills.run(user_message, client, conversation_history=conversation_history)
