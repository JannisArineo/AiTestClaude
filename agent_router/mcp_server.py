#!/usr/bin/env python3
"""
MCP Server — exposes the Agent Routing System as a tool for Claude Desktop.

Protocol: JSON-RPC 2.0 over stdio (MCP spec).

Tool exposed:
  route_query(message: str) → str
    Classifies the message with the router and dispatches it to the
    correct agent. Returns the agent's text response.

Usage (Claude Desktop):
  Add this server to ~/Library/Application Support/Claude/claude_desktop_config.json
  See /claude_desktop_config.json for the exact snippet.
"""

from __future__ import annotations

import json
import os
import sys

import anthropic

# Allow running as a script directly from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_router.router import classify
from agent_router.dispatcher import dispatch

# ─────────────────────────────────────────────
# MCP protocol helpers
# ─────────────────────────────────────────────

def _send(obj: dict) -> None:
    """Write a JSON-RPC message to stdout."""
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _error(req_id, code: int, message: str) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def _result(req_id, result) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "result": result})


# ─────────────────────────────────────────────
# Tool manifest
# ─────────────────────────────────────────────

TOOLS = [
    {
        "name": "route_query",
        "description": (
            "Send a message through the Agent Routing System. "
            "The router (Haiku) automatically classifies the request and dispatches it to: "
            "• claude-opus-4-6 with adaptive thinking (complex tasks), "
            "• claude-haiku-4-5 + web search/fetch (tasks needing live data), "
            "• claude-haiku-4-5 + skill prompts (simple Q&A, formatting, translation). "
            "Returns the agent's response as a string."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The user message to route and answer.",
                }
            },
            "required": ["message"],
        },
    }
]

# ─────────────────────────────────────────────
# Request handlers
# ─────────────────────────────────────────────

def handle_initialize(req_id, _params) -> None:
    _result(req_id, {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "agent-router", "version": "1.0.0"},
    })


def handle_tools_list(req_id, _params) -> None:
    _result(req_id, {"tools": TOOLS})


def handle_tools_call(req_id, params: dict, client: anthropic.Anthropic) -> None:
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name != "route_query":
        _error(req_id, -32601, f"Unknown tool: {tool_name}")
        return

    message = arguments.get("message", "").strip()
    if not message:
        _error(req_id, -32602, "Parameter 'message' must not be empty.")
        return

    try:
        decision = classify(message, client)
        answer = dispatch(message, decision, client)
        route_info = (
            f"[Routed to: {decision.route} | "
            f"complexity={decision.complexity}/10 | "
            f"reason: {decision.reason}]\n\n"
        )
        full_response = route_info + answer
    except Exception as exc:
        _error(req_id, -32603, f"Agent error: {exc}")
        return

    _result(req_id, {
        "content": [{"type": "text", "text": full_response}],
        "isError": False,
    })


# ─────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────

def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        sys.stderr.write("ANTHROPIC_API_KEY is not set.\n")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            _send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            handle_initialize(req_id, params)
        elif method == "tools/list":
            handle_tools_list(req_id, params)
        elif method == "tools/call":
            handle_tools_call(req_id, params, client)
        elif method == "notifications/initialized":
            pass  # No response needed for notifications
        else:
            _error(req_id, -32601, f"Method not found: {method}")


if __name__ == "__main__":
    main()
