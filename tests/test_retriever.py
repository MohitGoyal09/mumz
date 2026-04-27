import pytest

from src.catalog import build_index
from src.retriever import retrieve_candidates
from src.schemas import IntentSchema


@pytest.fixture(autouse=True)
def ensure_index() -> None:
    build_index()


class TestRetriever:
    def test_retrieve_returns_candidates(self, mock_intent: IntentSchema) -> None:
        candidates = retrieve_candidates(mock_intent, k=10)
        assert isinstance(candidates, list)
        for product, score in candidates:
            assert product.price_aed <= (mock_intent.budget_aed or float("inf"))
            if mock_intent.child_age_months is not None:
                assert product.age_range_months_min <= mock_intent.child_age_months <= product.age_range_months_max

    def test_retrieve_respects_budget(self) -> None:
        intent = IntentSchema(
            budget_aed=100.0,
            query_language="en",
            is_parseable=True,
        )
        candidates = retrieve_candidates(intent, k=20)
        for product, _ in candidates:
            assert product.price_aed <= 100.0

    def test_retrieve_respects_age(self) -> None:
        intent = IntentSchema(
            child_age_months=6,
            query_language="en",
            is_parseable=True,
        )
        candidates = retrieve_candidates(intent, k=20)
        for product, _ in candidates:
            assert product.age_range_months_min <= 6 <= product.age_range_months_max

    def test_retrieve_respects_gender(self) -> None:
        intent = IntentSchema(
            gender_preference="girl",
            query_language="en",
            is_parseable=True,
        )
        candidates = retrieve_candidates(intent, k=20)
        for product, _ in candidates:
            assert product.gender in ("unisex", "girl")
