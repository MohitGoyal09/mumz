import pytest

from src.language import detect_language


class TestLanguageDetection:
    def test_detects_english(self) -> None:
        assert detect_language("I need a gift for a 6-month-old baby") == "en"

    def test_detects_arabic(self) -> None:
        assert detect_language("أحتاج هدية لطفل عمره 6 أشهر") == "ar"

    def test_fallback_to_english_on_error(self) -> None:
        assert detect_language("") == "en"
