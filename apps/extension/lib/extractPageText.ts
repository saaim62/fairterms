/**
 * Chrome’s built-in PDF viewer often leaves `document.body.innerText` empty; we scan
 * all frames (text layers + shadow roots) and optionally fetch-parse the PDF URL.
 */

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

function isBlockedChromeUrl(url: string): boolean {
  return (
    url.startsWith("chrome://") ||
    url.startsWith("chrome-extension://") ||
    url.startsWith("edge://") ||
    url.startsWith("about:")
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
  const v = tryDecode((raw || "").trim())
  if (!v) return ""
  if (/^https?:\/\//i.test(v)) return v
  if (/^file:\/\//i.test(v)) return v
  return ""
}

/**
 * Chrome PDF viewer often wraps the real URL:
 * - chrome-extension://.../index.html?src=file%3A%2F%2F...pdf
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

async function extractTextFromPdfUrl(url: string, maxChars: number): Promise<string> {
  try {
    const pdfjs = await import("pdfjs-dist/build/pdf.mjs")
    const workerSrc = chrome.runtime.getURL("pdf.worker.min.mjs")
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
  let injectionResults: chrome.scripting.InjectionResult<string>[] = []
  try {
    injectionResults = await chrome.scripting.executeScript({
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

  const url = extractPdfUrlCandidate(tabUrl || "")
  const tooShort = merged.trim().length < 120
  if (tooShort && looksLikePdfUrl(url) && !isBlockedChromeUrl(url)) {
    const fromPdf = await extractTextFromPdfUrl(url, MAX_ANALYZE_CHARS)
    if (fromPdf.trim().length > merged.trim().length) {
      merged = fromPdf.slice(0, MAX_ANALYZE_CHARS)
    }
  }

  return merged
}
