from src.language import detect_language
from src.intent_parser import parse_intent
from src.validator import validate_intent
from src.retriever import retrieve_candidates
from src.recommender import recommend
from src.schemas import GiftResponseSchema


def run_pipeline(query: str) -> GiftResponseSchema:
    query_language = detect_language(query)
    intent = parse_intent(query, query_language)
    refusal = validate_intent(intent)
    if refusal is not None:
        return refusal
    candidates = retrieve_candidates(intent, k=20)
    response = recommend(intent, candidates)
    return response
