from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Product(BaseModel):
    id: str
    name_en: str
    name_ar: str
    category: str
    subcategory: str
    price_aed: float = Field(..., ge=0)
    age_range_months_min: int = Field(..., ge=0)
    age_range_months_max: int = Field(..., ge=0)
    gender: Literal["unisex", "boy", "girl"]
    tags: list[str]
    description_en: str
    description_ar: str
    brand: str
    in_stock: bool

    @field_validator("age_range_months_max")
    @classmethod
    def max_age_gte_min_age(cls, v: int, info) -> int:
        if "age_range_months_min" in info.data and v < info.data["age_range_months_min"]:
            raise ValueError("age_range_months_max must be >= age_range_months_min")
        return v


class IntentSchema(BaseModel):
    child_age_months: Optional[int] = Field(None, ge=0)
    budget_aed: Optional[float] = Field(None, ge=0)
    occasion: Optional[str] = None
    relationship: Optional[str] = None
    gender_preference: Optional[Literal["boy", "girl", "unisex"]] = None
    query_language: Literal["en", "ar"] = "en"
    is_parseable: bool = True
    parse_issues: list[str] = Field(default_factory=list)


class GiftItem(BaseModel):
    product_id: str
    name_en: str
    name_ar: str
    price_aed: float
    reason_en: str
    reason_ar: str
    match_score: float = Field(..., ge=0.0, le=1.0)


class GiftResponseSchema(BaseModel):
    query_language: Literal["en", "ar"] = "en"
    recommendations: list[GiftItem] = Field(default_factory=list)
    summary_en: str = ""
    summary_ar: str = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    refused: bool = False
    refusal_reason: Optional[str] = None
    refusal_reason_ar: Optional[str] = None
