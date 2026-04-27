from typing import Any

import pytest
from src.schemas import Product, IntentSchema, GiftItem, GiftResponseSchema


@pytest.fixture
def sample_product() -> Product:
    return Product(
        id="PRD001",
        name_en="Test Product",
        name_ar="منتج تجريبي",
        category="toys",
        subcategory="test",
        price_aed=100.0,
        age_range_months_min=0,
        age_range_months_max=12,
        gender="unisex",
        tags=["test", "gift-worthy"],
        description_en="A test product.",
        description_ar="منتج تجريبي.",
        brand="TestBrand",
        in_stock=True,
    )


@pytest.fixture
def sample_catalog() -> list[Product]:
    return [
        Product(
            id=f"PRD{i:03d}",
            name_en=f"Product {i}",
            name_ar=f"منتج {i}",
            category="toys" if i % 2 == 0 else "feeding",
            subcategory="test",
            price_aed=float(50 + i * 10),
            age_range_months_min=0,
            age_range_months_max=24,
            gender="unisex",
            tags=["test"],
            description_en=f"Description {i}",
            description_ar=f"وصف {i}",
            brand="Brand",
            in_stock=True,
        )
        for i in range(1, 6)
    ]


@pytest.fixture
def mock_intent() -> IntentSchema:
    return IntentSchema(
        child_age_months=6,
        budget_aed=200.0,
        occasion="general",
        relationship="friend",
        gender_preference="unisex",
        query_language="en",
        is_parseable=True,
        parse_issues=[],
    )


@pytest.fixture
def mock_env_vars(monkeypatch: Any) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-key")
