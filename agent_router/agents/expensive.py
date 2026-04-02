"""
Expensive Agent — claude-opus-4-6 with adaptive thinking.

Used for complex reasoning, creative work, deep code analysis, etc.
"""

from __future__ import annotations

import anthropic

from ..config import EXPENSIVE_MODEL, EXPENSIVE_MAX_TOKENS

SYSTEM_PROMPT = """You are a highly capable AI assistant with deep reasoning abilities.
Take your time to think through problems carefully and provide thorough, accurate answers.
"""


def run(
    user_message: str,
    client: anthropic.Anthropic,
    conversation_history: list[dict] | None = None,
) -> str:
    """Run the expensive agent and return the final text response."""
    messages = list(conversation_history or [])
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=EXPENSIVE_MODEL,
        max_tokens=EXPENSIVE_MAX_TOKENS,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    # Extract the text block (thinking blocks come first, skip them)
    for block in response.content:
        if block.type == "text":
            return block.text

    return ""
