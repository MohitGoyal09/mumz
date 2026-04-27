from dataclasses import dataclass


@dataclass
class EvalCase:
    query: str
    expected_language: str
    should_refuse: bool
    min_recommendations: int
    description: str


CASES: list[EvalCase] = [
    EvalCase(
        query="I need a gift for a 6-month-old baby boy, budget 200 AED",
        expected_language="en",
        should_refuse=False,
        min_recommendations=1,
        description="English clear intent",
    ),
    EvalCase(
        query="أحتاج هدية لطفلة عمرها سنة، ميزانية 300 درهم",
        expected_language="ar",
        should_refuse=False,
        min_recommendations=1,
        description="Arabic clear intent",
    ),
    EvalCase(
        query="something nice for a baby",
        expected_language="en",
        should_refuse=False,
        min_recommendations=1,
        description="Vague query",
    ),
    EvalCase(
        query="gift for newborn under 5000 AED",
        expected_language="en",
        should_refuse=False,
        min_recommendations=1,
        description="High budget edge case",
    ),
    EvalCase(
        query="gift for a 20-year-old",
        expected_language="en",
        should_refuse=True,
        min_recommendations=0,
        description="Age out of range",
    ),
    EvalCase(
        query="toys for a baby girl",
        expected_language="en",
        should_refuse=False,
        min_recommendations=1,
        description="Gender-specific query",
    ),
    EvalCase(
        query="هدية عيد ميلاد لطفل عمره سنتين",
        expected_language="ar",
        should_refuse=False,
        min_recommendations=1,
        description="Arabic occasion-specific",
    ),
    EvalCase(
        query="",
        expected_language="en",
        should_refuse=True,
        min_recommendations=0,
        description="Empty query",
    ),
    EvalCase(
        query="asdfghjkl",
        expected_language="en",
        should_refuse=True,
        min_recommendations=0,
        description="Gibberish query",
    ),
    EvalCase(
        query="gift for 3-month-old budget 10 AED",
        expected_language="en",
        should_refuse=True,
        min_recommendations=0,
        description="Budget below minimum",
    ),
    EvalCase(
        query="best product for baby without mentioning age or budget",
        expected_language="en",
        should_refuse=False,
        min_recommendations=1,
        description="Missing age and budget",
    ),
    EvalCase(
        query="هدية لطفل، لا يوجد ميزانية محددة",
        expected_language="ar",
        should_refuse=False,
        min_recommendations=1,
        description="Arabic missing budget",
    ),
]
