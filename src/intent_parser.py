import json
import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv

from src.schemas import IntentSchema

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    return key


def call_openrouter(
    messages: list[dict[str, str]],
    model: str = "qwen/qwen-2.5-72b-instruct",
    temperature: float = 0.3,
    max_tokens: int = 1024,
    response_format: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format
    retries = 3
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(OPENROUTER_URL, headers=headers, json=payload)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise


def _system_prompt() -> str:
    return (
        "You are an intent parser for a baby-product gift finder. "
        "Extract structured intent from the user's query. "
        "CRITICAL RULES:\n"
        "1. If the query is about babies, children, kids, parenting, or gifts for them in ANY way, ALWAYS set is_parseable=true.\n"
        "2. Only set is_parseable=false if the query is completely unrelated to babies/children (e.g., cars, electronics for adults) or is pure gibberish/random letters.\n"
        "3. Missing budget, age, gender, or occasion is perfectly fine — just set those fields to null. NEVER refuse due to missing optional info.\n"
        "4. Vague queries about babies are OK — set is_parseable=true.\n"
        "Output strictly as JSON matching the IntentSchema."
    )


def _user_prompt(query: str, query_language: str) -> str:
    return (
        f"Query language: {query_language}\n"
        f"User query: {query}\n\n"
        "Return JSON with these fields:\n"
        "- child_age_months: int or null\n"
        "- budget_aed: float or null\n"
        "- occasion: string or null (e.g., birthday, newborn, general)\n"
        "- relationship: string or null (e.g., parent, friend, relative)\n"
        "- gender_preference: 'boy' | 'girl' | 'unisex' or null\n"
        "- query_language: 'en' | 'ar'\n"
        "- is_parseable: boolean\n"
        "- parse_issues: list of strings (empty if parseable)"
    )


def parse_intent(query: str, query_language: str) -> IntentSchema:
    try:
        response = call_openrouter(
            messages=[
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": _user_prompt(query, query_language)},
            ],
            response_format={"type": "json_object"},
        )
        content = response["choices"][0]["message"]["content"]
        data = json.loads(content)
        intent = IntentSchema(**data)
        # Rule-based fallback: never refuse baby-related queries due to LLM non-determinism
        if intent.is_parseable is False and _is_baby_related(query):
            intent.is_parseable = True
            intent.parse_issues = []
        return intent
    except Exception as e:
        if _is_baby_related(query):
            return IntentSchema(
                query_language=query_language,
                is_parseable=True,
                parse_issues=[],
            )
        return IntentSchema(
            query_language=query_language,
            is_parseable=False,
            parse_issues=[f"Intent parsing failed: {e}"],
        )


_BABY_KEYWORDS = [
    "baby", "babies", "newborn", "infant", "toddler", "child", "children", "kid", "kids",
    "gift for", "present for",
    "طفل", "طفلة", "أطفال", "مولود", "هدية", "هدايا", "رضيع", "صغير",
]


def _is_baby_related(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in _BABY_KEYWORDS)
