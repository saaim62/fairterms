# Contributing to FairTerms

Thank you for your interest in FairTerms. This document explains how to set up the project, run checks, and submit changes.

## Code of conduct

Be respectful and constructive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Reporting issues

- Use GitHub Issues for bugs, feature ideas, and questions about development.
- For **security vulnerabilities**, do **not** open a public issue. See [SECURITY.md](SECURITY.md).

## Development setup

### Prerequisites

- Node.js 18+
- Python 3.10+
- npm (or pnpm)

### Backend API (`apps/api`)

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

- Health check: `GET http://127.0.0.1:8000/health`
- Optional Groq: copy `.env.example` to `.env` and set `GROQ_API_KEY` (never commit secrets).

Run tests:

```bash
cd apps/api
pytest
```

`conftest.py` sets `FAIRTERMS_RATE_LIMIT_ENABLED=0` by default so the suite does not hit `/analyze` rate limits. To exercise limits locally, unset that variable or set it to `1` and tune `FAIRTERMS_RATE_LIMIT_ANALYZE` (see `.env.example`).

### Browser extension (`apps/extension`)

```bash
cd apps/extension
npm install
npm run dev
```

Load the dev build from `apps/extension/build/chrome-mv3-dev` in `chrome://extensions` (Developer mode → Load unpacked).

### Docker

From the repository root:

```bash
docker compose up --build
```

## Project layout

| Path | Role |
|------|------|
| `apps/extension` | Plasmo + React MV3 extension |
| `apps/api` | FastAPI analysis service |
| `packages/shared-types` | Shared TypeScript types for API payloads |
| `packages/ai-engine` | Placeholder for future NLP utilities |

Clause categories and severities are defined in `apps/api/services/category_registry.py`. The rule engine lives in `apps/api/services/analyzer.py`.

## Pull requests

1. **Branch** from `main` (or the default branch) with a descriptive name.
2. **Describe** what changed and why in the PR body.
3. **Test** your change: run `pytest` in `apps/api`; for UI work, smoke-test the extension build.
4. **Keep scope focused**—one logical change per PR when possible.

## Style

- **Python:** Match existing formatting; prefer clear names over clever shortcuts.
- **TypeScript/React:** Match existing component patterns and `theme` usage in the extension.
- **Commits:** Clear messages in the imperative (“Add rate limit env”, not “Added”).

## License

By contributing, you agree that your contributions are licensed under the same terms as the project ([LICENSE](LICENSE)).
