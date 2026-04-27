import pytest

from src.catalog import load_catalog, build_index, search_index, get_product_by_id
from src.schemas import Product


class TestCatalogLoader:
    def test_load_catalog_returns_100_products(self) -> None:
        products = load_catalog()
        assert len(products) == 100
        assert all(isinstance(p, Product) for p in products)

    def test_load_catalog_ids_unique(self) -> None:
        products = load_catalog()
        ids = [p.id for p in products]
        assert len(ids) == len(set(ids))


class TestIndexBuilder:
    def test_build_index_returns_faiss_index(self) -> None:
        products = load_catalog()
        index = build_index(products)
        assert index.ntotal == 100

    def test_search_index_top_k(self) -> None:
        build_index()
        results = search_index("baby bottle for newborn", k=5)
        assert len(results) == 5
        for product_id, score in results:
            assert product_id.startswith("PRD")
            assert 0.0 <= score <= 1.0

    def test_search_index_returns_different_products(self) -> None:
        build_index()
        results = search_index("toddler toy", k=3)
        ids = [r[0] for r in results]
        assert len(ids) == len(set(ids))

    def test_get_product_by_id(self) -> None:
        product = get_product_by_id("PRD001")
        assert product is not None
        assert product.id == "PRD001"

    def test_get_product_by_id_not_found(self) -> None:
        product = get_product_by_id("NONEXISTENT")
        assert product is None
