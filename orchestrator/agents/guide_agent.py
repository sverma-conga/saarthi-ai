"""
Guide Agent — Generates step-by-step instructions for the user to follow manually.
"""

import json
import os
import logging

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "guide.md")

_prompt_template: str | None = None


def _get_prompt_template() -> str:
    global _prompt_template
    if _prompt_template is None:
        with open(PROMPT_PATH, encoding="utf-8") as f:
            _prompt_template = f.read()
    return _prompt_template


async def generate_guide(
    user_input: str,
    interactive_elements: list[dict],
    page_context: dict,
    rag_context: str,
    client: AsyncOpenAI,
    model: str = "gpt-4o",
) -> dict:
    """Generate a step-by-step guide for the user.

    Returns:
        {"message": str, "guide_steps": list[dict], "done": bool}
    """
    system_prompt = _get_prompt_template().replace(
        "{rag_context}", rag_context or "No additional context available."
    )

    elements_str = json.dumps(interactive_elements, indent=2)

    user_message = f"""## User Request
"{user_input}"

## Current Page
- URL: {page_context.get('url', 'unknown')}
- Title: {page_context.get('page_title', 'unknown')}
- Visible Content: {page_context.get('visible_text_summary', 'N/A')}

## Interactive Elements on Screen
{elements_str}

Generate step-by-step instructions using the elements above."""

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=800,
    )

    try:
        result = json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, IndexError):
        logger.warning("Guide parse error")
        result = {
            "message": "I couldn't generate a guide for this request. Please try rephrasing.",
            "guide_steps": [],
            "done": True,
        }

    logger.info("Guide: %d steps for '%s'", len(result.get("guide_steps", [])), user_input[:40])
    return result
