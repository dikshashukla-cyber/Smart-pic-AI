"""Internationalization (i18n) module for SmartPick AI.

Provides bilingual English and Hinglish UI dictionary for key labels,
headings, explanations, and metric descriptions.
"""

from typing import Literal

Language = Literal["en", "hi"]

TRANSLATIONS: dict[str, dict[Language, str]] = {
    "app_title": {
        "en": "SmartPick AI",
        "hi": "SmartPick AI — Smart Mobile Recommender",
    },
    "app_subtitle": {
        "en": "Intelligent Smartphone Recommender — Specification-Grounded, Mathematically Transparent Shortlists",
        "hi": "Aapka Personal Smart Mobile Guide — Specifications Par Aadharit, Transparent Recommender",
    },
    "catalog_status": {
        "en": "Catalog Status",
        "hi": "Catalog Ki Halat",
    },
    "verified_recent": {
        "en": "Verified",
        "hi": "Verify Kiya Gaya",
    },
    "quick_presets": {
        "en": "⚡ Quick Presets",
        "hi": "⚡ Fast Presets (Seedha Chunein)",
    },
    "budget_window": {
        "en": "💰 Budget Window (₹ INR)",
        "hi": "💰 Budget Ki Range (₹ INR)",
    },
    "priority_dimensions": {
        "en": "🎯 Priority Dimensions (0.0 to 1.0)",
        "hi": "🎯 Aapki Zarooratein (Kitna Important Hai)",
    },
    "dim_perf": {
        "en": "🚀 Performance / Gaming",
        "hi": "🚀 Speed aur Gaming Power",
    },
    "dim_cam": {
        "en": "📸 Camera Resolution",
        "hi": "📸 Camera Quality (Megapixels)",
    },
    "dim_bat": {
        "en": "🔋 Battery Capacity",
        "hi": "🔋 Battery Backup (mAh)",
    },
    "dim_disp": {
        "en": "📺 Display Refresh Rate",
        "hi": "📺 Smooth Display (Hz)",
    },
    "dim_stor": {
        "en": "💾 Storage Space",
        "hi": "💾 Storage (GB)",
    },
    "dim_val": {
        "en": "💎 Value for Money",
        "hi": "💎 Paisa Vasool (Spec-to-Price)",
    },
    "brand_filter": {
        "en": "Brand Filter",
        "hi": "Brand Chunein",
    },
    "require_5g": {
        "en": "Require 5G Connectivity",
        "hi": "Sirf 5G Phone Dikhayein",
    },
    "ranking_engine_mode": {
        "en": "Ranking Engine Mode",
        "hi": "Ranking Ka Tarika",
    },
    "reset_profile": {
        "en": "🔄 Reset to Default Profile",
        "hi": "🔄 Shuru Se Shuru Karein (Reset)",
    },
    "tab_recommendations": {
        "en": "🎯 Recommendations",
        "hi": "🎯 Top Phones",
    },
    "tab_compare": {
        "en": "⚖️ Compare",
        "hi": "⚖️ Aamne-Saamne Compare",
    },
    "tab_frontier": {
        "en": "💎 Value Frontier (Pareto)",
        "hi": "💎 Paisa Vasool Frontier",
    },
    "tab_why_not": {
        "en": "🔍 Why NOT This Phone?",
        "hi": "🔍 Yeh Phone Kyu Nahi Chuna?",
    },
    "tab_insights": {
        "en": "📈 Insights",
        "hi": "📈 Market Charts",
    },
    "tab_evaluation": {
        "en": "🔬 Evaluation",
        "hi": "🔬 Test & Benchmarks",
    },
    "tab_about": {
        "en": "ℹ️ About & Data",
        "hi": "ℹ️ Data aur Niyam",
    },
    "top_match": {
        "en": "TOP MATCH",
        "hi": "SABSE BEST MATCH",
    },
    "shortlisted": {
        "en": "SHORTLISTED",
        "hi": "RECOMMENDED",
    },
    "why_this_device": {
        "en": "💡 Why this device:",
        "hi": "💡 Yeh phone kyu chunein:",
    },
    "trade_offs": {
        "en": "⚖️ Trade-off Considerations:",
        "hi": "⚖️ Dhyan Dene Wali Baatein (Trade-offs):",
    },
    "add_to_compare": {
        "en": "Add to Compare",
        "hi": "Compare List Mein Dalein",
    },
    "find_similar": {
        "en": "🔍 Find Similar",
        "hi": "🔍 Aise Aur Phone Dikhayein",
    },
    "within_budget": {
        "en": "✓ Within Budget",
        "hi": "✓ Budget Ke Andar",
    },
    "match_score_label": {
        "en": "Match Score (Relative Heuristic Index)",
        "hi": "Fit Score (Aapke Preferences Ke Mutabiq)",
    },
}


def get_text(key: str, lang: Language = "en") -> str:
    """Retrieve localized text for a key with English fallback."""
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key.replace("_", " ").title()
    return entry.get(lang, entry.get("en", key))
