# FairTerms

FairTerms is a Consumer Contract Guardian that helps people understand risky terms before they agree.

For setup, contributing, and licensing, see the root [README](README.md), [CONTRIBUTING](CONTRIBUTING.md), and [LICENSE](LICENSE).

For a **post-MVP roadmap** toward production-grade completeness (~90–100%), see [ROADMAP.md](ROADMAP.md).

## Monorepo Structure

```text
fairterms/
├── apps/
│   ├── extension/          # Browser extension (Plasmo + React)
│   └── api/                # FastAPI backend
├── packages/
│   ├── shared-types/       # Shared TypeScript types
│   └── ai-engine/          # Python NLP utilities (planned)
├── LICENSE
├── CONTRIBUTING.md
├── docker-compose.yml
└── README.md
```

## 4-Week Delivery Plan

### Week 1 - Foundations and Contracts
- Finalize risk taxonomy and output schema.
- Scaffold API (`/health`, `/analyze`) and AI engine package.
- Add shared TypeScript types for analysis payloads.
- Connect extension popup to API with a mock analysis fallback.

### Week 2 - Extraction and Rule Engine
- Build content extraction from active tab in extension.
- Implement deterministic rule checks for core categories:
  - auto-renewal traps
  - arbitration and class-action waivers
  - broad data rights
  - unilateral term changes
  - cancellation friction
- Return evidence quotes and confidence scores.

### Week 3 - UX and Accuracy
- Add traffic-light status and grouped risk cards in popup.
- Add confidence and plain-language explanations.
- Tune false positives on 30-50 real ToS samples.
- Add basic telemetry and feedback hooks.

### Week 4 - Stabilization and MVP Launch
- Add tests, smoke checks, and error handling hardening.
- Set CORS and deployment config for API.
- Dockerize API and run extension + API locally via compose.
- Prepare demo script and MVP release checklist.

## MVP Scope

- Analyze current page text from browser extension.
- Flag top 5 exploitative contract categories.
- Show a simple Green/Yellow/Red signal.
- Provide evidence quote and explanation for each risk.

## Local Development

### API
- `cd apps/api`
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt`
- `uvicorn main:app --reload --port 8000`

### Extension
- `cd apps/extension`
- `npm install`
- `npm run dev`

### Full stack via Docker
- `docker compose up --build`

