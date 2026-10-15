"""SmartPick AI — Intelligent Mobile Recommender.

Streamlit application entry point.
Architectural rule: This module is strictly responsible for presentation, layout,
user interaction, and state management. All recommendation, filtering,
and evaluation logic resides in `src/`.
"""

import hashlib
import logging
import textwrap
import time
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.counterfactual import explain_why_not_phone
from src.data_loader import DataLoader, DatasetMetadata
from src.exceptions import (
    BudgetValidationError,
    NoEligiblePhonesError,
    SmartPickError,
    ZeroWeightsError,
)
from src.frontier import compute_pareto_frontier, render_pareto_frontier_chart
from src.i18n import get_text
from src.preprocessing import FeaturePreprocessor
from src.quality_report import QualityReportGenerator, QualitySummary
from src.recommender import RecommendationResult, SmartPickRecommender, UserPreferences
from src.sensitivity import compute_what_if_movement
from src.ui_charts import (
    render_contribution_bar,
    render_price_distribution,
    render_price_vs_battery_scatter,
    render_radar_comparison,
    render_weight_profile,
)
from src.ui_components import (
    build_compare_column_header_html,
    build_footer_html,
    build_hero_badge_html,
    build_no_candidates_html,
    build_phone_card_html,
    build_why_not_card_html,
)
from src.ui_export import export_recommendations_csv, export_recommendations_html
from src.ui_styles import inject_custom_styles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("smartpick_ai.app")

PRESET_CONFIGS: dict[str, dict[str, Any]] = {
    "Gamer": {
        "weights": {
            "weight_performance": 0.95,
            "weight_camera": 0.25,
            "weight_battery": 0.70,
            "weight_display": 0.85,
            "weight_storage": 0.60,
            "weight_value": 0.30,
        },
        "desc": "Maximizes GPU speed and 120Hz/144Hz refresh rate for competitive mobile gaming.",
    },
    "Photographer": {
        "weights": {
            "weight_performance": 0.45,
            "weight_camera": 0.95,
            "weight_battery": 0.50,
            "weight_display": 0.60,
            "weight_storage": 0.75,
            "weight_value": 0.35,
        },
        "desc": "Prioritizes high-resolution primary camera sensor and large flash storage for 4K video.",
    },
    "Student": {
        "weights": {
            "weight_performance": 0.50,
            "weight_camera": 0.40,
            "weight_battery": 0.80,
            "weight_display": 0.50,
            "weight_storage": 0.50,
            "weight_value": 0.90,
        },
        "desc": "Maximizes hardware-per-rupee value and dependable battery life for campus days.",
    },
    "Battery Saver": {
        "weights": {
            "weight_performance": 0.30,
            "weight_camera": 0.30,
            "weight_battery": 1.00,
            "weight_display": 0.40,
            "weight_storage": 0.40,
            "weight_value": 0.60,
        },
        "desc": "Prioritizes massive 6,000+ mAh battery capacity for field workers and multi-day shifts.",
    },
    "Senior-Friendly": {
        "weights": {
            "weight_performance": 0.40,
            "weight_camera": 0.40,
            "weight_battery": 0.75,
            "weight_display": 0.95,
            "weight_storage": 0.40,
            "weight_value": 0.50,
        },
        "desc": "Prioritizes large, vibrant displays with smooth legibility and dependable battery life.",
    },
    "Balanced": {
        "weights": {
            "weight_performance": 0.50,
            "weight_camera": 0.50,
            "weight_battery": 0.50,
            "weight_display": 0.50,
            "weight_storage": 0.50,
            "weight_value": 0.50,
        },
        "desc": "Equal distribution across all specification dimensions for a daily driver.",
    },
}


def get_dataset_version() -> str:
    """Calculate MD5 checksum of active catalog file for cache invalidation."""
    data_path = Path("data/phones.csv")
    if not data_path.exists():
        return "none"
    return hashlib.md5(data_path.read_bytes()).hexdigest()[:8]


def format_inr(value: float | None) -> str:
    """Format numeric value in Indian Lakhs/Thousands currency format."""
    if value is None or pd.isna(value):
        return "N/A"
    try:
        val_int = round(float(value))
    except (ValueError, TypeError):
        return str(value)

    s = str(abs(val_int))
    if len(s) <= 3:
        formatted = s
    else:
        last_three = s[-3:]
        remaining = s[:-3]
        parts = []
        while len(remaining) > 2:
            parts.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            parts.insert(0, remaining)
        formatted = f"{','.join(parts)},{last_three}"

    prefix = "-₹" if val_int < 0 else "₹"
    return f"{prefix}{formatted}"


def configure_page() -> None:
    """Configure Streamlit page layout, metadata, and branding."""
    st.set_page_config(
        page_title="SmartPick AI — Intelligent Mobile Recommender",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_custom_styles()


@st.cache_resource(show_spinner=False)
def load_catalog_and_engine(
    dataset_version: str,
) -> tuple[pd.DataFrame, DatasetMetadata, QualitySummary, SmartPickRecommender]:
    """Cached loader for catalog, metadata, summary, and initialized recommender.

    Invalidated automatically whenever the dataset file checksum changes.
    """
    data_path = Path("data/phones.csv")
    loader = DataLoader(data_path)
    df, metadata = loader.load_and_validate()
    generator = QualityReportGenerator(df, metadata)
    summary = generator.get_summary()

    scaler_path = Path("artifacts/preprocessor.joblib")
    if scaler_path.exists():
        preprocessor = FeaturePreprocessor.load(scaler_path)
    else:
        preprocessor = FeaturePreprocessor(strategy="robust_minmax")
        preprocessor.fit(df)
        scaler_path.parent.mkdir(parents=True, exist_ok=True)
        preprocessor.save(scaler_path)

    recommender = SmartPickRecommender(df, preprocessor)
    return df, metadata, summary, recommender


def init_session_state(df: pd.DataFrame) -> None:
    """Initialize session state and parse URL query parameters."""
    min_catalog_price = int(df["price_inr"].min())
    max_catalog_price = int(df["price_inr"].max())

    if "compare_list" not in st.session_state:
        st.session_state.compare_list = []

    if "ui_lang" not in st.session_state:
        st.session_state.ui_lang = "English"

    query_params = st.query_params

    if "min_budget" not in st.session_state:
        param_min = query_params.get("min_budget")
        st.session_state.min_budget = (
            int(param_min)
            if param_min and param_min.isdigit()
            else max(10000, min_catalog_price)
        )

    if "max_budget" not in st.session_state:
        param_max = query_params.get("max_budget")
        st.session_state.max_budget = (
            int(param_max)
            if param_max and param_max.isdigit()
            else min(50000, max_catalog_price)
        )

    for dim in ["performance", "camera", "battery", "display", "storage", "value"]:
        key = f"weight_{dim}"
        if key not in st.session_state:
            param_w = query_params.get(key)
            try:
                st.session_state[key] = float(param_w) if param_w is not None else 0.50
            except ValueError:
                st.session_state[key] = 0.50

    if "brand_filter" not in st.session_state:
        param_brands = query_params.get("brands")
        st.session_state.brand_filter = param_brands.split(",") if param_brands else []

    if "five_g_only" not in st.session_state:
        param_5g = query_params.get("five_g")
        st.session_state.five_g_only = param_5g.lower() == "true" if param_5g else False

    if "ranking_mode_idx" not in st.session_state:
        st.session_state.ranking_mode_idx = 0

    if "blend_factor" not in st.session_state:
        st.session_state.blend_factor = 0.35

    if "diversity_lambda" not in st.session_state:
        st.session_state.diversity_lambda = 0.70

    if "anchor_phone" not in st.session_state:
        st.session_state.anchor_phone = None


def sync_query_params() -> None:
    """Encode current filter state into URL query params for shareable profiles."""
    st.query_params["min_budget"] = str(st.session_state.min_budget)
    st.query_params["max_budget"] = str(st.session_state.max_budget)
    for dim in ["performance", "camera", "battery", "display", "storage", "value"]:
        st.query_params[f"weight_{dim}"] = f"{st.session_state[f'weight_{dim}']:.2f}"
    if st.session_state.brand_filter:
        st.query_params["brands"] = ",".join(st.session_state.brand_filter)
    elif "brands" in st.query_params:
        del st.query_params["brands"]
    st.query_params["five_g"] = "true" if st.session_state.five_g_only else "false"


def render_hero(
    summary: QualitySummary,
    metadata: DatasetMetadata,
    lang_code: str,
    version_hash: str,
) -> None:
    """Render top hero header, value proposition, freshness badge, and synthetic banner."""
    c_title, c_badge = st.columns([3, 1])
    with c_title:
        st.markdown(
            f"<h1 style='margin-bottom: 2px; color: #F8FAFC;'>📱 {get_text('app_title', lang=lang_code)}</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='font-size: 1.05rem; color: #94A3B8; margin-top: 0;'>"
            f"{get_text('app_subtitle', lang=lang_code)}"
            f"</p>",
            unsafe_allow_html=True,
        )
    with c_badge:
        st.markdown(
            build_hero_badge_html(
                catalog_status_text=get_text("catalog_status", lang=lang_code),
                source_name=metadata.source_name or "Curated Catalog",
                verified_recent_text=get_text("verified_recent", lang=lang_code),
                last_verified=metadata.last_verified or "2026-10-15",
                version_hash=version_hash,
            ),
            unsafe_allow_html=True,
        )

    if summary.is_synthetic:
        st.warning(
            "⚠️ **SYNTHETIC BENCHMARK SAMPLE ACTIVE**: "
            "This catalog contains procedurally generated specification data with deliberate edge cases "
            f"({summary.total_records} rows: missing attributes, hardware variants, outliers) "
            "for national competition evaluation and architectural testing. "
            "Scores represent relative heuristic preference alignment, not live retail inventory guarantees."
        )


def render_sidebar(df: pd.DataFrame, lang_code: str) -> UserPreferences:
    """Render sidebar controls: language toggle, budget, documented presets, and filters."""
    # 0. Language Selector
    st.sidebar.markdown("### 🌐 UI Language / भाषा")
    st.sidebar.radio(
        "Select Language",
        options=["English", "Hinglish"],
        horizontal=True,
        label_visibility="collapsed",
        key="ui_lang",
    )

    st.sidebar.markdown(f"### ⚙️ {get_text('quick_presets', lang=lang_code)}")

    # 1. Preset Buttons with Documented Weight Vectors (2-column grid for full visibility)
    p_cols1 = st.sidebar.columns(2)
    p_cols2 = st.sidebar.columns(2)
    p_cols3 = st.sidebar.columns(2)

    def apply_preset(preset_name: str) -> None:
        cfg = PRESET_CONFIGS[preset_name]["weights"]
        for k, v in cfg.items():
            st.session_state[k] = v

    if p_cols1[0].button(
        "🎮 Gamer", use_container_width=True, help=PRESET_CONFIGS["Gamer"]["desc"]
    ):
        apply_preset("Gamer")
        st.rerun()
    if p_cols1[1].button(
        "📸 Photo",
        use_container_width=True,
        help=PRESET_CONFIGS["Photographer"]["desc"],
    ):
        apply_preset("Photographer")
        st.rerun()
    if p_cols2[0].button(
        "🎓 Student", use_container_width=True, help=PRESET_CONFIGS["Student"]["desc"]
    ):
        apply_preset("Student")
        st.rerun()
    if p_cols2[1].button(
        "🔋 Battery",
        use_container_width=True,
        help=PRESET_CONFIGS["Battery Saver"]["desc"],
    ):
        apply_preset("Battery Saver")
        st.rerun()
    if p_cols3[0].button(
        "👓 Senior",
        use_container_width=True,
        help=PRESET_CONFIGS["Senior-Friendly"]["desc"],
    ):
        apply_preset("Senior-Friendly")
        st.rerun()
    if p_cols3[1].button(
        "⚖️ Balanced", use_container_width=True, help=PRESET_CONFIGS["Balanced"]["desc"]
    ):
        apply_preset("Balanced")
        st.rerun()

    with st.sidebar.expander("📖 View Documented Preset Weights"):
        for pname, pinfo in PRESET_CONFIGS.items():
            st.markdown(f"**{pname}**: {pinfo['desc']}")
            w_str = ", ".join(
                f"{k.replace('weight_', '')[:4]}:{v:.2f}"
                for k, v in pinfo["weights"].items()
            )
            st.caption(f"Vectors: `{w_str}`")

    st.sidebar.markdown("---")

    # 2. Budget Constraints
    st.sidebar.markdown(f"**{get_text('budget_window', lang=lang_code)}**")
    min_catalog = int(df["price_inr"].min())
    max_catalog = int(df["price_inr"].max())

    current_min = max(min_catalog, min(st.session_state.min_budget, max_catalog))
    current_max = max(min_catalog, min(st.session_state.max_budget, max_catalog))
    current_min = min(current_min, current_max)

    budget_range = st.sidebar.slider(
        "Select Range (₹)",
        min_value=min_catalog,
        max_value=max_catalog,
        value=(current_min, current_max),
        step=1000,
        format="₹%d",
        help="Hard constraint: 100% of recommended devices strictly fit within this window.",
    )
    st.session_state.min_budget = budget_range[0]
    st.session_state.max_budget = budget_range[1]

    st.sidebar.caption(
        f"Selected: **{format_inr(st.session_state.min_budget)}** to **{format_inr(st.session_state.max_budget)}**"
    )

    st.sidebar.markdown("---")

    # 3. Preference Sliders
    st.sidebar.markdown(f"**{get_text('priority_dimensions', lang=lang_code)}**")

    def slider_row(label: str, key: str, help_text: str) -> float:
        val = st.sidebar.slider(
            label,
            min_value=0.0,
            max_value=1.0,
            value=float(st.session_state[key]),
            step=0.05,
            key=key,
            help=help_text,
        )
        return val

    w_perf = slider_row(
        get_text("dim_perf", lang=lang_code),
        "weight_performance",
        "Prioritizes high AnTuTu processor score and RAM",
    )
    w_cam = slider_row(
        get_text("dim_cam", lang=lang_code),
        "weight_camera",
        "Prioritizes main sensor megapixel count (hardware proxy)",
    )
    w_bat = slider_row(
        get_text("dim_bat", lang=lang_code),
        "weight_battery",
        "Prioritizes large battery capacity (mAh)",
    )
    w_disp = slider_row(
        get_text("dim_disp", lang=lang_code),
        "weight_display",
        "Prioritizes smooth 120Hz/144Hz panel refresh rates",
    )
    w_stor = slider_row(
        get_text("dim_stor", lang=lang_code),
        "weight_storage",
        "Prioritizes large internal flash storage (GB)",
    )
    w_val = slider_row(
        get_text("dim_val", lang=lang_code),
        "weight_value",
        "Prioritizes spec-to-price ratio relative to eligible median",
    )

    st.sidebar.markdown("---")

    # 4. Optional Filters & Ranking Mode Selector
    st.sidebar.markdown(f"**🔍 {get_text('brand_filter', lang=lang_code)}**")
    available_brands = sorted(
        [str(b) for b in df["brand"].dropna().unique() if str(b).strip()]
    )
    selected_brands = st.sidebar.multiselect(
        "Brand Filter",
        options=available_brands,
        default=[b for b in st.session_state.brand_filter if b in available_brands],
        label_visibility="collapsed",
        help="Leave empty to include all manufacturers.",
    )
    st.session_state.brand_filter = selected_brands

    five_g_checked = False
    if "has_5g" in df.columns:
        five_g_checked = st.sidebar.checkbox(
            get_text("require_5g", lang=lang_code),
            value=st.session_state.five_g_only,
            help="Exclude devices that lack 5G support.",
        )
        st.session_state.five_g_only = five_g_checked

    st.sidebar.markdown(f"**⚙️ {get_text('ranking_engine_mode', lang=lang_code)}**")
    mode_options = [
        "Baseline (Multi-Attribute Heuristic)",
        "Similarity (Content-Based Cosine)",
        "Blended Hybrid (Baseline + Similarity)",
        "Diversity-Aware (MMR Re-ranked)",
    ]
    selected_mode_idx = st.sidebar.selectbox(
        "Select Engine Mode",
        options=range(len(mode_options)),
        format_func=lambda idx: mode_options[idx],
        index=st.session_state.ranking_mode_idx,
        label_visibility="collapsed",
        help="Choose ranking paradigm: Baseline utility, Content cosine, Blended hybrid, or Diversity MMR.",
    )
    st.session_state.ranking_mode_idx = selected_mode_idx
    mode_str = mode_options[selected_mode_idx]

    # Additional tuning controls for Blended and MMR modes
    blend_val = st.session_state.blend_factor
    lambda_val = st.session_state.diversity_lambda

    if "Blended" in mode_str:
        blend_val = st.sidebar.slider(
            "Similarity Blend Factor (α)",
            min_value=0.05,
            max_value=0.95,
            value=float(st.session_state.blend_factor),
            step=0.05,
            help="Weight alpha: (1-α)*Baseline + α*Similarity.",
        )
        st.session_state.blend_factor = blend_val

    if "Diversity-Aware" in mode_str or "MMR" in mode_str:
        lambda_val = st.sidebar.slider(
            "MMR Relevance Trade-off (λ)",
            min_value=0.10,
            max_value=0.90,
            value=float(st.session_state.diversity_lambda),
            step=0.05,
            help="Trade-off parameter: 1.0 = Pure relevance; 0.1 = Maximum brand diversity.",
        )
        st.session_state.diversity_lambda = lambda_val

    if st.session_state.anchor_phone:
        st.sidebar.info(f"Anchor Selected: **{st.session_state.anchor_phone}**")
        if st.sidebar.button("Clear Anchor Device"):
            st.session_state.anchor_phone = None
            st.rerun()

    if st.sidebar.button(
        get_text("reset_profile", lang=lang_code), use_container_width=True
    ):
        st.session_state.min_budget = min_catalog
        st.session_state.max_budget = max_catalog
        st.session_state.brand_filter = []
        st.session_state.five_g_only = False
        st.session_state.anchor_phone = None
        apply_preset("Balanced")
        st.rerun()

    sync_query_params()
    with st.sidebar.expander("🔗 Shareable Profile Link"):
        st.caption(
            "Judges can bookmark or share this search query with pre-configured weights."
        )
        st.code(
            f"?min_budget={st.session_state.min_budget}&max_budget={st.session_state.max_budget}"
            f"&w_perf={w_perf:.2f}&w_cam={w_cam:.2f}&w_bat={w_bat:.2f}"
            f"&brands={','.join(selected_brands)}&five_g={'true' if five_g_checked else 'false'}",
            language="text",
        )

    # Determine mode keyword for recommender
    mode_key = "baseline"
    if "Similarity" in mode_str:
        mode_key = "similarity"
    elif "Blended" in mode_str:
        mode_key = "blended"
    elif "Diversity" in mode_str or "MMR" in mode_str:
        mode_key = "mmr"

    return UserPreferences(
        min_budget=float(st.session_state.min_budget),
        max_budget=float(st.session_state.max_budget),
        weight_performance=w_perf,
        weight_camera=w_cam,
        weight_battery=w_bat,
        weight_display=w_disp,
        weight_storage=w_stor,
        weight_value=w_val,
        preferred_brands=selected_brands if selected_brands else None,
        require_5g=five_g_checked if five_g_checked else None,
        ranking_mode=mode_key,
        blend_factor=blend_val,
        diversity_lambda=lambda_val,
        reference_phone=st.session_state.anchor_phone,
    )


def compute_spec_completeness(specs: dict[str, Any]) -> int:
    """Calculate percentage completeness across 6 core canonical specifications."""
    core_keys = [
        "processor_score",
        "camera_mp",
        "battery_mah",
        "display_hz",
        "storage_gb",
        "ram_gb",
    ]
    valid_count = sum(1 for k in core_keys if pd.notna(specs.get(k)))
    return int((valid_count / len(core_keys)) * 100)


def render_recommendation_card(
    r: RecommendationResult, rank: int, lang_code: str
) -> None:
    """Render modern accessible fintech-grade card for a recommended smartphone."""
    card_html = build_phone_card_html(
        r=r,
        rank=rank,
        lang_code=lang_code,
        top_match_text=get_text("top_match", lang=lang_code),
        shortlisted_text=get_text("shortlisted", lang=lang_code),
        within_budget_text=get_text("within_budget", lang=lang_code),
        match_score_label=get_text("match_score_label", lang=lang_code),
        trade_offs_label=get_text("trade_offs", lang=lang_code),
        formatted_price=format_inr(r.price_inr),
    )
    st.markdown(card_html, unsafe_allow_html=True)

    act_col1, act_col2, _ = st.columns([1.5, 1.5, 4])
    is_in_compare = r.phone_name in st.session_state.compare_list
    if act_col1.checkbox(
        get_text("add_to_compare", lang=lang_code),
        value=is_in_compare,
        key=f"chk_{r.phone_name}",
    ):
        if r.phone_name not in st.session_state.compare_list:
            if len(st.session_state.compare_list) < 4:
                st.session_state.compare_list.append(r.phone_name)
            else:
                st.toast(
                    "⚠️ Maximum 4 devices can be compared simultaneously.", icon="ℹ️"
                )
    else:
        if r.phone_name in st.session_state.compare_list:
            st.session_state.compare_list.remove(r.phone_name)

    if act_col2.button(
        get_text("find_similar", lang=lang_code),
        key=f"btn_sim_{r.phone_name}",
        help="Use this device as similarity anchor",
    ):
        st.session_state.anchor_phone = r.phone_name
        st.session_state.ranking_mode_idx = 1  # Switch to similarity mode
        st.toast(
            f"Anchor selected: **{r.phone_name}**. Switched to Content Similarity mode.",
            icon="📱",
        )
        st.rerun()


def render_tab_recommendations(
    recommender: SmartPickRecommender,
    prefs: UserPreferences,
    metadata: DatasetMetadata,
    lang_code: str,
) -> tuple[list[RecommendationResult], pd.DataFrame]:
    """Render Tab 1: Recommendation cards, export buttons, and What-If simulator."""
    try:
        t0 = time.perf_counter()
        results = recommender.recommend(prefs, top_k=5)
        candidates = recommender.filter_candidates(prefs)
        latency_ms = (time.perf_counter() - t0) * 1000.0
    except NoEligiblePhonesError:
        candidates = pd.DataFrame()
        results = []
        latency_ms = 0.0
    except ZeroWeightsError:
        st.warning(
            "⚠️ **All preference weights are currently set to 0.0.** "
            "Please assign a positive weight to at least one dimension or click a preset in the sidebar."
        )
        return [], pd.DataFrame()
    except BudgetValidationError as err:
        st.error(f"🚨 **Budget Configuration Error:** {err}")
        return [], pd.DataFrame()

    if candidates.empty:
        st.markdown(build_no_candidates_html(), unsafe_allow_html=True)
        return [], candidates

    # Top Action Bar with Export Buttons and Live Inference Speed Pill
    h_col1, h_col2, h_col3 = st.columns([3, 1.2, 1.2])
    with h_col1:
        st.markdown(
            f"**Displaying Top {len(results)} Recommendations** "
            f"<span style='color: #94A3B8; font-size: 0.85rem;'>(Filtered from {len(candidates)} candidates | ⚡ Inference: {latency_ms:.1f}ms)</span>",
            unsafe_allow_html=True,
        )
    with h_col2:
        csv_data = export_recommendations_csv(results)
        st.download_button(
            label="📥 Export CSV",
            data=csv_data,
            file_name="smartpick_recommendations.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with h_col3:
        html_data = export_recommendations_html(results, prefs, metadata)
        st.download_button(
            label="📄 Export Report",
            data=html_data,
            file_name="smartpick_report.html",
            mime="text/html",
            use_container_width=True,
        )

    # Render Cards
    for rank, r in enumerate(results, start=1):
        render_recommendation_card(r, rank, lang_code)

    # What-If Sensitivity Simulator Expander
    st.markdown("---")
    with st.expander(
        "🧪 **What-If Sensitivity Simulator** — Real-time Rank Movement Analysis",
        expanded=False,
    ):
        st.markdown(
            "Understand how robust these top recommendations are to changes in your priorities. "
            "Select a dimension to boost and see simulated rank displacements (`▲` moved up, `▼` moved down, `=` stayed same)."
        )
        w_c1, w_c2, _ = st.columns([2, 2, 2])
        boost_dim = w_c1.selectbox(
            "Priority Dimension to Boost",
            options=["Performance", "Camera", "Battery", "Display", "Storage", "Value"],
            index=2,
        )
        boost_amt = w_c2.slider(
            "Boost Increment", min_value=0.10, max_value=0.50, value=0.30, step=0.05
        )

        movements = compute_what_if_movement(
            recommender=recommender,
            base_prefs=prefs,
            boost_dimension=boost_dim.lower(),
            boost_amount=boost_amt,
            top_k=min(5, len(results)),
        )

        mov_rows = []
        for m in movements:
            mov_rows.append(
                {
                    "Baseline Rank": f"#{m.original_rank}",
                    "Device Name": m.phone_name,
                    "Simulated Rank": f"#{m.simulated_rank}"
                    if m.simulated_rank
                    else "Unranked",
                    "Movement Indicator": f"{m.indicator}",
                    "Base Score": f"{m.original_score:.1f}",
                    "Simulated Score": f"{m.simulated_score:.1f}",
                }
            )

        st.dataframe(
            pd.DataFrame(mov_rows),
            use_container_width=True,
            hide_index=True,
        )

    return results, candidates


def render_tab_compare(
    catalog_df: pd.DataFrame,
    recommender: SmartPickRecommender,
    prefs: UserPreferences,
    results: list[RecommendationResult],
) -> None:
    """Render Tab 2: Multi-device side-by-side comparison matrix and radar chart."""
    st.markdown("### ⚖️ Side-by-Side Specification Comparison")

    try:
        candidates = recommender.filter_candidates(prefs)
        all_names = sorted(candidates["phone_name"].dropna().unique().tolist())
    except (NoEligiblePhonesError, ZeroWeightsError, BudgetValidationError):
        all_names = []

    raw_default = (
        st.session_state.compare_list
        if st.session_state.compare_list
        else [r.phone_name for r in results[:2]]
    )
    valid_default = [name for name in raw_default if name in all_names]

    chosen_names = st.multiselect(
        "Select 2 to 4 devices to compare:",
        options=all_names,
        default=valid_default,
        max_selections=4,
        help="Pick 2, 3, or 4 smartphones to compare specifications.",
    )
    st.session_state.compare_list = chosen_names

    if len(chosen_names) < 2:
        st.info(
            "👉 Please select at least **2 devices** (maximum 4) to generate the comparison matrix and radar chart."
        )
        return

    selected_results: list[RecommendationResult] = []
    for name in chosen_names:
        match = next((r for r in results if r.phone_name == name), None)
        if match:
            selected_results.append(match)
        else:
            single_df = catalog_df[catalog_df["phone_name"] == name]
            if not single_df.empty:
                res = recommender.rank_baseline(single_df, prefs, top_k=1)
                if res:
                    selected_results.append(res[0])

    if len(selected_results) < 2:
        st.warning("Could not assemble spec profiles for selected devices.")
        return

    # Render Phone Image Cards Header for Selected Devices
    cmp_cols = st.columns(len(selected_results))
    for i, r in enumerate(selected_results):
        with cmp_cols[i]:
            header_html = build_compare_column_header_html(
                phone_name=r.phone_name,
                brand=r.brand,
                price_str=format_inr(r.price_inr),
                image_path=r.image_path,
                attribution=r.image_attribution,
                license_str=r.image_license,
            )
            st.markdown(header_html, unsafe_allow_html=True)

    st.plotly_chart(render_radar_comparison(selected_results), use_container_width=True)

    spec_rows: list[dict[str, Any]] = [
        {"Feature": "Price (₹ INR)", "key": "price_inr", "is_min_better": True},
        {
            "Feature": "Match Score (0-100)",
            "key": "match_score",
            "is_min_better": False,
        },
        {
            "Feature": "Processor Benchmark",
            "key": "processor_score",
            "is_min_better": False,
        },
        {"Feature": "RAM (GB)", "key": "ram_gb", "is_min_better": False},
        {"Feature": "Storage (GB)", "key": "storage_gb", "is_min_better": False},
        {
            "Feature": "Battery Capacity (mAh)",
            "key": "battery_mah",
            "is_min_better": False,
        },
        {
            "Feature": "Camera Resolution (MP)",
            "key": "camera_mp",
            "is_min_better": False,
        },
        {
            "Feature": "Display Refresh Rate (Hz)",
            "key": "display_hz",
            "is_min_better": False,
        },
        {"Feature": "5G Connectivity", "key": "has_5g", "is_min_better": False},
    ]

    table_data: list[dict[str, str]] = []

    for row_spec in spec_rows:
        feat_name = str(row_spec["Feature"])
        feat_key = str(row_spec["key"])
        is_min = bool(row_spec["is_min_better"])

        vals = []
        for r in selected_results:
            if feat_key == "price_inr":
                v = r.price_inr
            elif feat_key == "match_score":
                v = r.match_score
            else:
                v = r.specs.get(feat_key)
            vals.append(v)

        numeric_vals = [
            float(v)
            for v in vals
            if v is not None and not pd.isna(v) and isinstance(v, (int, float))
        ]
        best_val = None
        if numeric_vals:
            best_val = min(numeric_vals) if is_min else max(numeric_vals)

        row_dict: dict[str, str] = {"Specification": feat_name}
        for idx, r in enumerate(selected_results):
            val = vals[idx]
            if val is None or pd.isna(val):
                display_str = "N/A"
            elif feat_key == "price_inr":
                display_str = format_inr(val)
            elif feat_key == "match_score":
                display_str = f"{val:.1f} pts"
            elif feat_key == "has_5g":
                display_str = "Yes ⚡" if val else "No"
            else:
                display_str = str(val)

            if (
                best_val is not None
                and val is not None
                and isinstance(val, (int, float))
                and val == best_val
            ):
                display_str = f"🏆 {display_str}"

            row_dict[r.phone_name] = display_str

        table_data.append(row_dict)

    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)


def render_tab_frontier(
    candidates_df: pd.DataFrame,
    recommender: SmartPickRecommender,
    results: list[RecommendationResult],
) -> None:
    """Render Tab 3: Value-for-Money Pareto Efficiency Frontier view."""
    st.markdown("### 💎 Value-for-Money: Price-vs-Specs Efficiency Frontier")

    if candidates_df.empty:
        st.info(
            "No candidates available under current budget window to compute Pareto frontier."
        )
        return

    frontier_df = compute_pareto_frontier(candidates_df, recommender.preprocessor)
    rec_names = [r.phone_name for r in results]

    st.plotly_chart(
        render_pareto_frontier_chart(frontier_df, rec_names), use_container_width=True
    )

    with st.expander(
        "📖 Microeconomic Methodology: What is the Pareto Efficiency Frontier?",
        expanded=False,
    ):
        st.markdown(
            textwrap.dedent(
                """
                In microeconomics and multi-objective decision theory, a smartphone is **Pareto Optimal** (on the efficiency frontier)
                if **no other available smartphone offers superior composite hardware specifications at an equal or lower price**.

                - **Non-dominated points (💎 Emerald Diamonds)**: Represent the maximum specification return per rupee invested.
                - **Dominated points (Slate circles)**: There exists at least one alternative phone that costs less and offers higher specs.
                - **Composite Hardware Score (0-100)**: Formed by normalizing processor throughput, battery capacity, camera resolution,
                  display refresh frequency, RAM, and internal flash storage using our outlier-resilient clipping scaler.
                """
            ).strip()
        )

    # Table of Pareto-optimal devices
    frontier_only = frontier_df[frontier_df["is_pareto_optimal"]].sort_values(
        "price_inr"
    )
    st.markdown("#### 🏆 Pareto-Optimal Devices in Current Budget Window")
    display_cols = [
        "phone_name",
        "brand",
        "price_inr",
        "hardware_score",
        "ram_gb",
        "storage_gb",
        "battery_mah",
        "camera_mp",
        "display_hz",
    ]
    available_disp = [c for c in display_cols if c in frontier_only.columns]

    formatted_df = frontier_only[available_disp].copy()
    formatted_df["price_inr"] = formatted_df["price_inr"].apply(format_inr)
    st.dataframe(formatted_df, use_container_width=True, hide_index=True)


def render_tab_why_not(
    catalog_df: pd.DataFrame,
    recommender: SmartPickRecommender,
    prefs: UserPreferences,
    results: list[RecommendationResult],
) -> None:
    """Render Tab 4: Counterfactual 'Why NOT this phone' explainer."""
    st.markdown("### 🔍 'Why NOT This Phone?' — Counterfactual Analysis")
    st.markdown(
        "Select any smartphone from our entire catalog to inspect why the recommendation engine "
        "either filtered it out or ranked it below your Top 5 shortlists."
    )

    all_catalog_names = sorted(catalog_df["phone_name"].dropna().unique().tolist())
    top_5_names = [r.phone_name for r in results]
    default_inspect = next(
        (n for n in all_catalog_names if n not in top_5_names), all_catalog_names[0]
    )

    inspected_phone = st.selectbox(
        "Select Smartphone to Inspect:",
        options=all_catalog_names,
        index=all_catalog_names.index(default_inspect)
        if default_inspect in all_catalog_names
        else 0,
        help="Pick any device to evaluate its exact deficits against your active criteria.",
    )

    if inspected_phone:
        reason = explain_why_not_phone(inspected_phone, recommender, prefs, results)

        # Category Badge
        cat_labels = {
            "already_top_5": ("⭐ SHORTLISTED", "#2563EB"),
            "budget_violation": ("🚫 BUDGET VIOLATION", "#EF4444"),
            "brand_filtered": ("🏷️ BRAND EXCLUDED", "#F59E0B"),
            "5g_missing": ("⚡ 4G ONLY / 5G MISSING", "#F59E0B"),
            "score_deficit": ("📉 PREFERENCE SCORE DEFICIT", "#8B5CF6"),
        }
        badge_txt, badge_col = cat_labels.get(reason.category, ("EXCLUDED", "#64748B"))

        why_not_html = build_why_not_card_html(
            phone_name=reason.phone_name,
            price_inr=reason.price_inr,
            formatted_price=format_inr(reason.price_inr),
            badge_txt=badge_txt,
            badge_col=badge_col,
            primary_reason=reason.primary_reason,
        )
        st.markdown(why_not_html, unsafe_allow_html=True)

        if reason.detailed_deficits:
            st.markdown("#### 📋 Detailed Specification Deficits (vs. Top-5 Medians)")
            for d in reason.detailed_deficits:
                st.markdown(f"- {d}")


def render_tab_insights(
    catalog_df: pd.DataFrame,
    prefs: UserPreferences,
    results: list[RecommendationResult],
) -> None:
    """Render Tab 5: Visual market insights, score decomposition, and price distributions."""
    st.markdown("### 📈 Visual Market Insights & Preference Allocation")

    rec_names = [r.phone_name for r in results]

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            render_price_distribution(catalog_df, prefs.min_budget, prefs.max_budget),
            use_container_width=True,
        )
    with c2:
        st.plotly_chart(
            render_price_vs_battery_scatter(catalog_df, rec_names),
            use_container_width=True,
        )

    if results:
        st.plotly_chart(render_contribution_bar(results), use_container_width=True)

    c3, _ = st.columns([1, 1])
    with c3:
        st.plotly_chart(render_weight_profile(prefs), use_container_width=True)


def render_tab_evaluation() -> None:
    """Render Tab 6: Offline evaluation benchmarks, ablation results, and sensitivity analysis."""
    st.markdown("### 🔬 Empirical Evaluation & Algorithmic Ablation Study")

    st.markdown(
        """
        > **Direct Honesty Directive (TRD Section 7 & TC-11)**:
        > SmartPick AI strictly distinguishes between **multi-attribute ranking heuristics** and **supervised ML models**.
        > Information retrieval metrics (Precision@K, Recall@K, NDCG@K) require ground-truth relevance judgements.
        > Below we present verified ablation results against our documented benchmark set (`data/synthetic_relevance_benchmark.csv`).
        """
    )

    eval_doc_path = Path("docs/EVALUATION.md")
    if eval_doc_path.exists():
        content = eval_doc_path.read_text(encoding="utf-8")
        st.markdown(content)
    else:
        st.info("Evaluation report `docs/EVALUATION.md` is being generated...")


def render_tab_about(
    summary: QualitySummary,
    metadata: DatasetMetadata,
) -> None:
    """Render Tab 7: Catalog data dictionary, provenance logs, and algorithmic disclosures."""
    st.markdown("### ℹ️ Architecture, Data Dictionary & Trust Framework")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📋 Catalog Health Overview")
        st.markdown(
            textwrap.dedent(
                f"""
                - **Total Records Ingested**: `{summary.total_records}`
                - **Valid Recommendable Devices**: `{summary.valid_records}`
                - **Overall Spec Completeness**: `{summary.overall_completeness_pct}%`
                - **Manufacturers Represented**: `{summary.brand_count}`
                - **Catalog Median Price**: `{format_inr(summary.price_median)}`
                - **Duplicate Audit**: `{summary.exact_duplicates}` exact duplicates flagged; `{summary.hardware_variants}` valid RAM/Storage variants retained.
                """
            ).strip()
        )

    with c2:
        st.markdown("#### 📐 Mathematical Ranking Specifications")
        st.markdown(
            textwrap.dedent(
                r"""
                - **1. Baseline Heuristic (TRD 6.1)**:
                  $$\text{Score}(d) = \frac{\sum_{i \in \text{active}} w_i \cdot s_i(d)}{\sum_{i \in \text{active}} w_i} \times 100$$
                - **2. Content Similarity (TRD 6.2)**:
                  Cosine angle between candidate spec vector and user profile vector.
                - **3. Blended Hybrid (TRD 6.3)**:
                  $$\text{Score}_{\text{blend}} = (1 - \alpha)\text{Score}_{\text{base}} + \alpha\text{Score}_{\text{sim}}$$
                - **4. MMR Diversity (TRD 6.3)**:
                  $$\text{MMR}(d) = \lambda \cdot \text{Rel}(d) - (1 - \lambda) \max_{s \in S} \text{Sim}(d, s)$$
                - **Missing Value Policy**: Excluded for that phone; active weights renormalized to $1.0$. No zeros invented.
                """
            ).strip()
        )

    st.markdown("---")
    st.markdown("#### 📚 Canonical Data Dictionary")
    dict_data = [
        {
            "Column": "phone_name",
            "Type": "string",
            "Constraint": "Required, Non-empty",
            "Description": "Manufacturer brand and model designation",
        },
        {
            "Column": "brand",
            "Type": "string",
            "Constraint": "Extracted",
            "Description": "Normalized manufacturer name (e.g. Apple, Samsung, OnePlus)",
        },
        {
            "Column": "price_inr",
            "Type": "float",
            "Constraint": "Required, > 0",
            "Description": "Retail price in Indian Rupees (₹ INR)",
        },
        {
            "Column": "ram_gb",
            "Type": "float",
            "Constraint": "Optional (NaN allowed)",
            "Description": "Random Access Memory in Gigabytes",
        },
        {
            "Column": "storage_gb",
            "Type": "float",
            "Constraint": "Optional (NaN allowed)",
            "Description": "Internal flash storage capacity in Gigabytes",
        },
        {
            "Column": "battery_mah",
            "Type": "float",
            "Constraint": "Optional (NaN allowed)",
            "Description": "Battery cell capacity in milliampere-hours",
        },
        {
            "Column": "camera_mp",
            "Type": "float",
            "Constraint": "Optional (NaN allowed)",
            "Description": "Primary rear camera sensor resolution in Megapixels",
        },
        {
            "Column": "display_hz",
            "Type": "float",
            "Constraint": "Optional (NaN allowed)",
            "Description": "Display refresh frequency (e.g. 60, 90, 120, 144 Hz)",
        },
        {
            "Column": "has_5g",
            "Type": "boolean",
            "Constraint": "Optional (NaN allowed)",
            "Description": "Fifth-generation cellular network support",
        },
        {
            "Column": "processor_score",
            "Type": "float",
            "Constraint": "Optional (NaN allowed)",
            "Description": "Composite AnTuTu/Geekbench benchmark throughput",
        },
        {
            "Column": "image_path",
            "Type": "string",
            "Constraint": "Optional (assets/phones/)",
            "Description": "Local verified WebP image or SVG silhouette path",
        },
        {
            "Column": "image_source",
            "Type": "string",
            "Constraint": "Optional",
            "Description": "Source archive (e.g. Wikimedia Commons official API)",
        },
        {
            "Column": "image_license",
            "Type": "string",
            "Constraint": "Optional",
            "Description": "Legal distribution licence (CC BY-SA 4.0, Public Domain)",
        },
        {
            "Column": "image_attribution",
            "Type": "string",
            "Constraint": "Optional",
            "Description": "Photographer credit and copyright provenance",
        },
    ]
    st.dataframe(pd.DataFrame(dict_data), use_container_width=True, hide_index=True)

    with st.expander("📸 Smartphone Imagery Provenance & Licensing"):
        st.markdown(
            textwrap.dedent(
                """
                SmartPick AI strictly follows data integrity and ethical licensing standards:
                - **Zero Scraping:** No web scraping of e-commerce, Google Images, or copyright-restricted catalogs.
                - **Zero Hotlinking:** All media assets are stored locally under `assets/phones/` and served via self-contained Data URIs to eliminate external HTTP dependencies.
                - **Licensed Photography:** Real smartphone images are sourced strictly from Wikimedia Commons via its official API under Creative Commons (CC BY, CC BY-SA) or Public Domain licences.
                - **Procedural SVG Fallback:** Catalog devices without public-domain photographs display clean SVG silhouettes with manufacturer brand color accents (`#0F172A` frame).
                """
            ).strip()
        )


def render_footer() -> None:
    """Render persistent legal disclaimer and transparency notice across all views."""
    st.markdown(build_footer_html(), unsafe_allow_html=True)


def main() -> None:
    """Render application shell and presentation layout."""
    configure_page()

    version_hash = get_dataset_version()

    try:
        catalog_df, metadata, summary, recommender = load_catalog_and_engine(
            version_hash
        )
    except SmartPickError as err:
        st.error(f"Catalog Configuration Error: {err}")
        return
    except (OSError, ValueError) as err:
        logger.exception("Unexpected runtime error while initializing catalog")
        st.error(f"Failed to load dataset: {err}")
        return

    init_session_state(catalog_df)
    lang_code = "hi" if st.session_state.ui_lang == "Hinglish" else "en"

    render_hero(summary, metadata, lang_code, version_hash)

    try:
        prefs = render_sidebar(catalog_df, lang_code)
    except ZeroWeightsError:
        st.warning(
            "⚠️ **All preference weights are currently set to 0.0.** "
            "Please assign a positive weight to at least one dimension or click a preset in the sidebar."
        )
        render_footer()
        return
    except BudgetValidationError as err:
        st.error(f"🚨 **Budget Configuration Error:** {err}")
        render_footer()
        return

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            get_text("tab_recommendations", lang=lang_code),
            get_text("tab_compare", lang=lang_code),
            get_text("tab_frontier", lang=lang_code),
            get_text("tab_why_not", lang=lang_code),
            get_text("tab_insights", lang=lang_code),
            get_text("tab_evaluation", lang=lang_code),
            get_text("tab_about", lang=lang_code),
        ]
    )

    results: list[RecommendationResult] = []
    candidates_df: pd.DataFrame = pd.DataFrame()

    with tab1:
        results, candidates_df = render_tab_recommendations(
            recommender, prefs, metadata, lang_code
        )

    with tab2:
        render_tab_compare(catalog_df, recommender, prefs, results)

    with tab3:
        render_tab_frontier(candidates_df, recommender, results)

    with tab4:
        render_tab_why_not(catalog_df, recommender, prefs, results)

    with tab5:
        render_tab_insights(catalog_df, prefs, results)

    with tab6:
        render_tab_evaluation()

    with tab7:
        render_tab_about(summary, metadata)

    render_footer()


if __name__ == "__main__":
    main()
