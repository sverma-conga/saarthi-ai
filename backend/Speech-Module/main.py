import logging

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from config import Settings, get_settings
from schemas import TranscriptResponse, AIResponse, PipelineResponse
from services.speech_to_text import transcribe_audio
from services.ai_service import get_ai_response
from services.text_to_speech import synthesize_speech

logger = logging.getLogger(__name__)

app = FastAPI(title="Speech Module", version="1.0.0")

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".webm", ".ogg", ".flac"}


@app.post("/speech-to-text", response_model=TranscriptResponse)
async def speech_to_text(
    file: UploadFile = File(...),
):
    """Accept an audio file and return the transcript (Google free STT)."""
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        transcript = await transcribe_audio(audio_bytes, file.filename)
    except Exception as e:
        logger.exception("Speech-to-text error")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    return TranscriptResponse(transcript=transcript)


@app.post("/text-to-speech")
async def text_to_speech(text: str):
    """Accept text and return synthesized speech audio (Google free gTTS)."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty")

    try:
        audio_bytes = await synthesize_speech(text)
    except Exception as e:
        logger.exception("Text-to-speech error")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")

    return StreamingResponse(
        BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=response.mp3"},
    )


@app.post("/pipeline", response_model=PipelineResponse)
async def full_pipeline(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    """
    Full pipeline:
      1. Speech-to-Text (Google free)  →  transcript
      2. Transcript → AI (OpenAI)     →  AI response
      3. AI response → Text-to-Speech (gTTS free)  →  audio
    """
    # Step 1: Speech-to-Text
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    transcript = await transcribe_audio(audio_bytes, file.filename)

    # Step 2: AI Response
    ai_response = await get_ai_response(transcript, settings)

    # Step 3: Text-to-Speech
    tts_audio = await synthesize_speech(ai_response)
    output_path = "response.mp3"
    with open(output_path, "wb") as f:
        f.write(tts_audio)

    return PipelineResponse(
        transcript=transcript,
        ai_response=ai_response,
        audio_url=f"/{output_path}",
    )


@app.post("/pipeline/stream")
async def pipeline_stream(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    """
    Full pipeline that streams the TTS audio directly back as the response.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    transcript = await transcribe_audio(audio_bytes, file.filename)
    ai_response = await get_ai_response(transcript, settings)
    tts_audio = await synthesize_speech(ai_response)

    return StreamingResponse(
        BytesIO(tts_audio),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "attachment; filename=response.mp3",
            "X-Transcript": transcript,
            "X-AI-Response": ai_response[:500],
        },
    )
