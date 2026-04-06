export type RiskSeverity = "red" | "yellow" | "green"

export interface RiskIssue {
  category: string
  label: string
  severity: Exclude<RiskSeverity, "green">
  explanation: string
  /**
   * Relative strength for sorting and UI (rule hits use fixed tiers; Groq uses model output).
   * Not a calibrated statistical probability.
   */
  confidence: number
  evidence_quote: string
}

export interface AnalyzeResponse {
  signal: RiskSeverity
  source_url?: string | null
  issue_count: number
  issues: RiskIssue[]
  /** "rules" | "rules+groq" when Groq API key is configured */
  analysis_source?: string
  /** ISO 639-1 hint from langdetect when enabled (es/de/fr), else omitted */
  document_language?: string | null
  /** Pattern banks applied: always includes "en"; may include es/de/fr */
  rule_locales_used?: string[]
  disclaimer: string
}
