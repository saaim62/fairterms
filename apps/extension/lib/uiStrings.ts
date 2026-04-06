/**
 * Popup UI copy (detection uses API; this is chrome/browser UI language only).
 */

export type UiLocale = "en" | "es" | "de" | "fr"

type Messages = Record<string, string>

const EN: Messages = {
  subtitle: "AI Contract Guardian",
  analyzePage: "Analyze Current Page",
  scanning: "Scanning...",
  safetyRating: "Safety Rating",
  highRisk: "High Risk",
  caution: "Caution",
  secure: "Secure",
  awaitingScan: "Awaiting Scan",
  noRisksTitle: "No Risks Detected",
  noRisksBody: "This document appears to follow standard fair practices.",
  apiFailed: "API Connection Failed",
  noTab: "No active tab found",
  recoverContext: "Recovering stale extension context...",
  locatedPrefix: "Located:",
  locateFailed:
    "Could not locate text on this page (try refreshing the tab, or the viewer may block highlighting).",
  criticalRisk: "Critical Risk",
  warning: "Warning",
  locateInDoc: "Locate in Document",
  noReadableText:
    "No readable text found. For PDFs: enable “Allow access to file URLs” in chrome://extensions for local files, and note some scanned/image-only PDFs do not contain selectable text.",
  footerFallback: "FairTerms AI • v0.1.0"
}

const ES: Messages = {
  ...EN,
  subtitle: "Asistente de contratos IA",
  analyzePage: "Analizar página actual",
  scanning: "Escaneando...",
  safetyRating: "Nivel de seguridad",
  highRisk: "Alto riesgo",
  caution: "Precaución",
  secure: "Seguro",
  awaitingScan: "Esperando escaneo",
  noRisksTitle: "Sin riesgos detectados",
  noRisksBody: "Este documento parece seguir prácticas habituales razonables.",
  apiFailed: "Error de conexión con la API",
  noTab: "No hay pestaña activa",
  recoverContext: "Recuperando contexto de la extensión...",
  locatedPrefix: "Ubicado:",
  locateFailed:
    "No se pudo localizar el texto en esta página (actualice la pestaña o el visor puede bloquear el resaltado).",
  criticalRisk: "Riesgo crítico",
  warning: "Advertencia",
  locateInDoc: "Ubicar en el documento",
  noReadableText:
    "No hay texto legible. Para PDF locales: active “Permitir acceso a URL de archivo” para FairTerms en chrome://extensions. Los PDF escaneados pueden no tener texto seleccionable.",
  footerFallback: "FairTerms IA • v0.1.0"
}

const DE: Messages = {
  ...EN,
  subtitle: "KI-Vertragsassistent",
  analyzePage: "Aktuelle Seite analysieren",
  scanning: "Scanne...",
  safetyRating: "Sicherheit",
  highRisk: "Hohes Risiko",
  caution: "Vorsicht",
  secure: "Unbedenklich",
  awaitingScan: "Warte auf Scan",
  noRisksTitle: "Keine Risiken erkannt",
  noRisksBody: "Dieses Dokument scheint üblichen fairen Praktiken zu entsprechen.",
  apiFailed: "API-Verbindung fehlgeschlagen",
  noTab: "Kein aktiver Tab",
  recoverContext: "Erweiterungskontext wird wiederhergestellt...",
  locatedPrefix: "Gefunden:",
  locateFailed:
    "Text konnte nicht gefunden werden (Tab neu laden oder Viewer blockiert Markierung).",
  criticalRisk: "Kritisches Risiko",
  warning: "Warnung",
  locateInDoc: "Im Dokument suchen",
  noReadableText:
    "Kein lesbarer Text. Für lokale PDFs: „Zugriff auf Datei-URLs“ für FairTerms unter chrome://extensions erlauben. Gescannte PDFs enthalten oft keinen Text.",
  footerFallback: "FairTerms KI • v0.1.0"
}

const FR: Messages = {
  ...EN,
  subtitle: "Assistant contractuel IA",
  analyzePage: "Analyser la page actuelle",
  scanning: "Analyse...",
  safetyRating: "Niveau de sécurité",
  highRisk: "Risque élevé",
  caution: "Prudence",
  secure: "Sûr",
  awaitingScan: "En attente d’analyse",
  noRisksTitle: "Aucun risque détecté",
  noRisksBody: "Ce document semble respecter des pratiques habituelles raisonnables.",
  apiFailed: "Échec de connexion à l’API",
  noTab: "Aucun onglet actif",
  recoverContext: "Récupération du contexte de l’extension...",
  locatedPrefix: "Trouvé :",
  locateFailed:
    "Impossible de localiser le texte (rafraîchissez l’onglet ou le visualiseur bloque la surbrillance).",
  criticalRisk: "Risque critique",
  warning: "Avertissement",
  locateInDoc: "Repérer dans le document",
  noReadableText:
    "Aucun texte lisible. Pour les PDF locaux : autorisez l’accès aux URL de fichier pour FairTerms dans chrome://extensions. Les PDF numérisés peuvent ne pas contenir de texte sélectionnable.",
  footerFallback: "FairTerms IA • v0.1.0"
}

const TABLES: Record<UiLocale, Messages> = {
  en: EN,
  es: ES,
  de: DE,
  fr: FR
}

let _cachedLocale: UiLocale | null = null

export function getUiLocale(): UiLocale {
  if (_cachedLocale) return _cachedLocale
  try {
    const raw =
      typeof chrome !== "undefined" && chrome.i18n?.getUILanguage
        ? chrome.i18n.getUILanguage()
        : typeof navigator !== "undefined"
          ? navigator.language
          : "en"
    const base = (raw || "en").split("-")[0]!.toLowerCase()
    if (base === "es" || base === "de" || base === "fr") {
      _cachedLocale = base
      return base
    }
  } catch {
    /* ignore */
  }
  _cachedLocale = "en"
  return "en"
}

export function tr(key: keyof typeof EN): string {
  const loc = getUiLocale()
  const table = TABLES[loc] ?? EN
  return table[key] ?? EN[key] ?? String(key)
}
