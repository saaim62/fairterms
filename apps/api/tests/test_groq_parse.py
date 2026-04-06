"""Tests for Groq response parsing and validation utilities."""

from services.groq_analyze import (
    _evidence_in_excerpt,
    _groq_payload_too_large,
    _strip_outer_quotes,
    _truncate,
    normalize_llm_category,
)


class TestTruncate:
    def test_short_text_unchanged(self):
        assert _truncate("hello", 100) == "hello"

    def test_long_text_truncated(self):
        text = "a" * 200
        result = _truncate(text, 100)
        assert len(result) <= 100
        assert "[truncated]" in result

    def test_empty_text(self):
        assert _truncate("", 100) == ""
        assert _truncate(None, 100) == ""


class TestStripOuterQuotes:
    def test_double_quotes(self):
        assert _strip_outer_quotes('"hello world"') == "hello world"

    def test_single_quotes(self):
        assert _strip_outer_quotes("'hello world'") == "hello world"

    def test_curly_quotes(self):
        assert _strip_outer_quotes("\u201chello\u201d") == "hello"

    def test_no_quotes(self):
        assert _strip_outer_quotes("hello world") == "hello world"

    def test_nested_quotes(self):
        assert _strip_outer_quotes('""nested""') == "nested"


class TestEvidenceInExcerpt:
    def test_exact_match(self):
        assert _evidence_in_excerpt("binding arbitration", "You agree to binding arbitration.") == "binding arbitration"

    def test_not_found(self):
        assert _evidence_in_excerpt("nonexistent text", "Some other text here.") is None

    def test_with_quotes(self):
        assert _evidence_in_excerpt('"binding arbitration"', "You agree to binding arbitration.") == "binding arbitration"

    def test_empty_quote(self):
        assert _evidence_in_excerpt("", "Some text") is None

    def test_typographic_normalization(self):
        result = _evidence_in_excerpt("test\u2014value", "test-value in context")
        assert result is not None


class TestNormalizeLlmCategory:
    def test_canonical_keys(self):
        assert normalize_llm_category("arbitration_waiver") == "arbitration_waiver"
        assert normalize_llm_category("Auto_Renewal") == "auto_renewal"

    def test_dynamic_snake_case(self):
        assert normalize_llm_category("mandatory_insurance_bundle") == "mandatory_insurance_bundle"
        assert normalize_llm_category("opaque fee stacking") == "opaque_fee_stacking"

    def test_rejects_invalid(self):
        assert normalize_llm_category("") is None
        assert normalize_llm_category("Bad-Category") is None
        assert normalize_llm_category("ab") is None
        assert normalize_llm_category("has__double") is None
        assert normalize_llm_category("123start") is None


class TestPayloadTooLarge:
    def test_413_status(self):
        class FakeExc(Exception):
            status_code = 413
        assert _groq_payload_too_large(FakeExc("too large"))

    def test_413_in_message(self):
        assert _groq_payload_too_large(Exception("Error code: 413 - Request too large"))

    def test_rate_limit_tpm(self):
        assert _groq_payload_too_large(Exception("rate_limit_exceeded on tokens per minute TPM"))

    def test_normal_error(self):
        assert not _groq_payload_too_large(Exception("Connection refused"))
