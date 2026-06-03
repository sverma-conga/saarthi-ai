"""
Intent Classifier — Determines user request category.

Intents: ACTION, GUIDE, KNOWLEDGE, NAVIGATION, UNKNOWN
"""

import json
import os
import logging

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "intent_classifier.md"
)

_system_prompt: str | None = None


def _get_system_prompt() -> str:
    global _system_prompt
    if _system_prompt is None:
        with open(PROMPT_PATH, encoding="utf-8") as f:
            _system_prompt = f.read()
    return _system_prompt


async def classify_intent(
    user_input: str, client: AsyncOpenAI, model: str = "gpt-4o"
) -> dict:
    """Classify user input into an intent category.

    Returns:
        {"intent": "ACTION|GUIDE|KNOWLEDGE|NAVIGATION|UNKNOWN",
         "confidence": float, "reasoning": str}
    """
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _get_system_prompt()},
            {"role": "user", "content": user_input},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=200,
    )

    try:
        result = json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, IndexError):
        logger.warning("Intent classification failed, defaulting to UNKNOWN")
        result = {"intent": "UNKNOWN", "confidence": 0.0, "reasoning": "Parse error"}

    # Normalize
    result["intent"] = result.get("intent", "UNKNOWN").upper()
    if result["intent"] not in {"ACTION", "GUIDE", "KNOWLEDGE", "NAVIGATION", "UNKNOWN"}:
        result["intent"] = "UNKNOWN"

    logger.info("Intent: %s (%.2f) — %s", result["intent"], result.get("confidence", 0), user_input[:60])
    return result
