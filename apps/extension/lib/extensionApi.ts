/**
 * Cross-browser extension API (Chrome, Edge, Brave, Opera, Firefox, Safari Web Extension).
 * Prefer this over raw `chrome` so MV3 builds behave consistently where APIs differ.
 */
import browser from "webextension-polyfill"

export default browser
