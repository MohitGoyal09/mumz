# Tradeoffs & Design Decisions

## Problem Choice

**Why gift recommendation?**
- High business value for Mumzworld (conversion driver)
- Natural fit for LLM + retrieval (intent parsing + product matching)
- Multilingual requirement makes it technically interesting
- Scoped to work with a synthetic catalog, avoiding external data dependencies

## Architecture Decisions

### Two-LLM Design
- **LLM Call 1 (Intent Parser)** — Extracts structured intent from free text
- **LLM Call 2 (Recommender)** — Ranks candidates and generates reasoning

**Tradeoff**: Two calls = higher latency and cost, but much better accuracy than a single monolithic prompt. Separation of concerns makes testing and debugging easier.

### FAISS + sentence-transformers
- `paraphrase-multilingual-MiniLM-L12-v2` handles EN/AR in the same embedding space
- `IndexFlatIP` with L2 normalization = cosine similarity
- Combined text fields (name + description + tags + category) for richer embeddings

**Tradeoff**: Flat index is exact but O(n) search. With 100 products this is trivial; at 100K+ products we'd need IVF or HNSW.

### Rule-Based Validator Before LLM
- Budget, age, and parseability checks happen before any expensive LLM call
- Reduces API costs and improves latency for invalid queries

**Tradeoff**: Hardcoded rules are less flexible than LLM-based validation, but faster and more deterministic.

## Cuts & Simplifications

1. **No real product database** — Synthetic 100-product catalog. Real implementation would connect to Mumzworld's product DB.
2. **No caching** — No Redis/cache layer. Real production would cache embeddings and LLM responses.
3. **No user history / personalization** — Each query is stateless. Real implementation would use purchase history.
4. **No A/B testing framework** — Evals are manual/scripted. Production would use online evals.
5. **No async LLM calls** — Synchronous HTTP calls to OpenRouter. Production would use async + streaming.

## Known Limitations

- **Cold start**: First FAISS index build downloads the transformer model (~120MB).
- **LLM dependency**: Requires OpenRouter API key; offline mode not implemented.
- **Arabic quality**: Depends on Qwen-2.5-72B Arabic capabilities; may not match native copywriter quality.
- **Catalog size**: 100 products limits diversity; some queries may have no good matches.

## Time Log (Approximate)

| Phase | Time |
|-------|------|
| Setup + dependencies | 30 min |
| Schemas + catalog + FAISS | 45 min |
| Language + intent + validator + retriever | 60 min |
| Recommender + pipeline | 45 min |
| API + CLI | 30 min |
| Evals + runner + grader | 45 min |
| Documentation | 30 min |
| Testing + fixes | 45 min |
| **Total** | **~5.5 hours** |

## Next Steps

1. Connect to real Mumzworld product catalog
2. Add Redis caching for embeddings and LLM responses
3. Implement user history / personalization
4. Add async streaming for faster TTFB
5. Online A/B testing with conversion tracking
