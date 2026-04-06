import { tr } from "../lib/uiStrings"
import { theme } from "../styles/theme"

export const PopupHeader = () => (
  <div style={{ marginBottom: 20 }}>
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
      <div style={{ 
        width: 10, 
        height: 10, 
        borderRadius: "50%", 
        background: theme.secondary,
        boxShadow: `0 0 8px ${theme.secondary}`
      }} />
      <h2 style={{ 
        margin: 0, 
        fontSize: 18, 
        fontWeight: 700, 
        letterSpacing: "-0.02em",
        color: theme.textPrimary 
      }}>
        FairTerms
      </h2>
    </div>
    <p style={{ 
      margin: 0, 
      color: theme.textMuted, 
      fontSize: 12,
      fontWeight: 500,
      textTransform: "uppercase",
      letterSpacing: "0.05em"
    }}>
      {tr("subtitle")}
    </p>
  </div>
)
