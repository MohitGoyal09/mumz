import pytest

from src.validator import validate_intent
from src.schemas import IntentSchema, GiftResponseSchema


class TestValidator:
    def test_valid_intent_returns_none(self, mock_intent: IntentSchema) -> None:
        result = validate_intent(mock_intent)
        assert result is None

    def test_unparseable_intent_refused(self) -> None:
        intent = IntentSchema(
            is_parseable=False,
            parse_issues=["missing age"],
            query_language="en",
        )
        result = validate_intent(intent)
        assert isinstance(result, GiftResponseSchema)
        assert result.refused is True
        assert result.refusal_reason is not None

    def test_budget_too_high_refused(self) -> None:
        intent = IntentSchema(
            budget_aed=10000.0,
            query_language="en",
            is_parseable=True,
        )
        result = validate_intent(intent)
        assert result is not None
        assert result.refused is True
        assert "exceeds" in (result.refusal_reason or "").lower()

    def test_budget_too_low_refused(self) -> None:
        intent = IntentSchema(
            budget_aed=10.0,
            query_language="en",
            is_parseable=True,
        )
        result = validate_intent(intent)
        assert result is not None
        assert result.refused is True

    def test_age_too_high_refused(self) -> None:
        intent = IntentSchema(
            child_age_months=300,
            query_language="en",
            is_parseable=True,
        )
        result = validate_intent(intent)
        assert result is not None
        assert result.refused is True
