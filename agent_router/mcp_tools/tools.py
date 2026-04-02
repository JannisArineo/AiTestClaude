"""
MCP / Server-side tool definitions used by the cheap_mcp agent.

These are Anthropic-hosted server-side tools — no client-side execution required.
Claude calls them directly; results are returned in the response stream.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Server-side tool definitions (passed directly to the Messages API)
# ─────────────────────────────────────────────────────────────────────────────

WEB_SEARCH = {
    "type": "web_search_20260209",
    "name": "web_search",
}

WEB_FETCH = {
    "type": "web_fetch_20260209",
    "name": "web_fetch",
}

# All tools available to the cheap_mcp agent
ALL_TOOLS = [WEB_SEARCH, WEB_FETCH]

# Mapping from friendly name → tool definition (for selective loading)
TOOL_MAP: dict[str, dict] = {
    "web_search": WEB_SEARCH,
    "web_fetch": WEB_FETCH,
}


def select_tools(requested: list[str]) -> list[dict]:
    """Return tool definitions for the requested tool names.

    Falls back to ALL_TOOLS when the requested list is empty or contains
    names that aren't in TOOL_MAP.
    """
    if not requested:
        return ALL_TOOLS

    selected = [TOOL_MAP[name] for name in requested if name in TOOL_MAP]
    return selected if selected else ALL_TOOLS
