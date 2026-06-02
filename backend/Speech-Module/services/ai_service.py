import openai
from config import Settings


async def get_ai_response(transcript: str, settings: Settings) -> str:
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Respond concisely."},
            {"role": "user", "content": transcript},
        ],
    )
    return response.choices[0].message.content
