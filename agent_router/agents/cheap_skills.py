"""
Cheap Skills Agent — claude-haiku-4-5 with skill-based system prompts.

Used for simple, self-contained tasks: Q&A, formatting, translation,
summarisation, templating, etc.
"""

from __future__ import annotations

import anthropic

from ..config import CHEAP_MODEL, CHEAP_MAX_TOKENS

# Skill prompt library — each skill focuses Claude on a specific task type
SKILL_PROMPTS: dict[str, str] = {
    "default": (
        "You are a concise, helpful AI assistant. "
        "Answer directly and keep responses short unless detail is requested."
    ),
    "summarize": (
        "You are a summarisation expert. "
        "Condense the provided text into clear, accurate bullet points or a short paragraph. "
        "Preserve key facts and omit filler."
    ),
    "translate": (
        "You are a professional translator. "
        "Translate the given text accurately, preserving tone and meaning."
    ),
    "reformat": (
        "You are a text-formatting assistant. "
        "Reformat the input as requested (markdown, JSON, bullet points, table, etc.) "
        "without changing the content."
    ),
    "qa": (
        "You are a knowledgeable assistant. "
        "Answer the question concisely and accurately based on your training knowledge."
    ),
    "template": (
        "You are a template-filling assistant. "
        "Fill in the provided template with appropriate, contextually correct content."
    ),
}


def _pick_skill(user_message: str) -> str:
    """Simple heuristic to pick a skill prompt from the message content."""
    lower = user_message.lower()
    if any(w in lower for w in ("summarize", "summarise", "tldr", "summary")):
        return "summarize"
    if any(w in lower for w in ("translate", "translation", "auf deutsch", "en français")):
        return "translate"
    if any(w in lower for w in ("reformat", "convert to", "as json", "as markdown", "as table")):
        return "reformat"
    if any(w in lower for w in ("template", "fill in", "placeholder")):
        return "template"
    return "qa"


def run(
    user_message: str,
    client: anthropic.Anthropic,
    skill: str | None = None,
    conversation_history: list[dict] | None = None,
) -> str:
    """Run the cheap skills agent and return the final text response."""
    chosen_skill = skill or _pick_skill(user_message)
    system_prompt = SKILL_PROMPTS.get(chosen_skill, SKILL_PROMPTS["default"])

    messages = list(conversation_history or [])
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=CHEAP_MODEL,
        max_tokens=CHEAP_MAX_TOKENS,
        system=system_prompt,
        messages=messages,
    )

    for block in response.content:
        if block.type == "text":
            return block.text

    return ""
