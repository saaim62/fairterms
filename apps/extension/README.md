# FairTerms browser extension

Plasmo + React **Manifest V3** extension that extracts visible legal text from the active tab, sends it to the FairTerms API, and shows traffic-light risk cards with optional “show on page” highlighting.

## Requirements

- Node.js 18+
- npm or pnpm

## Development

```bash
npm install
npm run dev
```

In Chrome: `chrome://extensions` → Developer mode → **Load unpacked** → select:

`apps/extension/build/chrome-mv3-dev`

Edit `popup.tsx` and related components; Plasmo hot-reloads when possible.

## Production build

```bash
npm run build
```

Load from `build/chrome-mv3-prod` for a production-like bundle.

## Configuration

The popup reads the API base URL from `chrome.storage.sync` (`apiUrl`). The default is `http://localhost:8000` (see `popup.tsx`). Point it at your self-hosted API in production.

## Permissions

The manifest requests `activeTab`, `scripting`, and `tabs`, plus broad `host_permissions` for reading page content and PDFs. Review `package.json` → `manifest` before publishing.

## Repository layout

This app lives under `apps/extension/` in the [FairTerms monorepo](../../README.md).

## License

[MIT](../../LICENSE)
