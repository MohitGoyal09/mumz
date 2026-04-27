from src.catalog import search_index
from src.schemas import IntentSchema, Product


def retrieve_candidates(intent: IntentSchema, k: int = 20) -> list[tuple[Product, float]]:
    from src.catalog import get_product_by_id

    query_parts: list[str] = []
    if intent.occasion:
        query_parts.append(intent.occasion)
    if intent.relationship:
        query_parts.append(intent.relationship)
    if intent.gender_preference:
        query_parts.append(intent.gender_preference)
    if intent.child_age_months is not None:
        query_parts.append(f"age {intent.child_age_months} months")
    query = " ".join(query_parts) if query_parts else "baby gift"

    results = search_index(query, k=k)
    candidates: list[tuple[Product, float]] = []
    for product_id, score in results:
        product = get_product_by_id(product_id)
        if product is None:
            continue
        if intent.budget_aed is not None and product.price_aed > intent.budget_aed:
            continue
        if intent.child_age_months is not None:
            if not (product.age_range_months_min <= intent.child_age_months <= product.age_range_months_max):
                continue
        if intent.gender_preference is not None and intent.gender_preference != "unisex":
            if product.gender != "unisex" and product.gender != intent.gender_preference:
                continue
        candidates.append((product, score))
    return candidates
