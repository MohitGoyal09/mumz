import pytest
from pydantic import ValidationError

from src.schemas import Product, IntentSchema, GiftItem, GiftResponseSchema


class TestProduct:
    def test_valid_product(self, sample_product: Product) -> None:
        assert sample_product.id == "PRD001"
        assert sample_product.price_aed == 100.0
        assert sample_product.gender == "unisex"

    def test_negative_price_raises(self) -> None:
        with pytest.raises(ValidationError):
            Product(
                id="BAD",
                name_en="Bad",
                name_ar="",
                category="test",
                subcategory="test",
                price_aed=-10.0,
                age_range_months_min=0,
                age_range_months_max=12,
                gender="unisex",
                tags=[],
                description_en="",
                description_ar="",
                brand="",
                in_stock=True,
            )

    def test_age_max_lt_min_raises(self) -> None:
        with pytest.raises(ValidationError):
            Product(
                id="BAD",
                name_en="Bad",
                name_ar="",
                category="test",
                subcategory="test",
                price_aed=10.0,
                age_range_months_min=12,
                age_range_months_max=6,
                gender="unisex",
                tags=[],
                description_en="",
                description_ar="",
                brand="",
                in_stock=True,
            )


class TestIntentSchema:
    def test_valid_intent(self, mock_intent: IntentSchema) -> None:
        assert mock_intent.child_age_months == 6
        assert mock_intent.budget_aed == 200.0
        assert mock_intent.query_language == "en"
        assert mock_intent.is_parseable is True

    def test_unparseable_intent(self) -> None:
        intent = IntentSchema(
            child_age_months=None,
            budget_aed=None,
            is_parseable=False,
            parse_issues=["missing age", "missing budget"],
        )
        assert intent.is_parseable is False
        assert len(intent.parse_issues) == 2


class TestGiftItem:
    def test_valid_gift_item(self) -> None:
        item = GiftItem(
            product_id="PRD001",
            name_en="Toy",
            name_ar="لعبة",
            price_aed=100.0,
            reason_en="Great for babies",
            reason_ar="ممتاز للأطفال",
            match_score=0.95,
        )
        assert item.match_score == 0.95

    def test_match_score_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            GiftItem(
                product_id="PRD001",
                name_en="Toy",
                name_ar="لعبة",
                price_aed=100.0,
                reason_en="Great for babies",
                reason_ar="ممتاز للأطفال",
                match_score=1.5,
            )


class TestGiftResponseSchema:
    def test_valid_response_with_recommendations(self) -> None:
        items = [
            GiftItem(
                product_id=f"PRD{i}",
                name_en=f"Item {i}",
                name_ar=f"عنصر {i}",
                price_aed=50.0 * i,
                reason_en=f"Reason {i}",
                reason_ar=f"سبب {i}",
                match_score=0.9 - i * 0.05,
            )
            for i in range(1, 4)
        ]
        response = GiftResponseSchema(
            query_language="en",
            recommendations=items,
            summary_en="Here are top picks",
            summary_ar="إليك أفضل الاختيارات",
            confidence=0.92,
        )
        assert len(response.recommendations) == 3
        assert response.refused is False

    def test_refused_response(self) -> None:
        response = GiftResponseSchema(
            query_language="en",
            refused=True,
            refusal_reason="We couldn't understand your request.",
            refusal_reason_ar="لم نتمكن من فهم طلبك.",
            confidence=0.0,
        )
        assert response.refused is True
        assert response.refusal_reason is not None
        assert response.refusal_reason_ar is not None
