# Changelog

All notable changes to FairTerms are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
where versioning applies.

## [Unreleased]

### Added

- Open-source documentation: `LICENSE` (MIT), `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md`, and this changelog.
- `ROADMAP.md`: phased plan toward ~90–100% production readiness.
- Per-IP rate limiting on `POST /analyze` (`slowapi`; configurable via `FAIRTERMS_RATE_LIMIT_*`).
- Stricter CORS in production: with `FAIRTERMS_ENV=production`, an unset `FAIRTERMS_CORS_ORIGINS` no longer falls back to `*` (set explicit origins, e.g. `chrome-extension://…`).
- `services/analyzer_rules.py` holding regex rule definitions; `analyzer.py` focuses on orchestration.

### Changed

- Documented that `confidence` on issues is a heuristic / model value for ranking, not a calibrated probability (API schema, `shared-types`, code comment).
