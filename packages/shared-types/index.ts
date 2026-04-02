export type RiskSeverity = "red" | "yellow" | "green"

export interface RiskIssue {
  category: string
  label: string
  severity: Exclude<RiskSeverity, "green">
  explanation: string
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
  disclaimer: string
}
