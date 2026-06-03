"""
Executor Agent — Maps a single business step to a concrete UI action.

Takes a planner step + DOM snapshot → returns one action with a real selector.
"""

import json
import os
import logging

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "executor.md")

_system_prompt: str | None = None


def _get_system_prompt() -> str:
    global _system_prompt
    if _system_prompt is None:
        with open(PROMPT_PATH, encoding="utf-8") as f:
            _system_prompt = f.read()
    return _system_prompt


async def execute_step(
    step: str,
    interactive_elements: list[dict],
    page_context: dict,
    client: AsyncOpenAI,
    model: str = "gpt-4o",
) -> dict:
    """Map a business-level step to a concrete UI action.

    Args:
        step: Business-level step description (from planner)
        interactive_elements: DOM elements available on the current page
        page_context: {"url": ..., "page_title": ..., "visible_text_summary": ...}

    Returns:
        {"action": ActionDetail dict, "confidence": float,
         "needs_clarification": bool, "message": str}
    """
    elements_str = json.dumps(interactive_elements, indent=2)

    user_message = f"""## Step to Execute
"{step}"

## Current Page
- URL: {page_context.get('url', 'unknown')}
- Title: {page_context.get('page_title', 'unknown')}
- Visible Content: {page_context.get('visible_text_summary', 'N/A')}

## Interactive Elements on Screen
{elements_str}

Map the step above to exactly ONE action using elements from the list."""

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _get_system_prompt()},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=400,
    )

    try:
        result = json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, IndexError):
        logger.warning("Executor parse error for step: %s", step)
        result = {
            "action": {"type": "wait", "duration_ms": 500, "description": "Parsing error — waiting"},
            "confidence": 0.0,
            "needs_clarification": True,
            "message": "I had trouble mapping this step. Please try again.",
        }

    logger.info(
        "Executor: %s → %s (conf=%.2f)",
        step[:40],
        result.get("action", {}).get("type", "?"),
        result.get("confidence", 0),
    )
    return result
