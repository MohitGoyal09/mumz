import json
import os
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.schemas import Product

_CATALOG: list[Product] = []
_INDEX: faiss.Index | None = None
_PRODUCT_IDS: list[str] = []
_MODEL: SentenceTransformer | None = None
_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(_MODEL_NAME)
    return _MODEL


def load_catalog(path: str | None = None) -> list[Product]:
    global _CATALOG
    if _CATALOG:
        return _CATALOG
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    _CATALOG = [Product(**item) for item in raw]
    return _CATALOG


def _product_text(product: Product) -> str:
    parts = [
        product.name_en,
        product.name_ar,
        product.description_en,
        product.description_ar,
        product.category,
        product.subcategory,
        ", ".join(product.tags),
    ]
    return " ".join(parts)


def build_index(products: list[Product] | None = None) -> faiss.Index:
    global _INDEX, _PRODUCT_IDS
    if _INDEX is not None:
        return _INDEX
    if products is None:
        products = load_catalog()
    model = _get_model()
    texts = [_product_text(p) for p in products]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    embeddings = embeddings.astype("float32")
    faiss.normalize_L2(embeddings)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    _INDEX = index
    _PRODUCT_IDS = [p.id for p in products]
    return index


def search_index(query: str, k: int = 10) -> list[tuple[str, float]]:
    if _INDEX is None:
        build_index()
    model = _get_model()
    embedding = model.encode([query], convert_to_numpy=True)
    embedding = embedding.astype("float32")
    faiss.normalize_L2(embedding)
    scores, indices = _INDEX.search(embedding, k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_PRODUCT_IDS):
            continue
        results.append((_PRODUCT_IDS[idx], float(score)))
    return results


def get_product_by_id(product_id: str) -> Product | None:
    for p in load_catalog():
        if p.id == product_id:
            return p
    return None
