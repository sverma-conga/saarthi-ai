from pydantic import BaseModel


class TranscriptResponse(BaseModel):
    transcript: str


class AIResponse(BaseModel):
    transcript: str
    ai_response: str


class PipelineResponse(BaseModel):
    transcript: str
    ai_response: str
    audio_url: str
