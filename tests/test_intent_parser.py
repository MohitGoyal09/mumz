import json
from typing import Any

import pytest

from src import intent_parser
from src.schemas import IntentSchema


class TestIntentParser:
    def test_parse_intent_success(self, monkeypatch: Any) -> None:
        def mock_call(*args, **kwargs):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({
                                "child_age_months": 6,
                                "budget_aed": 200.0,
                                "occasion": "general",
                                "relationship": "friend",
                                "gender_preference": "unisex",
                                "query_language": "en",
                                "is_parseable": True,
                                "parse_issues": [],
                            })
                        }
                    }
                ]
            }

        monkeypatch.setattr(intent_parser, "call_openrouter", mock_call)
        result = intent_parser.parse_intent("gift for 6 month old", "en")
        assert isinstance(result, IntentSchema)
        assert result.child_age_months == 6
        assert result.is_parseable is True

    def test_parse_intent_failure_returns_unparseable(self, monkeypatch: Any) -> None:
        def mock_call(*args, **kwargs):
            raise RuntimeError("API error")

        monkeypatch.setattr(intent_parser, "call_openrouter", mock_call)
        result = intent_parser.parse_intent("???", "en")
        assert result.is_parseable is False
        assert len(result.parse_issues) > 0
