import asyncio
import logging
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

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


def _is_production_env() -> bool:
    return os.environ.get("FAIRTERMS_ENV", "").strip().lower() in ("production", "prod")


def _cors_allowed_origins() -> list[str]:
    """
    Explicit FAIRTERMS_CORS_ORIGINS (comma-separated) always wins.
    In production, an empty env means no wildcard — set origins explicitly
    (e.g. chrome-extension://...). Outside production, unset env defaults to * for local dev.
    """
    raw = os.environ.get("FAIRTERMS_CORS_ORIGINS", "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    if _is_production_env():
        return []
    return ["*"]


_ALLOWED_ORIGINS = _cors_allowed_origins()


def _rate_limit_enabled() -> bool:
    return os.environ.get("FAIRTERMS_RATE_LIMIT_ENABLED", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _analyze_rate_limit() -> str:
    """slowapi limit string; effectively unlimited when rate limiting is disabled."""
    if not _rate_limit_enabled():
        return "1000000000/day"
    limit = os.environ.get("FAIRTERMS_RATE_LIMIT_ANALYZE", "30/minute").strip()
    return limit if limit else "30/minute"


limiter = Limiter(key_func=get_remote_address, default_limits=[])


MAX_INPUT_TEXT_CHARS = 120_000


class AnalyzeRequest(BaseModel):
    text: str = Field(..., max_length=MAX_INPUT_TEXT_CHARS)
    source_url: str | None = None


class RiskIssueResponse(BaseModel):
    category: str
    label: str
    severity: Literal["red", "yellow"]
    explanation: str
    confidence: float = Field(
        ...,
        description=(
            "Relative strength for ranking and display, not a calibrated probability. "
            "Rule hits use fixed tiers; Groq uses the model-reported value when present."
        ),
    )
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


app = FastAPI(title="FairTerms API", version="0.2.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=bool(_ALLOWED_ORIGINS) and _ALLOWED_ORIGINS != ["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit(_analyze_rate_limit)
async def analyze(request: Request, body: AnalyzeRequest) -> AnalyzeResponse:
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="text must not be empty")
    result = await asyncio.to_thread(
        analyze_contract_text, text, body.source_url
    )
    return AnalyzeResponse(**result)
