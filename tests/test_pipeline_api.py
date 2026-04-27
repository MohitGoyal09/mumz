from typing import Any

import pytest
from fastapi.testclient import TestClient

import api.main as api_main
from src import pipeline as pipeline_module
from src.schemas import GiftResponseSchema, GiftItem
from api.main import app


client = TestClient(app)


class TestPipeline:
    def test_pipeline_refuses_invalid_budget(self, monkeypatch: Any) -> None:
        def mock_parse(*args, **kwargs):
            from src.schemas import IntentSchema
            return IntentSchema(
                budget_aed=10000.0,
                query_language="en",
                is_parseable=True,
            )

        monkeypatch.setattr(pipeline_module, "parse_intent", mock_parse)
        result = pipeline_module.run_pipeline("expensive gift")
        assert result.refused is True

    def test_pipeline_returns_recommendations(self, monkeypatch: Any) -> None:
        def mock_parse(*args, **kwargs):
            from src.schemas import IntentSchema
            return IntentSchema(
                child_age_months=6,
                budget_aed=500.0,
                query_language="en",
                is_parseable=True,
            )

        def mock_recommend(*args, **kwargs):
            return GiftResponseSchema(
                query_language="en",
                recommendations=[
                    GiftItem(
                        product_id="PRD001",
                        name_en="Test",
                        name_ar="اختبار",
                        price_aed=100.0,
                        reason_en="Good match",
                        reason_ar="مطابق جيد",
                        match_score=0.9,
                    )
                ],
                summary_en="Top pick",
                summary_ar="الاختيار الأفضل",
                confidence=0.9,
            )

        monkeypatch.setattr(pipeline_module, "parse_intent", mock_parse)
        monkeypatch.setattr(pipeline_module, "recommend", mock_recommend)
        result = pipeline_module.run_pipeline("gift for 6 month old")
        assert result.refused is False
        assert len(result.recommendations) == 1


class TestAPI:
    def test_health(self) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_recommend_refuses_bad_budget(self, monkeypatch: Any) -> None:
        def mock_run(*args, **kwargs):
            return GiftResponseSchema(
                query_language="en",
                refused=True,
                refusal_reason="Budget too high",
                refusal_reason_ar="الميزانية مرتفعة جداً",
                confidence=0.0,
            )

        monkeypatch.setattr(api_main, "run_pipeline", mock_run)
        resp = client.post("/recommend", json={"query": "expensive"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["refused"] is True

    def test_recommend_returns_gifts(self, monkeypatch: Any) -> None:
        def mock_run(*args, **kwargs):
            return GiftResponseSchema(
                query_language="en",
                recommendations=[
                    GiftItem(
                        product_id="PRD001",
                        name_en="Bottle",
                        name_ar="زجاجة",
                        price_aed=100.0,
                        reason_en="Great for babies",
                        reason_ar="ممتاز للأطفال",
                        match_score=0.95,
                    )
                ],
                summary_en="Here is our top pick",
                summary_ar="إليك اختيارنا الأفضل",
                confidence=0.9,
            )

        monkeypatch.setattr(api_main, "run_pipeline", mock_run)
        resp = client.post("/recommend", json={"query": "bottle for newborn"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["product_id"] == "PRD001"
