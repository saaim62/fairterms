import asyncio
import logging
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.analyzer import analyze_contract_text


def _load_env_file(path: Path) -> None:
    """Load KEY=VALUE from .env without requiring python-dotenv."""
    if not path.is_file():
        return
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


_env_path = Path(__file__).resolve().parent / ".env"
try:
    from dotenv import load_dotenv

    load_dotenv(_env_path)
except ImportError:
    _load_env_file(_env_path)


def _configure_llm_console_logging() -> None:
    """Ensure Groq/LLM INFO logs show in the uvicorn terminal."""
    lg = logging.getLogger("services.groq_analyze")
    lg.setLevel(logging.INFO)
    if lg.handlers:
        return
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(levelname)s [Groq] %(message)s"))
    lg.addHandler(handler)
    lg.propagate = False


_configure_llm_console_logging()


MAX_INPUT_TEXT_CHARS = 120_000


class AnalyzeRequest(BaseModel):
    text: str = Field(..., max_length=MAX_INPUT_TEXT_CHARS)
    source_url: str | None = None


class RiskIssueResponse(BaseModel):
    category: str
    label: str
    severity: Literal["red", "yellow"]
    explanation: str
    confidence: float
    evidence_quote: str


class AnalyzeResponse(BaseModel):
    signal: Literal["red", "yellow", "green"]
    source_url: str | None = None
    issue_count: int
    issues: list[RiskIssueResponse]
    analysis_source: str
    document_language: str | None = None
    rule_locales_used: list[str]
    disclaimer: str


_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("FAIRTERMS_CORS_ORIGINS", "").split(",")
    if o.strip()
]

app = FastAPI(title="FairTerms API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS or ["*"],
    allow_credentials=bool(_ALLOWED_ORIGINS),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    text = (request.text or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="text must not be empty")
    result = await asyncio.to_thread(
        analyze_contract_text, text, request.source_url
    )
    return AnalyzeResponse(**result)
