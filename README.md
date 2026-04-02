# FairTerms

FairTerms is a **Consumer Contract Guardian** that scans Terms of Service and contract pages before users agree to them.

It identifies risky clauses (auto-renewal traps, arbitration waivers, broad data rights, unilateral term changes, and hard-to-cancel terms), then shows clear traffic-light risk signals with evidence quotes.

## Why FairTerms

Most people do not have time to read long legal agreements. FairTerms helps by:

- extracting visible legal text from the active browser tab,
- analyzing it for high-risk patterns,
- explaining findings in plain language,
- and helping users jump directly to suspicious clauses on the page.

## Current MVP

The current MVP includes:

- **Browser Extension (`apps/extension`)**
  - Plasmo + React popup
  - One-click page analysis
  - Risk cards with severity and evidence snippets
  - "Show on page" highlight and scroll behavior
- **Backend API (`apps/api`)**
  - FastAPI service
  - `GET /health` endpoint
  - `POST /analyze` endpoint for contract text analysis
  - Rule-based clause detection plus optional **Groq** LLM pass (same categories, merged results)
- **Shared Contracts (`packages/shared-types`)**
  - TypeScript types used across extension and backend integration
- **AI Engine Placeholder (`packages/ai-engine`)**
  - planned package for stronger NLP/LLM-based analysis

## Monorepo Structure

```text
fairterms/
├── apps/
│   ├── extension/          # Browser extension (Plasmo + React)
│   └── api/                # FastAPI backend
├── packages/
│   ├── shared-types/       # Shared TypeScript types
│   └── ai-engine/          # Python NLP utilities (planned)
├── docker-compose.yml
├── Plan.md
└── README.md
```

## Detection Categories (MVP)

The analyzer currently checks for:

1. **Auto-Renewal Trap** (red)
2. **Forced Arbitration / Class Waiver** (red)
3. **Broad Data Rights** (yellow)
4. **Unilateral Term Changes** (yellow)
5. **Hard-to-Cancel Terms** (yellow)

## Tech Stack

- **Extension:** Plasmo, React, TypeScript
- **Backend:** FastAPI, Python
- **Shared Types:** TypeScript interfaces
- **Containerization:** Docker + Docker Compose

## Local Setup

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

Verify:

- Health: `http://127.0.0.1:8000/health`

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

### 3) Production build (extension)

```bash
cd apps/extension
npm run build
```

Load unpacked from:

- `apps/extension/build/chrome-mv3-prod`

## API Contract

### `GET /health`

Returns service status.

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

Response shape (from `packages/shared-types`):

```ts
interface AnalyzeResponse {
  signal: "red" | "yellow" | "green"
  source_url?: string | null
  issue_count: number
  analysis_source?: "rules" | "rules+groq"
  issues: {
    category: string
    label: string
    severity: "red" | "yellow"
    explanation: string
    confidence: number
    evidence_quote: string
  }[]
  disclaimer: string
}
```

## Docker

Run API via Docker Compose:

```bash
docker compose up --build
```

API will be available on `http://localhost:8000`.

## Notes

- FairTerms provides informational risk signals and is **not legal advice**.
- Current analysis is deterministic/rule-based; AI-assisted classification is planned in `packages/ai-engine`.

## Roadmap (Next)

- Improve clause localization and highlighting precision
- Add confidence calibration + evaluation dataset
- Add safe-clause positives and explainability scoring
- Add tests and CI checks for analyzer quality
- Expand to full LLM-assisted risk reasoning
