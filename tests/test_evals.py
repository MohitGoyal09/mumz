import pytest
from typing import Any

from evals import runner as runner_module
from evals.cases import CASES
from src.schemas import GiftResponseSchema, GiftItem


class TestEvalCases:
    def test_has_12_cases(self) -> None:
        assert len(CASES) >= 12

    def test_cases_have_required_fields(self) -> None:
        for case in CASES:
            assert case.query is not None
            assert case.expected_language in ("en", "ar")
            assert case.min_recommendations >= 0


class TestEvalRunner:
    def test_score_response_passes_correctly(self) -> None:
        from evals.cases import EvalCase
        case = EvalCase(
            query="test",
            expected_language="en",
            should_refuse=False,
            min_recommendations=1,
            description="test",
        )
        response = GiftResponseSchema(
            query_language="en",
            recommendations=[
                GiftItem(
                    product_id="P1",
                    name_en="A",
                    name_ar="ب",
                    price_aed=100.0,
                    reason_en="R",
                    reason_ar="سبب",
                    match_score=0.9,
                )
            ],
            summary_en="S",
            summary_ar="ملخص",
            confidence=0.8,
        )
        scores = runner_module.score_response(response, case)
        assert scores["passed"] is True

    def test_score_response_fails_on_refusal_mismatch(self) -> None:
        from evals.cases import EvalCase
        case = EvalCase(
            query="test",
            expected_language="en",
            should_refuse=True,
            min_recommendations=0,
            description="test",
        )
        response = GiftResponseSchema(
            query_language="en",
            refused=False,
            recommendations=[],
            confidence=0.5,
        )
        scores = runner_module.score_response(response, case)
        assert scores["passed"] is False
        assert scores["refused_correctly"] is False

    def test_run_evals_runs_all_cases(self, monkeypatch: Any) -> None:
        def mock_run_pipeline(query: str) -> GiftResponseSchema:
            return GiftResponseSchema(
                query_language="en",
                refused=False,
                recommendations=[
                    GiftItem(
                        product_id="P1",
                        name_en="A",
                        name_ar="ب",
                        price_aed=100.0,
                        reason_en="R",
                        reason_ar="سبب",
                        match_score=0.9,
                    )
                ],
                summary_en="S",
                summary_ar="ملخص",
                confidence=0.8,
            )

        monkeypatch.setattr(runner_module, "run_pipeline", mock_run_pipeline)
        report = runner_module.run_evals()
        assert report["total"] == len(CASES)
        assert len(report["results"]) == len(CASES)
