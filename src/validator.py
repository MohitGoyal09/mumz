from src.schemas import IntentSchema, GiftResponseSchema

_MIN_BUDGET_AED = 30.0
_MAX_BUDGET_AED = 5000.0
_MAX_AGE_MONTHS = 216


def validate_intent(intent: IntentSchema) -> GiftResponseSchema | None:
    issues: list[str] = []
    issues_ar: list[str] = []

    if intent.is_parseable is False:
        issues.append("We couldn't understand your request clearly.")
        issues_ar.append("لم نتمكن من فهم طلبك بوضوح.")

    if intent.budget_aed is not None and intent.budget_aed > _MAX_BUDGET_AED:
        issues.append(f"Budget exceeds maximum of {_MAX_BUDGET_AED} AED.")
        issues_ar.append(f"الميزانية تتجاوز الحد الأقصى {_MAX_BUDGET_AED} درهم.")

    if intent.budget_aed is not None and intent.budget_aed < _MIN_BUDGET_AED:
        issues.append(f"Budget is below minimum of {_MIN_BUDGET_AED} AED.")
        issues_ar.append(f"الميزانية أقل من الحد الأدنى {_MIN_BUDGET_AED} درهم.")

    if intent.child_age_months is not None and intent.child_age_months > _MAX_AGE_MONTHS:
        issues.append(f"Age exceeds supported range (up to {_MAX_AGE_MONTHS} months).")
        issues_ar.append(f"العمر يتجاوز النطاق المدعوم (حتى {_MAX_AGE_MONTHS} شهراً).")

    if issues:
        return GiftResponseSchema(
            query_language=intent.query_language,
            refused=True,
            refusal_reason=" ".join(issues),
            refusal_reason_ar=" ".join(issues_ar),
            confidence=0.0,
        )

    return None
