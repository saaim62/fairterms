import type { RiskIssue } from "../../../packages/shared-types"
import { theme } from "../styles/theme"

interface IssueCardProps {
  issue: RiskIssue
  onShowOnPage: (issue: RiskIssue) => void
}

export const IssueCard = ({ issue, onShowOnPage }: IssueCardProps) => (
  <div
    style={{
      border: `1px solid ${theme.border}`,
      borderLeft: `4px solid ${issue.severity === "red" ? theme.danger : theme.accent}`,
      borderRadius: 12,
      padding: 14,
      background: theme.card,
      backdropFilter: theme.glass,
      WebkitBackdropFilter: theme.glass,
      transition: "transform 0.2s ease",
      cursor: "default"
    }}>
    <div style={{ marginBottom: 8 }}>
      <span style={{ 
        fontSize: 10, 
        fontWeight: 700, 
        textTransform: "uppercase", 
        color: issue.severity === "red" ? theme.danger : theme.accent,
        background: issue.severity === "red" ? "rgba(239, 68, 68, 0.1)" : "rgba(245, 158, 11, 0.1)",
        padding: "2px 6px",
        borderRadius: 4,
        letterSpacing: "0.02em"
      }}>
        {issue.severity === "red" ? "Critical Risk" : "Warning"}
      </span>
    </div>
    <strong style={{ 
      color: theme.textPrimary, 
      fontSize: 14, 
      display: "block",
      marginBottom: 4 
    }}>
      {issue.label}
    </strong>
    <p style={{ 
      margin: "0 0 12px 0", 
      fontSize: 12, 
      lineHeight: "1.5",
      color: theme.textMuted 
    }}>
      {issue.explanation}
    </p>
    
    <div style={{ 
      background: "rgba(15, 23, 42, 0.3)", 
      padding: 8, 
      borderRadius: 6, 
      fontSize: 11, 
      color: theme.textMuted,
      fontStyle: "italic",
      marginBottom: 12,
      border: "1px solid rgba(255,255,255,0.05)"
    }}>
      {issue.evidence_quote.length > 100
        ? issue.evidence_quote.slice(0, 100) + "..."
        : issue.evidence_quote}
    </div>

    <button
      onClick={() => onShowOnPage(issue)}
      style={{
        width: "100%",
        border: `1px solid ${theme.secondary}44`,
        borderRadius: 8,
        background: "rgba(34, 211, 238, 0.05)",
        color: theme.secondary,
        padding: "8px 12px",
        fontSize: 12,
        fontWeight: 600,
        cursor: "pointer",
        transition: "all 0.2s ease"
      }}>
      Locate in Document
    </button>
  </div>
)
