# FairTerms browser extension

Plasmo + React **Manifest V3** extension that extracts visible legal text from the active tab, sends it to the FairTerms API, and shows traffic-light risk cards with optional “show on page” highlighting.

Runtime APIs go through [`webextension-polyfill`](https://github.com/mozilla/webextension-polyfill) so the same code runs on Chromium-based browsers and Firefox.

## Requirements

- Node.js 18+
- npm or pnpm

## Development (Chrome / Edge / Brave / Opera — Chromium bundle)

```bash
npm install
npm run dev
```

Open your browser’s extensions page, enable **Developer mode**, **Load unpacked**, and select:

`apps/extension/build/chrome-mv3-dev`

| Browser | Extensions page (typical) |
|---------|---------------------------|
| Google Chrome | `chrome://extensions` |
| Microsoft Edge | `edge://extensions` |
| Brave | `brave://extensions` |
| Opera | `opera://extensions` (or **Extensions** in the menu) |

Use the **`build/chrome-mv3-*` output** for all of the above: they share Chromium’s extension model, so one build is enough.

## Development (Firefox)

```bash
npm run dev:firefox
```

Load unpacked from:

`apps/extension/build/firefox-mv3-dev`

In Firefox: `about:debugging` → **This Firefox** → **Load Temporary Add-on** → pick `manifest.json` inside that folder.

## Production builds

| Command | Output folder | Use for |
|---------|---------------|---------|
| `npm run build` or `npm run build:chromium` | `build/chrome-mv3-prod` | Chrome, Edge, Brave, Opera |
| `npm run build:firefox` | `build/firefox-mv3-prod` | Firefox |
| `npm run build:safari` | `build/safari-mv3-prod` | Safari (next step: Apple converter, see below) |

## Safari (extra steps)

Plasmo emits a **Safari-oriented MV3 bundle**, but Apple still expects you to **wrap and sign** it as a Safari Web Extension (Xcode, **Safari Web Extension Converter**, Apple Developer Program). There is no way around Apple’s packaging and review rules from this repo alone. After `npm run build:safari`, follow Apple’s current docs: [Converting a web extension for Safari](https://developer.apple.com/documentation/safariservices/safari_web_extensions/converting_a_web_extension_for_safari).

## Configuration

The popup reads the API base URL from **sync storage** (`apiUrl`). The default is `http://localhost:8000` (see `popup.tsx`). Point it at your self-hosted API in production.

## Permissions

The manifest requests `activeTab`, `scripting`, and `tabs`, plus broad `host_permissions` for reading page content and PDFs. Review `package.json` → `manifest` before publishing; store listings differ per vendor (Chrome Web Store, Firefox Add-ons, Microsoft Edge Add-ons, etc.).

## Repository layout

This app lives under `apps/extension/` in the [FairTerms monorepo](../../README.md).

## License

[MIT](../../LICENSE)
