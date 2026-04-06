# FairTerms

FairTerms is a **Consumer Contract Guardian** that scans Terms of Service and contract pages before users agree to them.

It identifies risky clauses (for example auto-renewal traps, arbitration waivers, broad data rights, unilateral changes, and cancellation friction), then shows clear traffic-light risk signals with evidence quotes.

## Why FairTerms

Most people do not have time to read long legal agreements. FairTerms helps by:

- extracting visible legal text from the active browser tab,
- analyzing it for high-risk patterns,
- explaining findings in plain language,
- and helping users jump directly to suspicious clauses on the page.

## Current MVP

The current MVP includes:

- **Browser Extension (`apps/extension`)** — Plasmo + React popup, one-click analysis, risk cards with severity and evidence snippets, “Show on page” highlight and scroll behavior.
- **Backend API (`apps/api`)** — FastAPI service with `GET /health` and `POST /analyze`; rule-based clause detection plus optional **Groq** LLM pass (merged results).
- **Shared contracts (`packages/shared-types`)** — TypeScript types shared with the extension.
- **AI engine placeholder (`packages/ai-engine`)** — planned package for stronger NLP and evaluation.

## Monorepo structure

```text
fairterms/
├── apps/
│   ├── extension/          # Plasmo + React MV3 extension
│   └── api/                # FastAPI backend
├── packages/
│   ├── shared-types/       # Shared TypeScript types
│   └── ai-engine/          # Python utilities (planned)
├── LICENSE                 # MIT
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── CHANGELOG.md
├── docker-compose.yml
├── Plan.md
└── README.md
```

## Detection categories

The analyzer uses a fixed taxonomy of clause categories (red and yellow severities). The canonical list with labels and explanations is in [`apps/api/services/category_registry.py`](apps/api/services/category_registry.py). The README’s older “five categories” summary is illustrative only; the implementation covers many more consumer-risk patterns.

## Tech stack

- **Extension:** Plasmo, React, TypeScript
- **Backend:** FastAPI, Python 3.10+
- **Shared types:** TypeScript interfaces in `packages/shared-types`
- **Containerization:** Docker Compose (API development)

## Local setup

### Prerequisites

- Node.js 18+
- npm or pnpm
- Python 3.10+
- pip
- (Optional) Docker Desktop

### 1) Run backend API

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Verify: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

More detail: [`apps/api/README.md`](apps/api/README.md).

#### Optional: Groq (improved analysis)

1. Copy `apps/api/.env.example` to `apps/api/.env`.
2. Set `GROQ_API_KEY` from [Groq Console](https://console.groq.com/) (never commit `.env`).
3. Restart the API. Responses include `analysis_source`: `"rules"` or `"rules+groq"`.

Groq calls log to the API terminal with the `[Groq]` prefix (request size, token usage, raw preview, parse errors, accepted issue counts). Set `FAIRTERMS_LOG_LLM_FULL=1` in `.env` to print the full JSON body.

Rule hits take precedence per category; Groq adds **additional** categories the regex engine missed. If Groq is unavailable, the API falls back to rules only.

### 2) Run extension

```bash
cd apps/extension
npm install
npm run dev
```

In Chrome:

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select: `apps/extension/build/chrome-mv3-dev`

See [`apps/extension/README.md`](apps/extension/README.md) for build paths and permissions.

### 3) Production build (extension)

```bash
cd apps/extension
npm run build
```

Load unpacked from `apps/extension/build/chrome-mv3-prod`.

## API contract

### `GET /health`

```json
{ "status": "ok" }
```

### `POST /analyze`

Request:

```json
{
  "text": "terms content here...",
  "source_url": "https://example.com/terms"
}
```

Response shape (see [`packages/shared-types/index.ts`](packages/shared-types/index.ts)):

```ts
interface AnalyzeResponse {
  signal: "red" | "yellow" | "green"
  source_url?: string | null
  issue_count: number
  analysis_source: string
  issues: RiskIssue[]
  document_language?: string | null
  rule_locales_used: string[]
  disclaimer: string
}
```

`text` is capped server-side (see `MAX_INPUT_TEXT_CHARS` in `apps/api/main.py`). The extension truncates client-side to its own limit before sending.

## Docker

```bash
docker compose up --build
```

API defaults to `http://localhost:8000`.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) (setup, tests, pull requests) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

Report security issues privately as described in [SECURITY.md](SECURITY.md).

## License

FairTerms is open source under the [MIT License](LICENSE).

## Disclaimer

FairTerms provides informational risk signals and is **not legal advice**.

## Roadmap (indicative)

- Improve clause localization and highlighting precision
- Confidence calibration and evaluation datasets
- CI checks for analyzer quality
- Expanded LLM-assisted reasoning where it improves grounded results

See also [CHANGELOG.md](CHANGELOG.md).
