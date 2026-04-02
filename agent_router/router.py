"""
Router Agent — uses claude-haiku-4-5 to classify incoming requests.

Returns a RoutingDecision that the dispatcher uses to pick the right agent.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import anthropic

from .config import (
    ROUTER_MODEL,
    ROUTER_MAX_TOKENS,
    EXPENSIVE_THRESHOLD,
    ROUTE_EXPENSIVE,
    ROUTE_CHEAP_MCP,
    ROUTE_CHEAP_SKILLS,
)

ROUTER_SYSTEM_PROMPT = """You are a routing agent. Your only job is to analyse a user request
and decide which processing pipeline it should go to. Respond ONLY with valid JSON — no prose.

Pipelines available:
- "expensive"     : Complex reasoning, nuanced analysis, creative writing, multi-step code
                    generation / review, research synthesis. Use when depth matters.
- "cheap_mcp"     : Tasks that require live external data or tools: web search, URL fetching,
                    file system operations, weather, news, APIs.
- "cheap_skills"  : Simple, self-contained tasks: quick Q&A, reformatting, translation,
                    summarising a text already provided, templating.

JSON schema you MUST follow exactly:
{
  "route":       "<expensive|cheap_mcp|cheap_skills>",
  "complexity":  <integer 1-10>,
  "tool_needed": <true|false>,
  "tools":       ["<tool name>", ...],   // empty list if tool_needed is false
  "reason":      "<one sentence>"
}

Rules:
- complexity >= 7  → always route "expensive"
- tool_needed true → route "cheap_mcp" (unless complexity >= 7, then still "expensive")
- otherwise        → route "cheap_skills"
- Be conservative: when in doubt, prefer "expensive" over wrong cheap routing.
"""


@dataclass
class RoutingDecision:
    route: str
    complexity: int
    tool_needed: bool
    tools: list[str]
    reason: str
    raw_json: dict


def classify(user_message: str, client: anthropic.Anthropic) -> RoutingDecision:
    """Ask the router model to classify a user request."""
    response = client.messages.create(
        model=ROUTER_MODEL,
        max_tokens=ROUTER_MAX_TOKENS,
        system=ROUTER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text.strip()

    # Strip markdown code fences if present
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Router returned invalid JSON:\n{raw_text}") from exc

    # Enforce threshold rule regardless of what the model said
    route = data.get("route", ROUTE_CHEAP_SKILLS)
    complexity = int(data.get("complexity", 5))
    tool_needed = bool(data.get("tool_needed", False))

    if complexity >= EXPENSIVE_THRESHOLD:
        route = ROUTE_EXPENSIVE
    elif tool_needed and route != ROUTE_EXPENSIVE:
        route = ROUTE_CHEAP_MCP
    elif route not in (ROUTE_EXPENSIVE, ROUTE_CHEAP_MCP, ROUTE_CHEAP_SKILLS):
        route = ROUTE_CHEAP_SKILLS

    return RoutingDecision(
        route=route,
        complexity=complexity,
        tool_needed=tool_needed,
        tools=data.get("tools", []),
        reason=data.get("reason", ""),
        raw_json=data,
    )
