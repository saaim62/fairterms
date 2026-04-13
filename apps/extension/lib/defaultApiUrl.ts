/**
 * Build-time default API base URL from `apps/extension/.env`:
 * `PLASMO_PUBLIC_API_URL=https://your-host` (no trailing slash required).
 * Falls back to local API when unset (e.g. missing `.env`).
 */
export const DEFAULT_API_URL = (
  process.env.PLASMO_PUBLIC_API_URL || "http://localhost:8000"
).replace(/\/+$/, "")
