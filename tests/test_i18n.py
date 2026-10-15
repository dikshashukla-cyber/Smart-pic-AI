"""Unit tests for bilingual English and Hinglish i18n dictionary."""

from src.i18n import get_text


def test_i18n_english_retrieval() -> None:
    """Verify standard English label retrieval."""
    assert get_text("budget_window", lang="en") == "💰 Budget Window (₹ INR)"
    assert get_text("tab_recommendations", lang="en") == "🎯 Recommendations"
    assert get_text("add_to_compare", lang="en") == "Add to Compare"


def test_i18n_hinglish_retrieval() -> None:
    """Verify localized Hinglish label retrieval."""
    assert "Budget Ki Range" in get_text("budget_window", lang="hi")
    assert "Top Phones" in get_text("tab_recommendations", lang="hi")
    assert "Compare" in get_text("add_to_compare", lang="hi")


def test_i18n_unknown_key_fallback() -> None:
    """Verify unknown keys fall back gracefully to title-cased key string."""
    assert get_text("unknown_feature_button", lang="hi") == "Unknown Feature Button"
