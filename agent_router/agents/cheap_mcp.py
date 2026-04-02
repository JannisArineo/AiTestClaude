"""
Cheap MCP Agent — claude-haiku-4-5 with server-side tools (web search, web fetch).

Used when the request needs live external data but doesn't require deep reasoning.
"""

from __future__ import annotations

import anthropic

from ..config import CHEAP_MODEL, CHEAP_MAX_TOKENS
from ..mcp_tools.tools import select_tools

SYSTEM_PROMPT = """You are an efficient AI assistant with access to web search and web fetch tools.
Use tools when you need current or external information.
Be concise and factual in your answers.
"""


def run(
    user_message: str,
    client: anthropic.Anthropic,
    tools_requested: list[str] | None = None,
    conversation_history: list[dict] | None = None,
) -> str:
    """Run the cheap MCP agent and return the final text response.

    Handles the server-side tool loop automatically: if Claude returns
    pause_turn (server tool iteration limit), we re-submit to continue.
    """
    tools = select_tools(tools_requested or [])
    messages = list(conversation_history or [])
    messages.append({"role": "user", "content": user_message})

    max_continuations = 5
    continuations = 0

    while continuations <= max_continuations:
        response = client.messages.create(
            model=CHEAP_MODEL,
            max_tokens=CHEAP_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "pause_turn":
            # Server-side tool loop hit its iteration limit; re-submit to continue
            messages.append({"role": "assistant", "content": response.content})
            continuations += 1
            continue

        # Any other stop reason — just break and return what we have
        break

    for block in response.content:
        if block.type == "text":
            return block.text

    return ""
