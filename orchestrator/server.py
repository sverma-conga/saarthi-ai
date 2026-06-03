"""
SAARTHI AI — Orchestrator Server

FastAPI entry point for the agentic orchestrator.
Listens on port 8001, accepts POST /api/process.

Usage:
    cd orchestrator
    python -m uvicorn server:app --port 8001 --reload
"""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from config import get_settings
from schemas.request import OrchestratorRequest
from schemas.response import OrchestratorResponse
from agent import process_request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-5s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SAARTHI AI Orchestrator",
    version="1.0.0",
    description="Agentic orchestrator for Conga CLM voice assistant",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
    return _client


@app.post("/api/process", response_model=OrchestratorResponse)
async def api_process(request: OrchestratorRequest):
    """Main endpoint — receives user intent + DOM context, returns next action."""
    try:
        settings = get_settings()
        client = get_openai_client()
        result = await process_request(request, client, settings.openai_model)
        return result
    except Exception as e:
        logger.exception("Error processing request")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "saarthi-orchestrator"}


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("server:app", host=settings.host, port=settings.port, reload=True)
