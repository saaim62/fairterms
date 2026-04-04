import { useMemo, useState } from "react"

import { AnalyzeButton } from "./components/AnalyzeButton"
import { IssueCard } from "./components/IssueCard"
import { PopupHeader } from "./components/PopupHeader"
import { StatusCard } from "./components/StatusCard"
import { extractTabTextForAnalyze } from "./lib/extractPageText"
import { theme } from "./styles/theme"
import type { AnalyzeResponse, RiskIssue } from "../../packages/shared-types"

const API_URL = "http://localhost:8000/analyze"

/** Strip LLM/UI wrapping quotes so matching uses the same text as the page. */
function cleanEvidenceForLocate(raw: string): string {
  let s = (raw || "").trim()
  for (;;) {
    let changed = false
    if (
      (s.startsWith('"') && s.endsWith('"')) ||
      (s.startsWith("'") && s.endsWith("'"))
    ) {
      s = s.slice(1, -1).trim()
      changed = true
    } else if (s.startsWith("\u201c") && s.endsWith("\u201d")) {
      s = s.slice(1, -1).trim()
      changed = true
    } else if (s.startsWith("\u2018") && s.endsWith("\u2019")) {
      s = s.slice(1, -1).trim()
      changed = true
    }
    if (!changed) break
  }
  return s.trim()
}

function IndexPopup() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [actionMessage, setActionMessage] = useState("")
  const [result, setResult] = useState<AnalyzeResponse | null>(null)

  const signalLabel = useMemo(() => {
    if (!result) return "Awaiting Scan"
    return result.signal === "red"
      ? "High Risk"
      : result.signal === "yellow"
        ? "Caution"
        : "Secure"
  }, [result])

  const issuesSorted = useMemo(() => {
    if (!result?.issues?.length) return []
    const rank = (s: string) => (s === "red" ? 0 : s === "yellow" ? 1 : 2)
    return [...result.issues].sort((a, b) => {
      const ra = rank(a.severity)
      const rb = rank(b.severity)
      if (ra !== rb) return ra - rb
      return (b.confidence ?? 0) - (a.confidence ?? 0)
    })
  }, [result?.issues])

  const analyzeCurrentPage = async () => {
    setLoading(true)
    setError("")
    setActionMessage("")
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
      if (!tab?.id) {
        throw new Error("No active tab found")
      }

      const extractedText = await extractTabTextForAnalyze(tab.id, tab.url)

      if (!extractedText.trim()) {
        throw new Error(
          "No readable text found. For PDFs: enable “Allow access to file URLs” in chrome://extensions for local files, and note some scanned/image-only PDFs do not contain selectable text."
        )
      }

      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: extractedText || "",
          source_url: tab.url || null
        })
      })

      if (!response.ok) {
        throw new Error(`API Connection Failed`)
      }

      const json = (await response.json()) as AnalyzeResponse
      setResult(json)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Analysis failed"
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const showIssueOnPage = async (issue: RiskIssue) => {
    setActionMessage("")
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
      if (!tab?.id) return

      const cleanedQuote = cleanEvidenceForLocate(issue.evidence_quote)

      const locateScript = {
        target: { tabId: tab.id, allFrames: true },
        args: [cleanedQuote, issue.label, issue.category],
        func: (evidenceQuote: string, label: string, category: string) => {
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

          const redCategories = new Set([
            "zombie_renewal",
            "arbitration_waiver",
            "class_bar_standalone",
            "data_succession",
            "gag_clauses",
            "unilateral_interpretation",
            "liquidated_damages_penalties",
            "perpetual_restraint",
            "waiver_of_statutory_rights",
            "device_exploitation",
            "data_selling",
            "private_message_monitoring",
            "content_copyright_transfer",
            "moral_rights_waiver",
            "shortened_limitation_period",
            "ai_training_license",
            "biometric_harvesting",
            "off_platform_tracking",
            "inactivity_fee_seizure",
            "notice_of_breach_delay"
          ])
          const highlightColor =
            label.toLowerCase().includes("safe") || category === "safe"
              ? "#22C55E"
              : redCategories.has(category)
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
            if (
              startContainer !== endContainer ||
              startContainer.nodeType !== Node.TEXT_NODE
            ) {
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

          // First try browser-native text finding (handles cross-node text well).
          const clauseBeforePeriod = firstClauseBeforeNonDecimalPeriod(core)
          const nativeFindProbes = [
            core,
            core.slice(0, 260),
            core.slice(0, 180),
            core.slice(0, 120),
            clauseBeforePeriod,
            core.split(";")[0] || ""
          ]
            .map((x) => x.trim())
            .filter((x) => x.length >= 18)

          const selection = window.getSelection()
          for (const probe of nativeFindProbes) {
            selection?.removeAllRanges()
            const found = (window as any).find(
              probe,
              false,
              false,
              true,
              false,
              false,
              false
            )
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
            if (
              tag === "SCRIPT" ||
              tag === "STYLE" ||
              tag === "NOSCRIPT" ||
              tag === "TEXTAREA" ||
              tag === "OPTION"
            ) {
              return false
            }
            const style = window.getComputedStyle(parent)
            return style.display !== "none" && style.visibility !== "hidden"
          }

          type NodeRange = {
            node: Text
            start: number
            end: number
          }

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

          const categoryHints: Record<string, string[]> = {
            unilateral_changes: ["change terms", "amend terms", "without notice", "continued use"],
            retroactive_changes: ["retroactive", "prior conduct", "already collected"],
            auto_renewal: ["auto-renew", "renews automatically", "subscription fee", "billing cycle"],
            zombie_renewal: ["reminder", "automatically renew", "annual"],
            arbitration_waiver: ["binding arbitration", "class action waiver", "jury trial"],
            class_bar_standalone: ["class action", "representative action", "no class"],
            data_rights: ["perpetual license", "irrevocable license", "third parties", "share data"],
            data_succession: ["successor", "merger", "bankruptcy", "assign"],
            cross_service_tracking: ["cross-service", "across our products", "combine data"],
            fee_modification: ["price", "fee", "notice", "grandfather"],
            cancellation_friction: ["non-refundable", "no refunds", "cancel", "cancellation fee"],
            gag_clauses: ["non-disparagement", "negative review", "review"],
            unilateral_interpretation: ["sole discretion", "interpret", "exclusive right"],
            liquidated_damages_penalties: ["liquidated damages", "per breach", "infraction"],
            one_way_attorneys_fees: ["attorneys fees", "prevailing party"],
            no_injunctive_relief: ["injunctive", "equitable relief"],
            mandatory_delay_tactics: ["mediation", "before filing", "days before"],
            perpetual_restraint: ["non-compete", "survive termination"],
            no_assignment_by_user: ["may not assign", "assignable"],
            overbroad_ip_restrictions: ["reverse engineer", "decompile"],
            device_exploitation: ["cryptomining", "processing power", "bandwidth"],
            shadow_profiling: ["contacts", "data broker", "non-user"],
            waiver_of_statutory_rights: ["ccpa", "gdpr", "waive"],
            english_language_supremacy: ["english version", "translation"],
            survival_of_termination_vague: ["survive termination", "necessary provisions"],
            limitation_of_liability: ["limitation of liability", "consequential damages", "not liable"],
            disclaimer_of_warranties: ["as is", "merchantability", "disclaimer of warranties"],
            broad_indemnity: ["indemnify", "hold harmless", "defend"],
            forum_selection_exclusive: ["exclusive jurisdiction", "exclusive venue", "jurisdiction"],
            discretionary_termination: ["sole discretion", "suspend", "terminate"],
            children_data_collection: ["under 13", "children", "parental consent"],
            marketing_communications_burden: ["marketing", "promotional", "sms", "opt out"],
            data_selling: ["sell personal information", "monetize data", "sale of data"],
            private_message_monitoring: ["private message", "direct message", "monitor communications"],
            device_fingerprinting: ["device fingerprint", "pixel tags", "web beacons"],
            continuous_location_tracking: ["precise location", "geolocation", "background location", "gps"],
            content_copyright_transfer: ["assign copyright", "exclusive license", "ownership"],
            moral_rights_waiver: ["moral rights", "waive attribution", "credit"],
            shortened_limitation_period: ["within one year", "time limit", "barred"],
            data_deletion_friction: ["retain after deletion", "backup copies", "no obligation to delete"],
            third_party_disclaimer: ["not responsible third-party", "at your own risk", "no control over"],
            force_majeure_broad: ["force majeure", "acts of god", "beyond our control"],
            ai_training_license: ["train ai", "machine learning", "llm", "training data"],
            biometric_harvesting: ["biometric", "facial recognition", "voiceprint", "fingerprint"],
            off_platform_tracking: ["browser history", "outside the service", "other applications", "keystroke"],
            inactivity_fee_seizure: ["inactivity fee", "dormant account", "unused credits expire"],
            no_refund_on_ban: ["without refund", "forfeit purchases", "no right to a refund"],
            payment_method_updating: ["account updater", "updated credit card", "update payment information"],
            beta_testing_waiver: ["beta features", "experimental", "at your own risk", "pre-release software"],
            notice_of_breach_delay: ["notify within 60 days", "90 days", "120 days", "commercially reasonable time"],
            consent_to_background_check: ["background check", "credit check", "criminal history"]
          }

          const tokenWords = quoteNorm
            .split(" ")
            .map((w) => w.trim())
            .filter((w) => w.length > 2)
          const quoteProbes = [
            quoteNorm,
            quoteNorm.slice(0, 260),
            quoteNorm.slice(0, 180),
            quoteNorm.slice(0, 120),
            quoteNorm.slice(0, 80)
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
              const hints = (categoryHints[category] || []).map((h) =>
                normalizeWithMap(h).text
              )
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
      }

      const tryLocate = async () => {
        const results = await chrome.scripting.executeScript(locateScript)
        return results.some((res) => Boolean(res.result))
      }

      const waitForTabReload = async (tabId: number) =>
        await new Promise<void>((resolve) => {
          let done = false
          const onUpdated = (updatedTabId: number, info: chrome.tabs.TabChangeInfo) => {
            if (updatedTabId === tabId && info.status === "complete") {
              chrome.tabs.onUpdated.removeListener(onUpdated)
              done = true
              resolve()
            }
          }
          chrome.tabs.onUpdated.addListener(onUpdated)
          setTimeout(() => {
            if (!done) {
              chrome.tabs.onUpdated.removeListener(onUpdated)
              resolve()
            }
          }, 6000)
        })

      let didHighlight = false
      try {
        didHighlight = await tryLocate()
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        const isContextInvalidated =
          msg.toLowerCase().includes("extension context invalidated") ||
          msg.toLowerCase().includes("context invalidated")

        if (!isContextInvalidated) throw err

        setActionMessage("Recovering stale extension context...")
        await chrome.tabs.reload(tab.id)
        await waitForTabReload(tab.id)
        didHighlight = await tryLocate()
      }

      if (didHighlight) {
        setActionMessage(`Located: ${issue.label}`)
      } else {
        setActionMessage(
          "Could not locate text on this page (try refreshing the tab, or the viewer may block highlighting)."
        )
      }
    } catch (err) {
      // silent fail for highlight
      setActionMessage(
        "Could not locate text on this page (try refreshing the tab, or the viewer may block highlighting)."
      )
    }
  }

  return (
    <div
      style={{
        padding: "20px 16px",
        width: 340,
        minHeight: 400,
        fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
        background: theme.background,
        color: theme.textPrimary,
        display: "flex",
        flexDirection: "column",
        position: "relative",
        overflow: "hidden"
      }}>
      {/* Background Glow */}
      <div style={{
        position: "absolute",
        top: -100,
        right: -100,
        width: 200,
        height: 200,
        background: `${theme.primary}22`,
        filter: "blur(60px)",
        borderRadius: "50%",
        zIndex: 0
      }} />

      <div style={{ zIndex: 1 }}>
        <PopupHeader />
        <AnalyzeButton loading={loading} onClick={analyzeCurrentPage} />
        <StatusCard signal={result?.signal} label={signalLabel} />

        {error ? (
          <div style={{ 
            marginTop: 16, 
            padding: 12, 
            borderRadius: 8, 
            background: `${theme.danger}11`, 
            border: `1px solid ${theme.danger}33`,
            color: theme.danger,
            fontSize: 12,
            textAlign: "center"
          }}>
            {error}
          </div>
        ) : null}

        {actionMessage ? (
          <div style={{ 
            marginTop: 12, 
            textAlign: "center",
            color: theme.secondary,
            fontSize: 11,
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.05em"
          }}>
            {actionMessage}
          </div>
        ) : null}

        <div style={{ marginTop: 20, display: "grid", gap: 12 }}>
          {issuesSorted.map((issue, idx) => (
            <IssueCard
              key={`${issue.category}-${idx}`}
              issue={issue}
              onShowOnPage={showIssueOnPage}
            />
          ))}
          
          {result && result.issues.length === 0 && !loading && (
            <div style={{ 
              textAlign: "center", 
              padding: "40px 20px",
              color: theme.textMuted
            }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>🛡️</div>
              <div style={{ color: theme.success, fontWeight: 700, marginBottom: 4 }}>No Risks Detected</div>
              <div style={{ fontSize: 12 }}>This document appears to follow standard fair practices.</div>
            </div>
          )}
        </div>
      </div>
      
      <div style={{ 
        marginTop: "auto", 
        paddingTop: 24, 
        textAlign: "center", 
        fontSize: 10, 
        color: theme.textMuted,
        opacity: 0.6
      }}>
        {result?.disclaimer || "FairTerms AI • v0.1.0"}
      </div>
    </div>
  )
}

export default IndexPopup
