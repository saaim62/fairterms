import { tr } from "../lib/uiStrings"
import { theme } from "../styles/theme"

interface AnalyzeButtonProps {
  loading: boolean
  onClick: () => void
}

export const AnalyzeButton = ({ loading, onClick }: AnalyzeButtonProps) => (
  <button
    onClick={onClick}
    disabled={loading}
    style={{
      width: "100%",
      padding: "12px 16px",
      border: `1px solid rgba(34, 211, 238, 0.3)`,
      borderRadius: 12,
      color: "#ffffff",
      fontSize: 14,
      fontWeight: 600,
      background: loading
        ? "rgba(30, 41, 59, 0.5)"
        : `linear-gradient(135deg, ${theme.primary} 0%, ${theme.secondary} 100%)`,
      boxShadow: loading ? "none" : "0 4px 12px rgba(37, 99, 235, 0.2)",
      cursor: loading ? "not-allowed" : "pointer",
      transition: "all 0.2s ease",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: 8
    }}>
    {loading ? (
      <>
        <div className="spinner" style={{
          width: 14,
          height: 14,
          border: "2px solid rgba(255,255,255,0.3)",
          borderTop: "2px solid white",
          borderRadius: "50%",
          animation: "spin 0.8s linear infinite"
        }} />
        <span>{tr("scanning")}</span>
      </>
    ) : (
      tr("analyzePage")
    )}
    <style>{`
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
    `}</style>
  </button>
)
