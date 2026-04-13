/**
 * Chromium / Firefox built-in PDF viewers often leave `document.body.innerText` empty; we scan
 * all frames (text layers + shadow roots) and optionally fetch-parse the PDF URL.
 */

import browser from "./extensionApi"

export const MAX_ANALYZE_CHARS = 30000

/** Injected into every frame; must stay self-contained (no closures/imports). */
export function scrapeFrameTextForInjection(): string {
  const acc: string[] = []

  function collectTextLayer(root: Document | ShadowRoot) {
    root.querySelectorAll("*").forEach((el) => {
      if (el.shadowRoot) collectTextLayer(el.shadowRoot)
    })
    root.querySelectorAll(".textLayer span").forEach((s) => {
      const t = (s.textContent || "").trim()
      if (t) acc.push(t)
    })
  }

  collectTextLayer(document)
  const fromLayers = acc.join(" ")

  const body = (document.body && document.body.innerText) || ""
  const rootText = (document.documentElement && document.documentElement.innerText) || ""

  const candidates = [fromLayers, body, rootText].filter((s) => s.trim().length > 0)
  candidates.sort((a, b) => b.length - a.length)
  return (candidates[0] || "").slice(0, 50000)
}

function looksLikePdfUrl(url: string): boolean {
  if (!url) return false
  if (/\.pdf(\?|#|$)/i.test(url)) return true
  return url.toLowerCase().includes("application/pdf")
}

/** URLs we must not fetch as HTTP(S) (browser internals and extension origins). */
function isBlockedInternalOrExtensionUrl(url: string): boolean {
  const u = url.toLowerCase()
  return (
    u.startsWith("chrome://") ||
    u.startsWith("chrome-extension://") ||
    u.startsWith("edge://") ||
    u.startsWith("brave://") ||
    u.startsWith("opera://") ||
    u.startsWith("vivaldi://") ||
    u.startsWith("moz-extension://") ||
    u.startsWith("about:")
  )
}

function tryDecode(value: string): string {
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

function normalizePdfCandidate(raw: string): string {
  let v = tryDecode((raw || "").trim())
  if (!v) return ""

  if (/^https?:\/\//i.test(v)) return v

  if (/^file:/i.test(v)) {
    v = v.replace(/^file:\/*/i, "file:///")
    return v
  }

  if (/^[A-Za-z]:[\\/]/.test(v)) {
    return `file:///${v.replace(/\\/g, "/")}`
  }

  if (/^\/[A-Za-z]:[\\/]/.test(v)) {
    return `file://${v.replace(/\\/g, "/")}`
  }

  return ""
}

/**
 * Chrome PDF viewer often wraps the real URL:
 * - chrome-extension://.../index.html?src=file%3A%2F%2F...pdf
 * - moz-extension://... (Firefox PDF.js) with similar query params
 * - chrome-extension://.../index.html?file=https%3A%2F%2F...pdf
 */
function extractPdfUrlCandidate(tabUrl: string): string {
  const direct = normalizePdfCandidate(tabUrl)
  if (direct && looksLikePdfUrl(direct)) return direct

  if (!tabUrl) return ""
  let parsed: URL
  try {
    parsed = new URL(tabUrl)
  } catch {
    return ""
  }

  const paramKeys = ["src", "file", "url"]
  for (const key of paramKeys) {
    const raw = parsed.searchParams.get(key)
    if (!raw) continue
    const candidate = normalizePdfCandidate(raw)
    if (candidate && looksLikePdfUrl(candidate)) return candidate
  }

  return ""
}

/**
 * True when the active tab is a PDF (or Chrome's built-in PDF viewer).
 * In-page locate/highlight does not work reliably there; analysis may still use fetched text.
 */
export function isPdfLikeTabUrl(tabUrl: string | undefined): boolean {
  if (!tabUrl) return false
  if (looksLikePdfUrl(tabUrl)) return true
  if (tabUrl.startsWith("chrome-extension://") || tabUrl.startsWith("moz-extension://")) {
    const extracted = extractPdfUrlCandidate(tabUrl)
    if (extracted && looksLikePdfUrl(extracted)) return true
    // Chromium built-in PDF viewer extension (stable channel)
    if (tabUrl.includes("mhjfbmdgcfjbbpaeojofohoefgiehjai")) return true
  }
  return false
}

function collectPdfCandidatesFromPage(): string[] {
  const urls = new Set<string>()
  const elements = Array.from(document.querySelectorAll("iframe,embed,object,a"))

  const pushCandidate = (value: string | null | undefined) => {
    if (!value) return
    const raw = value.trim()
    if (!raw) return
    if (raw.toLowerCase().includes(".pdf") || raw.toLowerCase().includes("application/pdf")) {
      urls.add(raw)
    }
  }

  for (const element of elements) {
    if (element instanceof HTMLAnchorElement) {
      pushCandidate(element.href)
    } else if (element instanceof HTMLIFrameElement) {
      pushCandidate(element.src)
      pushCandidate(element.getAttribute("src"))
    } else if (element instanceof HTMLObjectElement) {
      pushCandidate(element.data)
      pushCandidate(element.getAttribute("src"))
      pushCandidate(element.getAttribute("data"))
    } else if (element instanceof HTMLEmbedElement) {
      pushCandidate(element.src)
      pushCandidate(element.getAttribute("src"))
    }
  }

  return Array.from(urls)
}

async function extractTextFromPdfUrl(url: string, maxChars: number): Promise<string> {
  try {
    const pdfjs = await import("pdfjs-dist/build/pdf.mjs")
    const workerSrc = browser.runtime.getURL("assets/pdf.worker.min.mjs")
    pdfjs.GlobalWorkerOptions.workerSrc = workerSrc

    const res = await fetch(url, { credentials: "omit", cache: "no-cache" })
    if (!res.ok) return ""

    const buf = await res.arrayBuffer()
    let doc: any
    try {
      const loadingTask = pdfjs.getDocument({ data: buf, useSystemFonts: true })
      doc = await loadingTask.promise
    } catch {
      // Fallback for environments where the worker asset is unavailable.
      const loadingTaskNoWorker = pdfjs.getDocument({
        data: buf,
        useSystemFonts: true,
        disableWorker: true
      })
      doc = await loadingTaskNoWorker.promise
    }

    const out: string[] = []
    let total = 0
    for (let i = 1; i <= doc.numPages && total < maxChars; i += 1) {
      const page = await doc.getPage(i)
      const content = await page.getTextContent()
      const line = content.items
        .map((item) => {
          if (item && typeof item === "object" && "str" in item) {
            return String((item as { str: string }).str)
          }
          return ""
        })
        .join(" ")
      out.push(line)
      total += line.length + 1
    }
    return out.join("\n").slice(0, maxChars)
  } catch {
    return ""
  }
}

export async function extractTabTextForAnalyze(
  tabId: number,
  tabUrl: string | undefined
): Promise<string> {
  let injectionResults: Awaited<ReturnType<typeof browser.scripting.executeScript>> = []
  try {
    injectionResults = await browser.scripting.executeScript({
      target: { tabId, allFrames: true },
      func: scrapeFrameTextForInjection as () => string
    })
  } catch {
    // Some PDF/system pages block script injection; fallback to PDF fetch path below.
    injectionResults = []
  }

  const pieces = injectionResults
    .map((r) => String(r.result || "").trim())
    .filter((s) => s.length > 0)
  pieces.sort((a, b) => b.length - a.length)

  let merged = ""
  if (pieces.length === 0) merged = ""
  else if (pieces.length === 1) merged = pieces[0]
  else {
    const longest = pieces[0]
    const second = pieces[1] || ""
    merged =
      longest.length >= second.length * 1.4 ? longest : pieces.join("\n\n")
  }
  merged = merged.slice(0, MAX_ANALYZE_CHARS)

  const directUrl = extractPdfUrlCandidate(tabUrl || "")
  const candidates = [directUrl]

  if (!looksLikePdfUrl(directUrl)) {
    try {
      const pdfCandidates = await browser.scripting.executeScript({
        target: { tabId, allFrames: true },
        func: collectPdfCandidatesFromPage as () => string[]
      })
      for (const result of pdfCandidates) {
        if (Array.isArray(result.result)) {
          candidates.push(...result.result.map(String))
        }
      }
    } catch {
      // Ignore; candidate extraction may be blocked on some pages.
    }
  }

  const normalizedCandidates = candidates
    .map((raw) => normalizePdfCandidate(raw))
    .filter(
      (candidate) =>
        candidate && looksLikePdfUrl(candidate) && !isBlockedInternalOrExtensionUrl(candidate)
    )

  for (const candidate of normalizedCandidates) {
    const fromPdf = await extractTextFromPdfUrl(candidate, MAX_ANALYZE_CHARS)
    if (fromPdf.trim().length > merged.trim().length) {
      merged = fromPdf.slice(0, MAX_ANALYZE_CHARS)
      break
    }
  }

  return merged
}
