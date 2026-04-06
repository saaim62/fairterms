"""Tests for the rule-based analyzer."""

import os
import pytest


@pytest.fixture(autouse=True)
def _no_groq(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


def _analyze(text: str) -> dict:
    from services.analyzer import analyze_contract_text
    return analyze_contract_text(text)


class TestEnglishRules:
    def test_arbitration_detected(self):
        result = _analyze("You agree to binding arbitration and waive your right to a jury trial.")
        cats = {i["category"] for i in result["issues"]}
        assert "arbitration_waiver" in cats

    def test_auto_renewal_detected(self):
        result = _analyze("Your subscription will auto-renew each year unless you cancel before the next billing period.")
        cats = {i["category"] for i in result["issues"]}
        assert "auto_renewal" in cats

    def test_data_selling_detected(self):
        result = _analyze("We may sell your personal data to third parties for marketing purposes.")
        cats = {i["category"] for i in result["issues"]}
        assert "data_selling" in cats

    def test_green_signal_for_clean_text(self):
        result = _analyze("Welcome to our service. We respect your privacy and rights.")
        assert result["signal"] == "green"
        assert result["issue_count"] == 0

    def test_red_signal_present(self):
        result = _analyze("By using this service you agree to binding arbitration.")
        assert result["signal"] == "red"

    def test_evidence_quote_present(self):
        result = _analyze("We may sell your personal information to advertisers.")
        for issue in result["issues"]:
            assert issue["evidence_quote"], f"Missing quote for {issue['category']}"

    def test_response_shape(self):
        result = _analyze("Some normal text about our terms of service.")
        assert "signal" in result
        assert "issues" in result
        assert "analysis_source" in result
        assert "disclaimer" in result
        assert "rule_locales_used" in result
        assert result["analysis_source"] == "rules"

    def test_limitation_of_liability(self):
        result = _analyze("Our limitation of liability shall not exceed the total amount paid.")
        cats = {i["category"] for i in result["issues"]}
        assert "limitation_of_liability" in cats

    def test_as_is_disclaimer(self):
        result = _analyze("The service is provided as is without warranty of any kind.")
        cats = {i["category"] for i in result["issues"]}
        assert "disclaimer_of_warranties" in cats


class TestChineseRules:
    def test_chinese_unilateral_changes(self):
        result = _analyze("腾讯有权在必要时修改本协议条款，用户继续使用即视为同意。" * 2)
        cats = {i["category"] for i in result["issues"]}
        assert "unilateral_changes" in cats
        assert result.get("document_language") == "zh"

    def test_chinese_arbitration(self):
        result = _analyze("如有争议应提交仲裁解决，不得提起集体诉讼。" * 2)
        cats = {i["category"] for i in result["issues"]}
        assert "arbitration_waiver" in cats

    def test_chinese_disclaimer(self):
        result = _analyze("本公司不对服务的可用性作出任何保证，按现状提供。" * 2)
        cats = {i["category"] for i in result["issues"]}
        assert "disclaimer_of_warranties" in cats


class TestMultiLanguageDetection:
    def test_thai_script_detected(self):
        result = _analyze("ข้อกำหนดนี้อาจมีการแก้ไขได้โดยไม่ต้องแจ้งล่วงหน้า การใช้งานต่อเนื่องถือว่ายอมรับ " * 3)
        assert result.get("document_language") == "th"
        assert len(result["issues"]) > 0

    def test_korean_detected(self):
        result = _analyze("약관은 당사가 언제든지 변경할 수 있으며 계속 이용 시 동의한 것으로 간주됩니다 " * 3)
        assert result.get("document_language") == "ko"

    def test_hindi_detected(self):
        result = _analyze("हम बिना सूचना के नियमों में परिवर्तन कर सकते हैं। व्यक्तिगत डेटा साझा किया जा सकता है। " * 3)
        assert result.get("document_language") == "hi"


class TestGroqMergeSemantic:
    """LLM-only snake_case categories outside the fixed taxonomy must merge in (rules still win on canonical keys)."""

    def test_semantic_llm_issue_merged(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")

        def fake_groq(_text: str):
            return [
                {
                    "category": "mandatory_insurance_add_on",
                    "label": "Forced add-on insurance",
                    "severity": "yellow",
                    "explanation": "User must buy bundled insurance.",
                    "confidence": 0.72,
                    "evidence_quote": "You must purchase our partner insurance to use the service.",
                }
            ]

        monkeypatch.setattr("services.analyzer.analyze_with_groq", fake_groq)
        from services.analyzer import analyze_contract_text

        text = "Welcome. You must purchase our partner insurance to use the service. Thanks."
        result = analyze_contract_text(text)
        cats = [i["category"] for i in result["issues"]]
        assert "mandatory_insurance_add_on" in cats
        assert result["analysis_source"] == "rules+groq"

    def test_rules_win_over_groq_same_canonical_category(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")

        def fake_groq(_text: str):
            return [
                {
                    "category": "arbitration_waiver",
                    "label": "AI label",
                    "severity": "red",
                    "explanation": "AI explanation",
                    "confidence": 0.99,
                    "evidence_quote": "You agree to binding arbitration.",
                }
            ]

        monkeypatch.setattr("services.analyzer.analyze_with_groq", fake_groq)
        from services.analyzer import analyze_contract_text

        result = analyze_contract_text("You agree to binding arbitration.")
        arb = [i for i in result["issues"] if i["category"] == "arbitration_waiver"]
        assert len(arb) == 1
        from services.category_registry import get_label

        assert arb[0]["label"] == get_label("arbitration_waiver")


class TestSignalLogic:
    def test_red_overrides_yellow(self):
        text = (
            "You agree to binding arbitration. "
            "Your subscription will auto-renew each year."
        )
        result = _analyze(text)
        assert result["signal"] == "red"

    def test_issue_count_matches(self):
        result = _analyze("We provide binding arbitration and sell your personal data to third parties.")
        assert result["issue_count"] == len(result["issues"])
