import json
from typing import Any

from src.intent_parser import call_openrouter
from src.schemas import IntentSchema, Product, GiftItem, GiftResponseSchema


def _system_prompt() -> str:
    return (
        "You are a baby-product gift recommender for Mumzworld. "
        "Given a user's intent and candidate products, select the top 3 best matches. "
        "For each, explain WHY it matches in 1 sentence (English and Arabic). "
        "CRITICAL: Use the EXACT product_id from the candidate list (e.g., PRD001, PRD042). Do NOT shorten or modify IDs. "
        "Return strictly as JSON."
    )


def _user_prompt(intent: IntentSchema, candidates: list[tuple[Product, float]]) -> str:
    lines = [
        f"Intent: age={intent.child_age_months}mo, budget={intent.budget_aed}AED, "
        f"occasion={intent.occasion}, relationship={intent.relationship}, "
        f"gender={intent.gender_preference}, lang={intent.query_language}",
        "",
        "Candidates:",
    ]
    for idx, (product, score) in enumerate(candidates[:10], 1):
        lines.append(
            f"{idx}. {product.id} | {product.name_en} | {product.name_ar} | "
            f"{product.price_aed}AED | age {product.age_range_months_min}-{product.age_range_months_max}mo | "
            f"gender={product.gender} | tags={product.tags} | score={score:.3f}"
        )
    lines.extend([
        "",
        "Return JSON with:",
        "- recommendations: list of {product_id, name_en, name_ar, price_aed, reason_en, reason_ar, match_score}",
        "- summary_en: string",
        "- summary_ar: string",
        "- confidence: float 0-1",
    ])
    return "\n".join(lines)


def recommend(
    intent: IntentSchema,
    candidates: list[tuple[Product, float]],
) -> GiftResponseSchema:
    if not candidates:
        return GiftResponseSchema(
            query_language=intent.query_language,
            refused=False,
            recommendations=[],
            summary_en="No matching products found.",
            summary_ar="لم يتم العثور على منتجات مطابقة.",
            confidence=0.0,
        )

    try:
        response = call_openrouter(
            messages=[
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": _user_prompt(intent, candidates)},
            ],
            response_format={"type": "json_object"},
            max_tokens=2048,
        )
        content = response["choices"][0]["message"]["content"]
        data = json.loads(content)
        items = [GiftItem(**item) for item in data.get("recommendations", [])]
        return GiftResponseSchema(
            query_language=intent.query_language,
            recommendations=items,
            summary_en=data.get("summary_en", ""),
            summary_ar=data.get("summary_ar", ""),
            confidence=data.get("confidence", 0.5),
        )
    except Exception as e:
        return GiftResponseSchema(
            query_language=intent.query_language,
            refused=False,
            recommendations=[],
            summary_en=f"Recommendation generation failed: {e}",
            summary_ar="فشل في توليد التوصيات.",
            confidence=0.0,
        )
