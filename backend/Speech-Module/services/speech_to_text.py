import asyncio
import io

import speech_recognition as sr
from pydub import AudioSegment


async def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    """Convert audio bytes to text using Google's free Speech Recognition API."""
    return await asyncio.to_thread(_transcribe_sync, audio_bytes, filename)


def _transcribe_sync(audio_bytes: bytes, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"
    audio_stream = io.BytesIO(audio_bytes)

    # Convert any format to WAV using pydub
    audio_segment = AudioSegment.from_file(audio_stream, format=ext)
    wav_buffer = io.BytesIO()
    audio_segment.export(wav_buffer, format="wav")
    wav_buffer.seek(0)

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_buffer) as source:
        audio_data = recognizer.record(source)

    return recognizer.recognize_google(audio_data)
