"""
Planner Agent — Breaks user goal into business-level workflow steps.

The planner works at the BUSINESS level — no selectors, no DOM details.
"""

import json
import os
import logging

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "planner.md")

_prompt_template: str | None = None


def _get_prompt_template() -> str:
    global _prompt_template
    if _prompt_template is None:
        with open(PROMPT_PATH, encoding="utf-8") as f:
            _prompt_template = f.read()
    return _prompt_template


async def plan_task(
    user_input: str,
    rag_context: str,
    client: AsyncOpenAI,
    model: str = "gpt-4o",
) -> dict:
    """Generate a business-level execution plan for the user's goal.

    Returns:
        {"goal": str, "steps": list[str], "reasoning": str}
    """
    system_prompt = _get_prompt_template().replace("{rag_context}", rag_context or "No additional context available.")

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=600,
    )

    try:
        result = json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, IndexError):
        logger.warning("Planner parse error, returning single-step plan")
        result = {
            "goal": user_input,
            "steps": [user_input],
            "reasoning": "Could not generate detailed plan",
        }

    logger.info("Plan: %s → %d steps", result.get("goal", "?"), len(result.get("steps", [])))
    return result
