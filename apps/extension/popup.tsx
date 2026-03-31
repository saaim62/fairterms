import { useMemo, useState } from "react"

import { AnalyzeButton } from "./components/AnalyzeButton"
import { IssueCard } from "./components/IssueCard"
import { PopupHeader } from "./components/PopupHeader"
import { StatusCard } from "./components/StatusCard"
import { theme } from "./styles/theme"
import type { AnalyzeResponse, RiskIssue } from "../../packages/shared-types"

const API_URL = "http://localhost:8000/analyze"

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

  const analyzeCurrentPage = async () => {
    setLoading(true)
    setError("")
    setActionMessage("")
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
      if (!tab?.id) {
        throw new Error("No active tab found")
      }

      const [{ result: extractedText }] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const text = document.body?.innerText || ""
          return text.slice(0, 30000)
        }
      })

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

      const [{ result: didHighlight }] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        args: [issue.evidence_quote, issue.label, issue.category],
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

          const normalize = (value: string) =>
            value.toLowerCase().replace(/\s+/g, " ").trim()

          const normalizedQuote = normalize(evidenceQuote)
          const rawQuote = (evidenceQuote || "").toLowerCase().trim()
          const quoteWords = normalizedQuote
            .split(" ")
            .filter((w) => w.length > 3)
            .slice(0, 16)

          const categoryHints: Record<string, string[]> = {
            unilateral_changes: ["change these terms", "may change", "sole discretion"],
            auto_renewal: ["auto-renew", "renews automatically", "billing cycle"],
            arbitration_waiver: ["binding arbitration", "class action waiver"],
            data_rights: ["license", "third parties", "share", "irrevocable"],
            cancellation_friction: ["non-refundable", "no refunds", "cancel"]
          }

          const hints = (categoryHints[category] || []).map((x) => x.toLowerCase())
          const searchTerms = [...hints, ...quoteWords.map((w) => w.toLowerCase())].slice(0, 20)
          const phraseProbes = [rawQuote, rawQuote.slice(0, 140), rawQuote.slice(0, 90)].filter(
            (x) => x && x.length > 35
          )

          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
          let bestNode: Text | null = null
          let bestScore = 0
          let bestStart = -1
          let bestLen = 0

          while (walker.nextNode()) {
            const node = walker.currentNode as Text
            const raw = node.textContent || ""
            const text = raw.toLowerCase()
            if (!text || text.trim().length < 25) continue

            let score = 0
            let startIndex = -1
            let highlightLen = 0

            for (const probe of phraseProbes) {
              const idx = text.indexOf(probe)
              if (idx !== -1) {
                score += 12
                startIndex = idx
                highlightLen = probe.length
                break
              }
            }

            for (const term of searchTerms) {
              if (!term) continue
              const idx = text.indexOf(term)
              if (idx !== -1) {
                score += term.includes(" ") ? 3 : 1
                if (startIndex === -1) startIndex = idx
              }
            }

            const quoteProbe = normalizedQuote.slice(0, 60).toLowerCase()
            if (quoteProbe && text.includes(quoteProbe)) {
              score += 6
            }

            if (score > bestScore && startIndex !== -1) {
              bestScore = score
              bestNode = node
              bestStart = startIndex
              bestLen = highlightLen
            }
          }

          if (!bestNode || bestScore < 2) return false

          const raw = bestNode.textContent || ""
          const start = Math.max(0, bestStart)
          const end = Math.min(raw.length, start + (bestLen > 0 ? bestLen : 220))
          if (end <= start) return false

          const range = document.createRange()
          range.setStart(bestNode, start)
          range.setEnd(bestNode, end)

          const mark = document.createElement("mark")
          mark.setAttribute(HIGHLIGHT_ATTR, label)
          const highlightColor =
            label.toLowerCase().includes("safe") || category === "safe"
              ? "#22C55E"
              : category === "arbitration_waiver" || category === "auto_renewal"
                ? "#EF4444"
                : "#F59E0B"
          
          mark.style.backgroundColor = `${highlightColor}33`
          mark.style.outline = `2px solid ${highlightColor}`
          mark.style.borderRadius = "4px"
          mark.style.padding = "0 2px"
          mark.style.boxShadow = `0 0 12px ${highlightColor}44`
          mark.style.transition = "all 0.3s ease"

          range.surroundContents(mark)
          mark.scrollIntoView({ behavior: "smooth", block: "center" })
          return true
        }
      })

      if (didHighlight) {
        setActionMessage(`Located: ${issue.label}`)
      }
    } catch (err) {
      // silent fail for highlight
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
          {result?.issues?.map((issue, idx) => (
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
