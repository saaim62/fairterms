from dataclasses import dataclass


@dataclass
class EngineConfig:
    model: str = "rules-only"


class FairTermsEngine:
    def __init__(self, config: EngineConfig | None = None) -> None:
        self.config = config or EngineConfig()

    def analyze(self, text: str) -> dict:
        return {
            "signal": "green",
            "issues": [],
            "note": "Engine package scaffolded; wire model pipeline in week 2.",
            "text_length": len(text or ""),
        }
