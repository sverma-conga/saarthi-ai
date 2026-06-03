"""
Recovery Agent — Handles action failures and suggests recovery strategies.

Strategies: retry_with_alternative, scroll_and_retry, navigate_first,
            wait_and_retry, ask_user
"""

import json
import os
import logging

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "recovery.md")

_system_prompt: str | None = None


def _get_system_prompt() -> str:
    global _system_prompt
    if _system_prompt is None:
        with open(PROMPT_PATH, encoding="utf-8") as f:
            _system_prompt = f.read()
    return _system_prompt


MAX_RETRIES = 3


async def recover_from_error(
    error: str,
    failed_action: dict,
    interactive_elements: list[dict],
    page_context: dict,
    retry_count: int,
    client: AsyncOpenAI,
    model: str = "gpt-4o",
) -> dict:
    """Analyze a failure and suggest a recovery strategy.

    Returns:
        {"strategy": str, "action": ActionDetail dict or None,
         "message": str, "reasoning": str}
    """
    if retry_count >= MAX_RETRIES:
        return {
            "strategy": "ask_user",
            "action": None,
            "message": f"I've tried {retry_count} times but couldn't complete this step. Could you help me find the right element?",
            "reasoning": "Max retries exceeded",
        }

    elements_str = json.dumps(interactive_elements, indent=2)

    user_message = f"""## Error
{error}

## Failed Action
{json.dumps(failed_action, indent=2)}

## Retry Count
{retry_count} / {MAX_RETRIES}

## Current Page
- URL: {page_context.get('url', 'unknown')}
- Title: {page_context.get('page_title', 'unknown')}

## Interactive Elements on Screen
{elements_str}

Suggest a recovery strategy."""

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
        logger.warning("Recovery parse error")
        result = {
            "strategy": "wait_and_retry",
            "action": {"type": "wait", "duration_ms": 1000, "description": "Waiting before retry"},
            "message": "Something went wrong. Let me wait and try again.",
            "reasoning": "Parse error fallback",
        }

    logger.info("Recovery: %s → strategy=%s", error[:40], result.get("strategy", "?"))
    return result
