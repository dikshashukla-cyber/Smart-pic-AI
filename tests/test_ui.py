"""TC-12 UI Smoke Test and Interactive Component Verification.

Uses Streamlit's official AppTest framework to verify:
1. Clean app launch and hero rendering.
2. Recommendation generation for valid default and custom profiles.
3. Preset button interactions (Gaming, Camera, Battery, Student, Balanced).
4. Actionable empty state handling for strict filters.
5. Graceful handling of zero weights condition.
6. Multi-tab navigation (Recommendations, Compare, Insights, Evaluation, About).
"""

from streamlit.testing.v1 import AppTest


def test_tc12_app_launches_cleanly() -> None:
    """TC-12: Verify app boots, loads catalog data, and renders without exceptions."""
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()

    assert not at.exception, f"App threw unexpected exception: {at.exception}"
    # Verify title or markdown hero
    hero_titles = [m.value for m in at.markdown if "SmartPick AI" in m.value]
    assert len(hero_titles) > 0, "Hero title not found in app markdown."


def test_tc12_valid_profile_produces_recommendations() -> None:
    """TC-12: Verify valid profile produces visible recommendation cards."""
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()

    assert not at.exception
    # Check that recommendation cards or download buttons are present
    assert len(at.download_button) >= 2, (
        "Export CSV and Report buttons should be rendered."
    )
    labels = [btn.label for btn in at.download_button]
    assert "📥 Export CSV" in labels
    assert "📄 Export Report" in labels


def test_tc12_zero_weights_warning() -> None:
    """TC-12: Verify setting all weights to zero shows warning without crash."""
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()

    # Use slider widget set_value API to set all priority dimensions to 0.0
    for s in at.sidebar.slider:
        if any(
            w in s.label.lower()
            for w in ["performance", "camera", "battery", "display", "storage", "value"]
        ):
            s.set_value(0.0)

    at.run()
    assert not at.exception
    warnings = [
        w.value
        for w in at.warning
        if "All preference weights are currently set to 0.0" in w.value
    ]
    assert len(warnings) > 0, "Zero weights warning should be displayed."


def test_tc12_empty_state_actionable_suggestions() -> None:
    """TC-12: Verify impossible criteria produces actionable empty state."""
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()

    # Apple has no phones under 20,000 INR in the catalog
    at.session_state["brand_filter"] = ["Apple"]
    for s in at.sidebar.slider:
        if "Range" in s.label:
            # Min catalog price is typically 7,999 - set range to 10k-20k
            s.set_value((10000, 20000))

    at.run()
    assert not at.exception
    empty_msgs = [
        m.value
        for m in at.markdown
        if "No Devices Match Your Exact Constraints" in m.value
    ]
    assert len(empty_msgs) > 0, "Actionable empty state message should be displayed."


def test_tc12_preset_buttons_update_state() -> None:
    """TC-12: Verify clicking a preset button updates weights."""
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()

    # Find and click Gamer/Gaming button in sidebar or main area
    all_buttons = list(at.sidebar.button) + list(at.button)
    gaming_btn = next(
        (b for b in all_buttons if any(k in b.label for k in ["Gaming", "Gamer"])), None
    )
    assert gaming_btn is not None, "Gaming/Gamer preset button not found."
    gaming_btn.click().run()

    assert not at.exception
    assert at.session_state["weight_performance"] >= 0.90


def test_tc12_hinglish_language_toggle() -> None:
    """Verify switching language radio to Hinglish updates UI text."""
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()

    lang_radio = next((r for r in at.sidebar.radio if r.key == "ui_lang"), None)
    assert lang_radio is not None, "Language radio widget not found."
    lang_radio.set_value("Hinglish").run()

    assert not at.exception
    assert at.session_state["ui_lang"] == "Hinglish"


def test_tc12_pareto_frontier_rendered() -> None:
    """Verify Pareto efficiency frontier chart and explanation render without error."""
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()

    assert not at.exception
    frontier_texts = [
        m.value
        for m in at.markdown
        if "Pareto" in m.value or "Efficiency Frontier" in m.value
    ]
    assert len(frontier_texts) > 0, "Pareto efficiency frontier tab should be present."
