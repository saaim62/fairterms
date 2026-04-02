import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


class AnalyzeRequest(BaseModel):
    text: str
    source_url: str | None = None


app = FastAPI(title="FairTerms API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    return analyze_contract_text(request.text, request.source_url)

