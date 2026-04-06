/**
 * Injected into the active tab to locate and highlight a clause on the page.
 * Must be self-contained — no imports/closures (serialized by chrome.scripting.executeScript).
 */

import { RED_CATEGORY_KEYS, CATEGORY_HINTS } from "./categoryMeta"

export function highlightClauseOnPage(
  evidenceQuote: string,
  label: string,
  category: string
): boolean {
  const HIGHLIGHT_ATTR = "data-fairterms-highlight"
  const previous = document.querySelectorAll(`mark[${HIGHLIGHT_ATTR}]`)
  previous.forEach((el) => {
    const parent = el.parentNode
    if (!parent) return
    const text = document.createTextNode(el.textContent || "")
    parent.replaceChild(text, el)
    parent.normalize()
  })

  const stripOuterQuotes = (s: string) => {
    let t = (s || "").trim()
    for (;;) {
      let ch = false
      if (
        (t.startsWith('"') && t.endsWith('"')) ||
        (t.startsWith("'") && t.endsWith("'"))
      ) {
        t = t.slice(1, -1).trim()
        ch = true
      } else if (t.startsWith("\u201c") && t.endsWith("\u201d")) {
        t = t.slice(1, -1).trim()
        ch = true
      } else if (t.startsWith("\u2018") && t.endsWith("\u2019")) {
        t = t.slice(1, -1).trim()
        ch = true
      }
      if (!ch) break
    }
    return t
  }

  const canonicalChar = (ch: string) => {
    if (ch === "\u201c" || ch === "\u201d" || ch === "\u201e" || ch === "\u201f") return '"'
    if (ch === "\u2018" || ch === "\u2019" || ch === "\u201a" || ch === "\u201b") return "'"
    if (ch === "\u2013" || ch === "\u2014") return "-"
    return ch
  }

  const normalizeWithMap = (raw: string) => {
    let out = ""
    const map: number[] = []
    let prevSpace = true
    for (let i = 0; i < raw.length; i += 1) {
      const c = canonicalChar(raw[i]).toLowerCase()
      const isSpace = /\s/.test(c)
      if (isSpace) {
        if (!prevSpace) {
          out += " "
          map.push(i)
          prevSpace = true
        }
      } else {
        out += c
        map.push(i)
        prevSpace = false
      }
    }
    while (out.endsWith(" ")) {
      out = out.slice(0, -1)
      map.pop()
    }
    return { text: out, map }
  }

  const core = stripOuterQuotes(evidenceQuote)
  if (!core) return false

  const highlightColor =
    label.toLowerCase().includes("safe") || category === "safe"
      ? "#22C55E"
      : RED_CATEGORY_KEYS.has(category)
        ? "#EF4444"
        : "#F59E0B"

  const isDecimalDot = (s: string, i: number) => {
    if (i < 0 || i >= s.length || s[i] !== ".") return false
    const prev = i > 0 ? s[i - 1] : ""
    const next = i + 1 < s.length ? s[i + 1] : ""
    return /\d/.test(prev) && /\d/.test(next)
  }

  const firstClauseBeforeNonDecimalPeriod = (s: string) => {
    for (let i = 0; i < s.length; i += 1) {
      if (s[i] !== ".") continue
      if (isDecimalDot(s, i)) continue
      const slice = s.slice(0, i).trim()
      if (slice.length >= 18) return slice
    }
    return ""
  }

  const expandOffsetsToFullLine = (text: string, start: number, end: number) => {
    const lineStart = text.lastIndexOf("\n", Math.max(0, start - 1)) + 1
    let lineEnd = text.indexOf("\n", end)
    if (lineEnd === -1) lineEnd = text.length
    return { start: lineStart, end: lineEnd }
  }

  const expandRangeToFullLine = (range: Range) => {
    const { startContainer, endContainer, startOffset, endOffset } = range
    if (startContainer !== endContainer || startContainer.nodeType !== Node.TEXT_NODE) {
      return range.cloneRange()
    }
    const t = startContainer.textContent || ""
    let { start: ls, end: le } = expandOffsetsToFullLine(t, startOffset, endOffset)
    if (le <= ls) le = Math.min(t.length, ls + 1)
    const r = document.createRange()
    r.setStart(startContainer, Math.max(0, Math.min(ls, t.length)))
    r.setEnd(startContainer, Math.max(0, Math.min(le, t.length)))
    return r
  }

  const wrapRangeWithMark = (range: Range) => {
    const mark = document.createElement("mark")
    mark.setAttribute(HIGHLIGHT_ATTR, label)
    mark.style.backgroundColor = `${highlightColor}33`
    mark.style.outline = `2px solid ${highlightColor}`
    mark.style.borderRadius = "4px"
    mark.style.padding = "0 2px"
    mark.style.boxShadow = `0 0 12px ${highlightColor}44`
    mark.style.transition = "all 0.3s ease"
    try {
      range.surroundContents(mark)
    } catch {
      const frag = range.extractContents()
      mark.appendChild(frag)
      range.insertNode(mark)
    }
    mark.scrollIntoView({ behavior: "smooth", block: "center" })
    return true
  }

  const clauseBeforePeriod = firstClauseBeforeNonDecimalPeriod(core)
  const nativeFindProbes = [
    core, core.slice(0, 260), core.slice(0, 180), core.slice(0, 120),
    clauseBeforePeriod, core.split(";")[0] || ""
  ].map((x) => x.trim()).filter((x) => x.length >= 18)

  const selection = window.getSelection()
  for (const probe of nativeFindProbes) {
    selection?.removeAllRanges()
    const found = (window as any).find(probe, false, false, true, false, false, false)
    if (!found) continue
    const sel = window.getSelection()
    if (!sel || sel.rangeCount === 0) continue
    const range = expandRangeToFullLine(sel.getRangeAt(0).cloneRange())
    sel.removeAllRanges()
    return wrapRangeWithMark(range)
  }

  const isVisibleTextNode = (node: Text) => {
    const parent = node.parentElement
    if (!parent) return false
    const tag = parent.tagName
    if (tag === "SCRIPT" || tag === "STYLE" || tag === "NOSCRIPT" || tag === "TEXTAREA" || tag === "OPTION") return false
    const style = window.getComputedStyle(parent)
    return style.display !== "none" && style.visibility !== "hidden"
  }

  type NodeRange = { node: Text; start: number; end: number }

  const nodes: NodeRange[] = []
  let flatRaw = ""
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
  while (walker.nextNode()) {
    const node = walker.currentNode as Text
    if (!node.textContent || !node.textContent.trim()) continue
    if (!isVisibleTextNode(node)) continue
    const start = flatRaw.length
    flatRaw += node.textContent
    const end = flatRaw.length
    nodes.push({ node, start, end })
    flatRaw += "\n"
  }

  if (!flatRaw || nodes.length === 0) return false

  const docNorm = normalizeWithMap(flatRaw)
  const quoteNorm = normalizeWithMap(core).text
  if (!quoteNorm) return false

  const categoryHints: Record<string, string[]> = CATEGORY_HINTS

  const tokenWords = quoteNorm.split(" ").map((w) => w.trim()).filter((w) => w.length > 2)
  const quoteProbes = [
    quoteNorm, quoteNorm.slice(0, 260), quoteNorm.slice(0, 180),
    quoteNorm.slice(0, 120), quoteNorm.slice(0, 80)
  ].filter((p) => p.length >= 22)

  let bestNormStart = -1
  let bestNormLen = -1
  let bestScore = -1

  for (const probe of quoteProbes) {
    const idx = docNorm.text.indexOf(probe)
    if (idx !== -1 && probe.length > bestScore) {
      bestNormStart = idx
      bestNormLen = probe.length
      bestScore = probe.length + 50
      break
    }
  }

  if (bestNormStart === -1 && tokenWords.length > 0) {
    const anchorWords = tokenWords.slice(0, 12)
    const first = anchorWords[0]
    const expectedLen = Math.max(90, Math.min(340, quoteNorm.length + 60))
    let idx = docNorm.text.indexOf(first)
    while (idx !== -1) {
      let score = 0
      let cursor = idx
      for (const w of anchorWords) {
        const next = docNorm.text.indexOf(w, cursor)
        if (next !== -1 && next - idx <= 520) {
          score += w.length
          cursor = next + w.length
        }
      }
      const hints = (categoryHints[category] || []).map((h) => normalizeWithMap(h).text)
      for (const h of hints) {
        if (h && docNorm.text.indexOf(h, idx) !== -1 && docNorm.text.indexOf(h, idx) - idx <= 520) {
          score += 8
        }
      }
      if (score > bestScore) {
        bestScore = score
        bestNormStart = idx
        bestNormLen = expectedLen
      }
      idx = docNorm.text.indexOf(first, idx + 1)
    }
  }

  if (bestNormStart === -1 || bestScore < 20) return false

  const normEnd = Math.min(docNorm.text.length, bestNormStart + bestNormLen)
  const rawStart = docNorm.map[Math.max(0, bestNormStart)] ?? 0
  const rawEnd = (docNorm.map[Math.max(0, normEnd - 1)] ?? rawStart) + 1
  if (rawEnd <= rawStart) return false

  let chosen: NodeRange | null = null
  let chosenLocalStart = 0
  let chosenLocalEnd = 0
  let overlapBest = 0
  for (const r of nodes) {
    const overlapStart = Math.max(rawStart, r.start)
    const overlapEnd = Math.min(rawEnd, r.end)
    const overlap = overlapEnd - overlapStart
    if (overlap > overlapBest) {
      overlapBest = overlap
      chosen = r
      chosenLocalStart = overlapStart - r.start
      chosenLocalEnd = overlapEnd - r.start
    }
  }

  if (!chosen || overlapBest <= 0) return false
  const nodeText = chosen.node.textContent || ""
  if (!nodeText) return false
  let start = Math.max(0, Math.min(chosenLocalStart, nodeText.length - 1))
  let end = Math.max(start + 1, Math.min(chosenLocalEnd, nodeText.length))
  const line = expandOffsetsToFullLine(nodeText, start, end)
  start = line.start
  end = line.end
  if (end <= start) end = Math.min(nodeText.length, start + 1)

  const range = document.createRange()
  range.setStart(chosen.node, start)
  range.setEnd(chosen.node, end)
  return wrapRangeWithMark(range)
}
