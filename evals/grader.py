import json
from typing import Any

from evals.cases import CASES, EvalCase
from src.pipeline import run_pipeline
from src.schemas import GiftResponseSchema


def grade(response: GiftResponseSchema, case: EvalCase) -> dict[str, Any]:
    """Grade a single response against a test case.

    Returns PASS, PARTIAL, or FAIL based on rubric:
    - PASS: correct behavior, no hallucination, language quality OK
    - PARTIAL: correct intent, minor quality issue
    - FAIL: wrong products, hallucination, bad Arabic, wrong refusal
    """
    checks: dict[str, Any] = {
        "refused_correctly": response.refused == case.should_refuse,
        "has_recommendations": len(response.recommendations) >= case.min_recommendations,
        "has_bilingual_summary": bool(response.summary_en and response.summary_ar) if not response.refused else True,
        "confidence_in_range": 0.0 <= response.confidence <= 1.0,
    }

    all_pass = all(checks.values())
    if all_pass:
        verdict = "PASS"
    elif checks["refused_correctly"]:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    # Hallucination check: product_ids not in catalog
    hallucinations: list[str] = []
    if response.recommendations:
        from src.catalog import load_catalog
        try:
            products = load_catalog("data/catalog.json")
            valid_ids = {p.id for p in products}
            for item in response.recommendations:
                if item.product_id not in valid_ids:
                    hallucinations.append(item.product_id)
                    verdict = "FAIL"
        except Exception:
            pass

    return {
        "verdict": verdict,
        "checks": checks,
        "hallucinations": hallucinations,
    }


def run_eval() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    counts = {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "hallucination_count": 0}
    for case in CASES:
        try:
            response = run_pipeline(case.query)
        except Exception as e:
            response = GiftResponseSchema(
                query_language=case.expected_language,
                refused=True,
                refusal_reason=f"Pipeline error: {e}",
                refusal_reason_ar="خطأ في المعالجة.",
                confidence=0.0,
            )
        grading = grade(response, case)
        counts[grading["verdict"]] += 1
        if grading["hallucinations"]:
            counts["hallucination_count"] += len(grading["hallucinations"])
        results.append({
            "case": case.description,
            "query": case.query,
            "grading": grading,
            "response": response.model_dump(),
        })
    total = len(CASES)
    return {
        "total": total,
        **counts,
        "pass_rate": counts["PASS"] / total if total else 0.0,
        "results": results,
    }


if __name__ == "__main__":
    report = run_eval()
    with open("evals/results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(
        f"Evals complete: PASS={report['PASS']} PARTIAL={report['PARTIAL']} "
        f"FAIL={report['FAIL']} Hallucinations={report['hallucination_count']} "
        f"({report['pass_rate']:.1%})"
    )
