import json
from pathlib import Path
import streamlit as st
import httpx

st.set_page_config(
    page_title="Mumzworld AI Gift Finder",
    page_icon="🎁",
    layout="wide",
)

API_BASE_DEFAULT = "http://localhost:8000"
CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "catalog.json"

EXAMPLE_QUERIES = [
    ("EN: 6-month baby boy, budget 200 AED", "gift for 6-month-old baby boy, budget 200 AED"),
    ("EN: Newborn girl", "gift for newborn girl"),
    ("AR: هدية لطفل عمره سنة، ميزانية 300 درهم", "هدية لطفل عمره سنة، ميزانية 300 درهم"),
    ("AR: هدية لمولود جديد", "هدية لمولود جديد"),
]


@st.cache_data
def load_catalog() -> list[dict]:
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def check_health(api_base: str) -> dict:
    try:
        r = httpx.get(f"{api_base}/health", timeout=5)
        return r.json() if r.status_code == 200 else {"status": "error"}
    except Exception:
        return {"status": "unreachable"}


def fetch_recommendations(api_base: str, query: str) -> dict:
    r = httpx.post(
        f"{api_base}/recommend",
        json={"query": query},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


with st.sidebar:
    st.header("⚙️ Settings")
    api_base = st.text_input("API Base URL", value=API_BASE_DEFAULT)

    st.divider()
    st.header("ℹ️ About")
    st.markdown(
        """
        **Mumzworld AI Gift Finder** uses a two-stage LLM pipeline:
        1. **Intent Parsing** — extracts age, budget, gender, occasion
        2. **Recommendation** — ranks products with bilingual reasoning

        Built with FastAPI + Streamlit. Supports English & Arabic queries.
        """
    )

    st.divider()
    st.header("🔌 API Status")
    health = check_health(api_base)
    if health.get("status") == "ok":
        st.success("API Online")
    else:
        st.error(f"API {health.get('status', 'unknown')}")
        st.info("Start the API: `uvicorn api.main:app --reload`")

    st.divider()
    st.caption("⚠️ First request may take ~90s while the AI model loads.")


tab_gifts, tab_catalog = st.tabs(["🎁 Find Gifts", "📦 Browse Catalog"])


with tab_gifts:
    st.title("🎁 Mumzworld AI Gift Finder")
    st.markdown(
        "<p style='font-size:1.1rem; color:#666;'>"
        "Describe the gift you're looking for in <b>English</b> or <b>Arabic</b>. "
        "Our AI will find the perfect baby products from our catalog.</p>",
        unsafe_allow_html=True,
    )

    st.markdown("**Try an example:**")
    ex_cols = st.columns(len(EXAMPLE_QUERIES))
    for col, (label, query_text) in zip(ex_cols, EXAMPLE_QUERIES):
        if col.button(label, use_container_width=True):
            st.session_state["query_input"] = query_text
            st.session_state["submitted"] = True

    st.divider()

    query = st.text_area(
        "Your gift query",
        placeholder="e.g. gift for 6-month-old baby boy, budget 200 AED",
        height=80,
        value=st.session_state.get("query_input", ""),
    )
    submitted = st.button("Find Gifts", type="primary", use_container_width=True)
    if st.session_state.get("submitted"):
        submitted = True
        st.session_state["submitted"] = False

    if submitted and query:
        with st.spinner("🤖 Finding the perfect gifts for you... (first load may take ~90s)"):
            try:
                data = fetch_recommendations(api_base, query)
            except httpx.ConnectError:
                st.error(f"❌ Cannot connect to API at {api_base}. Make sure the server is running.")
                st.info("Start it with: `uvicorn api.main:app --reload`")
                st.stop()
            except httpx.HTTPStatusError as e:
                st.error(f"❌ API error ({e.response.status_code}): {e.response.text}")
                st.stop()
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
                st.stop()

        if data.get("refused"):
            st.error("❌ We couldn't process your request")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**English:** {data.get('refusal_reason', '')}")
            with c2:
                st.markdown(
                    f"<div dir='rtl' style='text-align:right;'>**العربية:** {data.get('refusal_reason_ar', '')}</div>",
                    unsafe_allow_html=True,
                )
        else:
            recs = data.get("recommendations", [])
            if recs:
                st.success(f"✅ Found {len(recs)} recommendation(s)")

                for i, item in enumerate(recs, 1):
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #FFF5F7;
                                border-radius: 12px;
                                padding: 20px;
                                margin-bottom: 16px;
                                border-left: 5px solid #FF6B9D;
                            ">
                                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                    <div style="flex:1;">
                                        <h4 style="margin:0 0 6px 0; color:#333;">{i}. {item.get('name_en', '')}</h4>
                                        <p style="margin:0 0 10px 0; color:#666; font-size:0.95rem; direction:rtl; text-align:right;">
                                            {item.get('name_ar', '')}
                                        </p>
                                    </div>
                                    <div style="
                                        background:#FF6B9D;
                                        color:white;
                                        padding:6px 14px;
                                        border-radius:20px;
                                        font-weight:bold;
                                        white-space:nowrap;
                                        margin-left:12px;
                                    ">
                                        {item.get('price_aed', 0):.0f} AED
                                    </div>
                                </div>
                                <div style="margin:10px 0;">
                                    <div style="display:flex; align-items:center; gap:10px;">
                                        <span style="font-size:0.85rem; color:#555;">Match Score:</span>
                                        <div style="flex:1; background:#eee; border-radius:10px; height:10px; overflow:hidden;">
                                            <div style="width:{item.get('match_score', 0)*100}%; background:#FF6B9D; height:100%;"></div>
                                        </div>
                                        <span style="font-weight:bold; color:#FF6B9D;">{item.get('match_score', 0):.0%}</span>
                                    </div>
                                </div>
                                <p style="margin:8px 0 4px 0; color:#444;"><b>Why this fits:</b> {item.get('reason_en', '')}</p>
                                <p style="margin:0; color:#666; direction:rtl; text-align:right;">{item.get('reason_ar', '')}</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                st.divider()
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Summary:** {data.get('summary_en', '')}")
                with c2:
                    st.markdown(
                        f"<div dir='rtl' style='text-align:right;'><b>الملخص:</b> {data.get('summary_ar', '')}</div>",
                        unsafe_allow_html=True,
                    )

                st.metric("Confidence", f"{data.get('confidence', 0):.0%}")
            else:
                st.info("No recommendations found. Try adjusting your query.")


with tab_catalog:
    st.title("📦 Product Catalog")
    st.markdown(
        "<p style='font-size:1.1rem; color:#666;'>"
        "Browse our curated catalog of baby products. Use the filters below to narrow down your search.</p>",
        unsafe_allow_html=True,
    )

    catalog = load_catalog()

    st.subheader("🔍 Filters")
    fcols = st.columns(4)

    with fcols[0]:
        categories = ["All"] + sorted({p["category"] for p in catalog})
        sel_category = st.selectbox("Category", categories)

    with fcols[1]:
        genders = ["All"] + sorted({p["gender"] for p in catalog})
        sel_gender = st.selectbox("Gender", genders)

    with fcols[2]:
        max_price = max(p["price_aed"] for p in catalog)
        sel_max_price = st.slider("Max Price (AED)", 0, int(max_price) + 50, int(max_price) + 50)

    with fcols[3]:
        stock_only = st.checkbox("In Stock Only", value=False)

    filtered = catalog
    if sel_category != "All":
        filtered = [p for p in filtered if p["category"] == sel_category]
    if sel_gender != "All":
        filtered = [p for p in filtered if p["gender"] == sel_gender]
    filtered = [p for p in filtered if p["price_aed"] <= sel_max_price]
    if stock_only:
        filtered = [p for p in filtered if p["in_stock"]]

    st.divider()
    scols = st.columns(4)
    scols[0].metric("Total Products", len(filtered))
    scols[1].metric("Avg Price", f"{sum(p['price_aed'] for p in filtered) / len(filtered):.0f} AED" if filtered else "0 AED")
    scols[2].metric("Categories", len({p["category"] for p in filtered}))
    scols[3].metric("Brands", len({p["brand"] for p in filtered}))

    st.divider()

    if not filtered:
        st.warning("No products match your filters.")
    else:
        st.subheader(f"Showing {len(filtered)} product(s)")

        table_data = []
        for p in filtered:
            table_data.append({
                "ID": p["id"],
                "Name (EN)": p["name_en"],
                "Name (AR)": p["name_ar"],
                "Category": p["category"],
                "Subcategory": p["subcategory"],
                "Brand": p["brand"],
                "Price (AED)": p["price_aed"],
                "Age Min (mo)": p["age_range_months_min"],
                "Age Max (mo)": p["age_range_months_max"],
                "Gender": p["gender"],
                "In Stock": "✅" if p["in_stock"] else "❌",
                "Tags": ", ".join(p["tags"]),
            })

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price (AED)": st.column_config.NumberColumn(format="%.0f AED"),
                "Name (AR)": st.column_config.TextColumn(width="large"),
            },
        )

        st.divider()
        st.subheader("📋 Product Details")
        for p in filtered:
            with st.expander(f"{p['id']} — {p['name_en']} ({p['price_aed']:.0f} AED)"):
                dcols = st.columns([2, 1])
                with dcols[0]:
                    st.markdown(f"**English:** {p['description_en']}")
                    st.markdown(
                        f"<div dir='rtl' style='text-align:right;'>**العربية:** {p['description_ar']}</div>",
                        unsafe_allow_html=True,
                    )
                with dcols[1]:
                    st.markdown(f"**Category:** {p['category']}")
                    st.markdown(f"**Subcategory:** {p['subcategory']}")
                    st.markdown(f"**Brand:** {p['brand']}")
                    st.markdown(f"**Gender:** {p['gender']}")
                    st.markdown(f"**Age Range:** {p['age_range_months_min']}–{p['age_range_months_max']} mo")
                    st.markdown(f"**Price:** {p['price_aed']:.0f} AED")
                    st.markdown(f"**Stock:** {'✅ In Stock' if p['in_stock'] else '❌ Out of Stock'}")
                    st.markdown(f"**Tags:** {', '.join(p['tags'])}")
