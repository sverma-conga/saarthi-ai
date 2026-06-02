import asyncio
import io

from gtts import gTTS


async def synthesize_speech(text: str, lang: str = "en") -> bytes:
    """Convert text to speech audio (MP3) using Google's free gTTS."""
    return await asyncio.to_thread(_synthesize_sync, text, lang)


def _synthesize_sync(text: str, lang: str) -> bytes:
    tts = gTTS(text=text, lang=lang)
    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)
    return buffer.read()
