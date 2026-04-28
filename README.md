# Mumzworld AI Gift Finder

[Python 3.12+](https://www.python.org/downloads/)
[FastAPI](https://fastapi.tiangolo.com)
[Pydantic v2](https://docs.pydantic.dev)
[License: MIT](LICENSE)

> **Multilingual AI-powered gift recommendation engine for Mumzworld.** Accepts free-text queries in **English** or **Arabic**, parses user intent via LLM, retrieves matching products via FAISS embedding search over a synthetic catalog, and generates ranked recommendations with **native-quality bilingual reasoning**.
>
> 🎥 **[Watch the 3-Minute Demo (Loom)](https://www.loom.com/share/2703472d63d7447294593e0449c47944)**

---

## Features

- **Bilingual Support** — Accepts queries in English (`en`) or Arabic (`ar`) with native-quality Arabic output (not translation)
- **Two-Stage LLM Pipeline** — Intent parsing (LLM call 1) + Recommendation ranking & reasoning (LLM call 2)
- **Embedding-Based Retrieval** — FAISS cosine similarity search with `sentence-transformers` multilingual embeddings
- **Smart Pre-Filters** — Budget, age range, and gender compatibility filtering before ranking
- **Explicit Uncertainty Handling** — Refuses out-of-scope queries with bilingual reasons (budget too low, age too high, gibberish)
- **Hallucination Guard** — All recommended `product_id`s are verified against the catalog; no fabricated products
- **FastAPI + Typer CLI** — Production-ready API and interactive command-line interface
- **Streamlit Frontend** — Two-tab web UI with AI gift finder and browsable catalog data table with filters
- **Automated Evaluations** — 12 test cases with PASS/PARTIAL/FAIL grading and hallucination detection

---

## Architecture

```
User Query (EN/AR)
       |
       v
+-------------------+
| Language Detection|  langdetect → "en" | "ar"
+-------------------+
       |
       v
+-------------------+
|  Intent Parser    |  OpenRouter Qwen-2.5-72B
|  (LLM Call 1)     |  → IntentSchema {age, budget, occasion, gender, ...}
+-------------------+
       |
       v
+-------------------+
|    Validator      |  Rule-based: budget ≥ 15 AED, age ≤ 144 mo,
|                   |  parseable=True, baby-related
+-------------------+
       | (invalid → refused response with bilingual reason)
       v
+-------------------+
|    Retriever      |  FAISS IndexFlatIP + cosine similarity
|                   |  Pre-filters: price ≤ budget, age overlap, gender match
+-------------------+
       |
       v
+-------------------+
|   Recommender     |  OpenRouter Qwen-2.5-72B
|  (LLM Call 2)     |  → Ranks top-3 candidates + bilingual reasoning
+-------------------+
       |
       v
+-------------------+
| GiftResponseSchema|  {recommendations[], summary_en, summary_ar,
|                   |   confidence, refused, refusal_reason, ...}
+-------------------+
```

### Data Flow

1. **Language Detection** — `langdetect` identifies the query language (`en` or `ar`)
2. **Intent Parsing** — LLM extracts structured intent: `child_age_months`, `budget_aed`, `occasion`, `relationship`, `gender_preference`
3. **Validation** — Rule-based guardrails:
  - Budget < 15 AED → refuse
  - Child age > 144 months (12 years) → refuse
  - `is_parseable=False` or non-baby-related → refuse
  - Missing optional fields (budget, age, gender) → **allowed**, passed as `null`
4. **Retrieval** — Embedding search over 100-product catalog:
  - Embed query intent into 384-dim vector
  - FAISS `IndexFlatIP` with L2-normalized vectors (cosine similarity)
  - Pre-filter candidates by budget, age compatibility, and gender
  - Return top-20 candidates
5. **Recommendation** — LLM ranks top-3 from candidates and generates:
  - `reason_en` + `reason_ar` — why this product matches
  - `summary_en` + `summary_ar` — overall recommendation summary
  - `confidence` — 0.0 to 1.0 match confidence
6. **Response** — Validated against `GiftResponseSchema` (Pydantic v2)

### FAISS Index Building

The search index is built **lazily on first request** (no manual step needed):

```python
# src/catalog.py — automatic index initialization

1. Load catalog: data/catalog.json → 100 Product objects
2. Load model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
3. Encode texts:  [name_en + name_ar + description_en + description_ar + category + tags]
                  → 100 vectors × 384 dimensions (float32)
4. Normalize:     L2-normalize all vectors (required for cosine similarity with IndexFlatIP)
5. Build index:   faiss.IndexFlatIP(384) + add(100 vectors)
6. Cache:         Store index, product IDs, and model in memory for subsequent requests
```

**Cold-start cost**: ~90 seconds on first request (model download + encoding). Subsequent requests are instantaneous.

---

## Tech Stack


| Component          | Technology                                         | Purpose                                                   |
| ------------------ | -------------------------------------------------- | --------------------------------------------------------- |
| API Framework      | [FastAPI](https://fastapi.tiangolo.com)            | REST API with auto-generated OpenAPI docs                 |
| CLI Framework      | [Typer](https://typer.tiangolo.com)                | Interactive command-line interface                        |
| Schema Validation  | [Pydantic v2](https://docs.pydantic.dev)           | Type-safe data models and request/response validation     |
| Vector Search      | [FAISS](https://github.com/facebookresearch/faiss) | Efficient similarity search over product embeddings       |
| Embeddings         | [sentence-transformers](https://www.sbert.net)     | `paraphrase-multilingual-MiniLM-L12-v2` for EN/AR text    |
| LLM Inference      | [OpenRouter](https://openrouter.ai)                | Qwen-2.5-72B-Instruct for intent parsing & recommendation |
| Language Detection | [langdetect](https://pypi.org/project/langdetect/) | Query language identification                             |
| HTTP Client        | [httpx](https://www.python-httpx.org)              | Async-capable API calls to OpenRouter                     |
| Frontend           | [Streamlit](https://streamlit.io)                  | Interactive web UI for gift search and catalog browsing   |
| Testing            | [pytest](https://docs.pytest.org)                  | Unit and integration tests                                |


---

## Quick Start

### Prerequisites

- Python 3.12+
- [OpenRouter](https://openrouter.ai) API key (free tier supported)

### 1. Clone & Setup

```bash
git clone https://github.com/MohitGoyal09/mumz
cd mumzworld-gift-finder

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configure API Key

```bash
# Create .env file with your OpenRouter API key
echo "OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx" > .env
```

> Get your API key at [openrouter.ai/keys](https://openrouter.ai/keys)

### 3. Verify Setup

```bash
# Run all tests (should pass: 40/40)
pytest tests/ -v

# Quick pipeline test
python -c "from src.pipeline import run_pipeline; print(run_pipeline('gift for 6 month old baby under 200 AED'))"
```

---

## Usage

### API Server

Start the FastAPI server:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

#### Endpoints


| Method | Path         | Description                                    |
| ------ | ------------ | ---------------------------------------------- |
| `POST` | `/recommend` | Submit a query, receive ranked recommendations |
| `GET`  | `/health`    | Health check                                   |


#### Example: English Query

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "gift for 6-month-old baby boy, budget 200 AED"}'
```

**Response**:

```json
{
  "query_language": "en",
  "recommendations": [
    {
      "product_id": "PRD001",
      "name_en": "Philips Avent Natural Baby Bottle Starter Set",
      "name_ar": "طقم زجاجات الرضاعة الطبيعية من فيليبس أفنت للمبتدئين",
      "price_aed": 189.0,
      "reason_en": "Perfect starter set for a 6-month-old transitioning to bottles.",
      "reason_ar": "طقم مثالي للمبتدئين لطفل عمره 6 أشهر ينتقل إلى الزجاجات.",
      "match_score": 0.92
    }
  ],
  "summary_en": "Top picks for a 6-month-old baby boy within 200 AED budget.",
  "summary_ar": "أفضل الاختيارات لطفل عمره 6 أشهر ضمن ميزانية 200 درهم.",
  "confidence": 0.85,
  "refused": false
}
```

#### Example: Arabic Query

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "أحتاج هدية لطفلة عمرها سنة، ميزانية 300 درهم"}'
```

#### Example: Refused Query (Budget Too Low)

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "gift for baby budget 10 AED"}'
```

**Response**:

```json
{
  "query_language": "en",
  "recommendations": [],
  "summary_en": "",
  "summary_ar": "",
  "confidence": 0.0,
  "refused": true,
  "refusal_reason": "Minimum budget is 15 AED. Please increase your budget.",
  "refusal_reason_ar": "الحد الأدنى للميزانية هو 15 درهم. يرجى زيادة ميزانيتك."
}
```

---

### CLI

#### Single Query

```bash
python cli/demo.py recommend "gift for newborn girl"
```

#### Interactive Mode

```bash
python cli/demo.py interactive
```

```
Query: gift for 6 month old baby under 200 AED
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                         Gift Recommendations                                      ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Product                  ┃ Price (AED) ┃ Match Score ┃ Reason                   ┃
┃ ...                      ┃ ...         ┃ ...         ┃ ...                      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━┻━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━┛
Summary: Top picks for a 6-month-old baby within 200 AED budget.
ملخص: أفضل الاختيارات لطفل عمره 6 أشهر ضمن ميزانية 200 درهم.
Confidence: 0.85
```

---

### Streamlit Frontend

Start the FastAPI server first, then launch the Streamlit UI:

```bash
# Terminal 1 — start the API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — start the frontend
streamlit run frontend/app.py
```

The UI opens at [http://localhost:8501](http://localhost:8501) with two tabs:

- **🎁 Find Gifts** — Enter a free-text query (English or Arabic) and get AI-ranked product recommendations with bilingual reasoning
- **📦 Browse Catalog** — Filter, sort, and explore the full product catalog with stats and expandable product details

---

## Project Structure

```
mumzworld-gift-finder/
├── api/
│   └── main.py                    # FastAPI application
├── cli/
│   └── demo.py                    # Typer CLI (recommend + interactive)
├── data/
│   └── catalog.json               # 100-product synthetic catalog (EN+AR)
├── frontend/
│   └── app.py                     # Streamlit web UI (gift finder + catalog browser)
├── .streamlit/
│   └── config.toml                # Streamlit theme configuration
├── docs/
│   ├── prd.md                     # Product Requirements Document
│   └── req.md                     # Assignment requirements
├── evals/
│   ├── cases.py                   # 12 evaluation test cases
│   ├── grader.py                  # PASS/PARTIAL/FAIL grading logic
│   ├── runner.py                  # Eval execution + scoring
│   ├── test_cases.json            # JSON export of cases
│   └── results.json               # Latest eval run results
├── src/                           # Core pipeline modules
│   ├── __init__.py
│   ├── schemas.py                 # Pydantic v2 models (Product, IntentSchema, GiftResponseSchema)
│   ├── catalog.py                 # Catalog loader + FAISS index builder/search
│   ├── language.py                # langdetect wrapper (EN/AR detection)
│   ├── intent_parser.py           # LLM Call 1: parse intent from query
│   ├── validator.py               # Rule-based validation (budget, age, scope)
│   ├── retriever.py               # FAISS embedding search + pre-filters
│   ├── recommender.py             # LLM Call 2: rank candidates + bilingual reasoning
│   └── pipeline.py                # Orchestrates full query → response flow
├── tests/                         # pytest suite (40 tests)
│   ├── test_schemas.py
│   ├── test_catalog.py
│   ├── test_language.py
│   ├── test_intent_parser.py
│   ├── test_validator.py
│   ├── test_retriever.py
│   ├── test_recommender.py
│   ├── test_pipeline.py
│   ├── test_api.py
│   ├── test_cli.py
│   └── test_evals.py
├── .env                           # Environment variables (gitignored)
├── .env.example                   # Template for environment variables
├── pyproject.toml                 # Project config + dependencies
├── pytest.ini                     # Test configuration
├── README.md                      # This file
├── EVALS.md                       # Evaluation rubric, test cases, honest scores
└── TRADEOFFS.md                   # Architecture decisions, cuts, next steps
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/test_pipeline.py -v
pytest tests/test_intent_parser.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

**Current status**: 40/40 tests passing

---

## Evaluation Framework

12 test cases covering easy, adversarial, and edge-case scenarios:


| #   | Case                           | Language | Expected  | Type        |
| --- | ------------------------------ | -------- | --------- | ----------- |
| 1   | Clear intent with budget & age | EN       | Recommend | Easy        |
| 2   | Clear Arabic intent            | AR       | Recommend | Easy        |
| 3   | Vague query                    | EN       | Recommend | Edge        |
| 4   | High budget edge case          | EN       | Recommend | Edge        |
| 5   | Age out of range (20 years)    | EN       | Refuse    | Adversarial |
| 6   | Gender-specific query          | EN       | Recommend | Easy        |
| 7   | Arabic occasion-specific       | AR       | Recommend | Easy        |
| 8   | Empty query                    | EN       | Refuse    | Adversarial |
| 9   | Gibberish query                | EN       | Refuse    | Adversarial |
| 10  | Budget below minimum (10 AED)  | EN       | Refuse    | Adversarial |
| 11  | Missing age and budget         | EN       | Recommend | Edge        |
| 12  | Arabic missing budget          | AR       | Recommend | Edge        |


### Run Evaluations

```bash
# Run the eval harness (requires OPENROUTER_API_KEY)
python evals/grader.py

# Results saved to evals/results.json
```

**Grading criteria**:

- **PASS**: Correct refusal behavior + recommendations + no hallucinations + bilingual output
- **PARTIAL**: Correct refusal but minor quality issues
- **FAIL**: Wrong refusal, hallucination, or missing critical output

**Hallucination guard**: Any `product_id` not in `data/catalog.json` auto-FAILs.

See `[EVALS.md](EVALS.md)` for full rubric, iteration history, and honest failure analysis.

---

## Configuration

### Environment Variables


| Variable             | Required | Description                          |
| -------------------- | -------- | ------------------------------------ |
| `OPENROUTER_API_KEY` | ✅ Yes    | API key for OpenRouter LLM inference |


Create a `.env` file:

```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx
```

### Catalog Data

The synthetic catalog (`data/catalog.json`) contains 100 baby products across 6 categories:

- **Feeding** — Bottles, breast pumps, sterilizers
- **Gear** — Carriers, strollers, car seats
- **Nursery** — Cribs, monitors, bedding
- **Toys** — Educational, plush, activity centers
- **Care** — Diapers, skincare, thermometers
- **Clothing** — Onesies, sets, seasonal wear

Each product includes: English + Arabic names/descriptions, price (AED), age range, gender tag, category, tags, brand, and stock status.

---

## Troubleshooting

### FAISS Index Cold Start (~90s)

**Symptom**: First request takes 60-90 seconds.

**Cause**: `sentence-transformers` downloads the multilingual model (`~120MB`) and encodes all 100 products on first use.

**Fix**: The index is cached in memory after first build. Warm up on startup if needed:

```python
from src.catalog import build_index
build_index()  # Pre-build before serving requests
```

### OpenRouter 429 Rate Limit

**Symptom**: `HTTP 429 Too Many Requests` during bulk eval runs.

**Cause**: Running 12+ eval cases sequentially triggers ~24 LLM calls; OpenRouter free tier has rate limits.

**Fix**: The code includes retry with exponential backoff (1s, 2s, 4s). For bulk testing, add delays between cases or upgrade your OpenRouter tier.

### Missing Arabic Output

**Symptom**: Arabic queries return English-only responses.

**Cause**: The recommender prompt explicitly requests bilingual output, but some LLM responses may be inconsistent.

**Fix**: The validator and grader check for bilingual presence; minor quality issues are scored as PARTIAL, not FAIL.

### Module Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'src'`

**Fix**: Install in editable mode:

```bash
pip install -e ".[dev]"
```

---

## Architecture Decisions

See `[TRADEOFFS.md](TRADEOFFS.md)` for detailed discussion of:

- **Why two LLM calls?** Separation of concerns: intent parsing (structured extraction) vs. recommendation (ranking + reasoning)
- **Why FAISS + sentence-transformers?** Fast, local, multilingual semantic search without external vector DB costs
- **Why Qwen-2.5-72B?** Strong multilingual (especially Arabic) performance on OpenRouter free tier
- **What was cut?** Multi-turn chat, streaming, real catalog scraping, image multimodal, user feedback loop
- **What would be built next?** Real Mumzworld catalog integration, confidence calibration, A/B testing, RTL web UI

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Tooling

This project was built with AI-assisted tooling:

- **Data Generation** — The 100-product bilingual synthetic catalog (`data/catalog.json`) was generated using [Claude](https://claude.ai) (Anthropic) with structured prompting for native-quality Arabic product names and descriptions
- **Code Development** — The entire codebase, architecture, and Streamlit frontend were developed using [OpenCode](https://opencode.ai) with the **Kimi K2.6** model

---

## Acknowledgments

- Built for the **Mumzworld AI Engineering Intern (Track A)** submission
- LLM inference powered by [OpenRouter](https://openrouter.ai)
- Embeddings powered by [sentence-transformers](https://www.sbert.net)
- Vector search powered by [FAISS](https://github.com/facebookresearch/faiss)

