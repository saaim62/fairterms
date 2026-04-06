# FairTerms API

FastAPI service that analyzes contract and Terms of Service text using deterministic rules (with optional multilingual pattern banks) and an optional **Groq** LLM pass.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# For tests: pip install -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

- `GET /health` — liveness
- `POST /analyze` — JSON body `{ "text": string, "source_url": string | null }`

See the [root README](../../README.md) for environment variables, Docker, and the full API contract.

## Key modules

| Module | Purpose |
|--------|---------|
| `main.py` | FastAPI app, CORS, body size limits, per-IP rate limit on `/analyze` |
| `services/analyzer_rules.py` | Declarative regex rules (compiled at import) |
| `services/analyzer.py` | Matching, locales, Groq merge, evidence snippets |
| `services/category_registry.py` | Clause categories, labels, severities |
| `services/groq_analyze.py` | Optional OpenAI-compatible Groq client |
| `services/locale_patterns.py` | Extra regex banks per locale |

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## License

[MIT](../../LICENSE)
