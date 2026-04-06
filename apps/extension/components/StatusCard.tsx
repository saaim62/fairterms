import type { RiskSeverity } from "../../../packages/shared-types"
import { tr } from "../lib/uiStrings"
import { theme } from "../styles/theme"

interface StatusCardProps {
  signal?: RiskSeverity
  label: string
}

const signalColor: Record<RiskSeverity, string> = {
  red: theme.danger,
  yellow: theme.accent,
  green: theme.success
}

export const StatusCard = ({ signal, label }: StatusCardProps) => (
  <div
    style={{
      marginTop: 16,
      padding: "12px 16px",
      borderRadius: 12,
      background: theme.panel,
      backdropFilter: theme.glass,
      WebkitBackdropFilter: theme.glass,
      border: `1px solid ${theme.border}`,
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between"
    }}>
    <span style={{ color: theme.textMuted, fontSize: 13, fontWeight: 500 }}>{tr("safetyRating")}</span>
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div style={{ 
        width: 8, 
        height: 8, 
        borderRadius: "50%", 
        background: signal ? signalColor[signal] : theme.textMuted,
        boxShadow: signal ? `0 0 8px ${signalColor[signal]}` : "none"
      }} />
      <span style={{ 
        color: signal ? signalColor[signal] : theme.textMuted,
        fontSize: 14,
        fontWeight: 700,
        textTransform: "uppercase"
      }}>
        {label}
      </span>
    </div>
  </div>
)
