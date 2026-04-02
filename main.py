#!/usr/bin/env python3
"""
Agent Routing System — Interactive CLI

Flow:
  User input
    └─► Router (claude-haiku-4-5)  ← fast, cheap classifier
          ├─► [complexity >= 7]  → Expensive Agent (claude-opus-4-6 + adaptive thinking)
          ├─► [tool_needed]      → Cheap MCP Agent (claude-haiku-4-5 + web search/fetch)
          └─► [simple]          → Cheap Skills Agent (claude-haiku-4-5 + skill prompts)

Usage:
  python main.py
  python main.py --single "What is the capital of France?"
  ANTHROPIC_API_KEY=sk-... python main.py
"""

from __future__ import annotations

import argparse
import os
import sys

import anthropic

from agent_router.router import classify
from agent_router.dispatcher import dispatch
from agent_router.config import ROUTE_EXPENSIVE, ROUTE_CHEAP_MCP, ROUTE_CHEAP_SKILLS

# ─────────────────────────────────────────────
# ANSI colour helpers
# ─────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
MAGENTA = "\033[95m"
RED = "\033[91m"
DIM = "\033[2m"


def colour(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"{code}{text}{RESET}"


ROUTE_COLOURS = {
    ROUTE_EXPENSIVE: MAGENTA,
    ROUTE_CHEAP_MCP: CYAN,
    ROUTE_CHEAP_SKILLS: GREEN,
}

ROUTE_LABELS = {
    ROUTE_EXPENSIVE: "EXPENSIVE  (claude-opus-4-6 + thinking)",
    ROUTE_CHEAP_MCP: "CHEAP+MCP  (claude-haiku-4-5 + tools)",
    ROUTE_CHEAP_SKILLS: "CHEAP+SKILLS (claude-haiku-4-5)",
}


def print_routing_info(decision) -> None:
    col = ROUTE_COLOURS.get(decision.route, RESET)
    label = ROUTE_LABELS.get(decision.route, decision.route)
    print(colour(f"\n[Router]  complexity={decision.complexity}/10  route={label}", col))
    print(colour(f"          reason: {decision.reason}", DIM))
    if decision.tools:
        print(colour(f"          tools: {', '.join(decision.tools)}", DIM))
    print()


def run_single(message: str, client: anthropic.Anthropic) -> str:
    decision = classify(message, client)
    print_routing_info(decision)
    return dispatch(message, decision, client)


def run_interactive(client: anthropic.Anthropic) -> None:
    print(colour("Agent Routing System", BOLD + CYAN))
    print(colour("Type your message, or 'quit' / 'exit' to leave.\n", DIM))

    conversation_history: list[dict] = []

    while True:
        try:
            raw = input(colour("You: ", BOLD + YELLOW)).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not raw:
            continue
        if raw.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        # ── Classify ───────────────────────────────────────────────────────
        try:
            decision = classify(raw, client)
        except Exception as exc:
            print(colour(f"[Router error] {exc}", RED))
            continue

        print_routing_info(decision)

        # ── Dispatch ───────────────────────────────────────────────────────
        try:
            answer = dispatch(raw, decision, client, conversation_history)
        except Exception as exc:
            print(colour(f"[Agent error] {exc}", RED))
            continue

        print(colour("Agent: ", BOLD + GREEN) + answer)
        print()

        # Store turns for multi-turn context
        conversation_history.append({"role": "user", "content": raw})
        conversation_history.append({"role": "assistant", "content": answer})


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agent Routing System — routes queries to cheap or expensive models."
    )
    parser.add_argument(
        "--single", "-s",
        metavar="MESSAGE",
        help="Run a single query and print the response (non-interactive).",
    )
    parser.add_argument(
        "--api-key", "-k",
        metavar="KEY",
        help="Anthropic API key (defaults to ANTHROPIC_API_KEY env var).",
    )
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(colour("Error: ANTHROPIC_API_KEY is not set.", RED), file=sys.stderr)
        print("  Set it with:  export ANTHROPIC_API_KEY=sk-...", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    if args.single:
        try:
            answer = run_single(args.single, client)
            print(answer)
        except Exception as exc:
            print(colour(f"Error: {exc}", RED), file=sys.stderr)
            sys.exit(1)
    else:
        run_interactive(client)


if __name__ == "__main__":
    main()
