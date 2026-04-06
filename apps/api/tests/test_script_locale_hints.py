"""Tests for Unicode script-based locale detection."""

from services.script_locale_hints import script_locale_hints


class TestScriptLocaleHints:
    def test_chinese_text(self):
        text = "腾讯有权修改本协议条款并以适当方式提醒用户"
        hints = script_locale_hints(text)
        assert "zh" in hints

    def test_japanese_text(self):
        text = "この利用規約は変更される場合があります。サービスの利用を継続する"
        hints = script_locale_hints(text)
        assert "ja" in hints

    def test_korean_text(self):
        text = "본 약관은 회사가 필요한 경우 변경할 수 있으며 계속 이용하는 경우 동의"
        hints = script_locale_hints(text)
        assert "ko" in hints

    def test_thai_text(self):
        text = "ข้อกำหนดเหล่านี้อาจมีการเปลี่ยนแปลงได้โดยไม่ต้องแจ้งให้ทราบล่วงหน้า"
        hints = script_locale_hints(text)
        assert "th" in hints

    def test_arabic_text(self):
        text = "يحق لنا تعديل شروط الاستخدام في أي وقت دون إشعار مسبق"
        hints = script_locale_hints(text)
        assert "ar" in hints
        assert "fa" in hints
        assert "ur" in hints

    def test_cyrillic_text(self):
        text = "Мы оставляем за собой право изменять условия использования"
        hints = script_locale_hints(text)
        assert "ru" in hints
        assert "uk" in hints

    def test_hindi_devanagari(self):
        text = "हम बिना सूचना के नियमों में परिवर्तन कर सकते हैं"
        hints = script_locale_hints(text)
        assert "hi" in hints

    def test_bengali_text(self):
        text = "আমরা যেকোনো সময় শর্তাবলী পরিবর্তন করতে পারি"
        hints = script_locale_hints(text)
        assert "bn" in hints

    def test_latin_returns_empty(self):
        text = "This is a normal English terms of service document."
        hints = script_locale_hints(text)
        assert hints == []

    def test_short_text_returns_empty(self):
        hints = script_locale_hints("短い")
        assert hints == []

    def test_single_pass_performance(self):
        """Verify it handles large text without issues."""
        text = "腾讯有权修改本协议。" * 5000
        hints = script_locale_hints(text)
        assert "zh" in hints
