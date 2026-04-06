# Security policy

## Supported versions

Security updates are applied to the default development branch (`main` or equivalent). There are no separate long-term release branches for the current MVP.

## Reporting a vulnerability

Please **do not** disclose security issues in public GitHub issues.

Instead, report details privately to the maintainers (use repository contact options if available, or open a draft security advisory if GitHub Security Advisories are enabled for this repo).

Include:

- A description of the issue and its impact
- Steps to reproduce (proof-of-concept if safe to share)
- Affected components (extension, API, or both)

We aim to acknowledge reports within a few business days. Please allow reasonable time for a fix before public disclosure.

## Scope notes

- The API is intended to be deployed with appropriate **network controls**, **authentication**, and **rate limiting** in production; the reference `docker-compose.yml` is for development.
- Never commit API keys, tokens, or `.env` files containing secrets.
