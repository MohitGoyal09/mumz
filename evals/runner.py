import json
from typing import Any

from evals.cases import CASES, EvalCase
from src.pipeline import run_pipeline
from src.schemas import GiftResponseSchema


def score_response(response: GiftResponseSchema, case: EvalCase) -> dict[str, Any]:
    scores: dict[str, Any] = {
        "refused_correctly": response.refused == case.should_refuse,
        "has_recommendations": len(response.recommendations) >= case.min_recommendations,
        "has_bilingual_summary": bool(response.summary_en and response.summary_ar),
        "confidence_in_range": 0.0 <= response.confidence <= 1.0,
    }
    scores["passed"] = all(scores.values())
    return scores


def run_evals() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    passed = 0
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
        scores = score_response(response, case)
        if scores["passed"]:
            passed += 1
        results.append({
            "case": case.description,
            "query": case.query,
            "scores": scores,
            "response": response.model_dump(),
        })
    total = len(CASES)
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": passed / total if total else 0.0,
        "results": results,
    }


if __name__ == "__main__":
    report = run_evals()
    with open("evals/results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Evals complete: {report['passed']}/{report['total']} passed ({report['pass_rate']:.1%})")
