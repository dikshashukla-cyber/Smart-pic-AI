"""Unit tests for 'Why NOT this phone' counterfactual explainability engine."""

import pytest

from src.counterfactual import explain_why_not_phone
from src.data_loader import DataLoader
from src.preprocessing import FeaturePreprocessor
from src.recommender import SmartPickRecommender, UserPreferences


@pytest.fixture(scope="module")
def recommender_instance() -> SmartPickRecommender:
    """Fixture providing initialized SmartPickRecommender with canonical catalog."""
    loader = DataLoader("data/phones.csv")
    df, _ = loader.load_and_validate()
    preprocessor = FeaturePreprocessor(strategy="robust_minmax")
    preprocessor.fit(df)
    return SmartPickRecommender(df, preprocessor)


def test_why_not_budget_exceeded(recommender_instance: SmartPickRecommender) -> None:
    """Verify phone priced above max_budget reports budget violation with exact numbers."""
    prefs = UserPreferences(
        min_budget=10000.0,
        max_budget=30000.0,
        weight_performance=0.5,
    )
    candidates = recommender_instance.filter_candidates(prefs)
    top_5 = recommender_instance.rank_baseline(candidates, prefs, top_k=5)

    # Samsung Galaxy S24 Ultra is ~129,999 INR (well above 30k)
    reason = explain_why_not_phone(
        "Samsung Galaxy S24 Ultra 5G", recommender_instance, prefs, top_5
    )
    assert reason.category == "budget_violation"
    assert "Disqualified by Hard Budget Constraint" in reason.primary_reason
    assert "₹129,999" in reason.primary_reason
    assert len(reason.detailed_deficits) >= 2


def test_why_not_budget_below_min(recommender_instance: SmartPickRecommender) -> None:
    """Verify phone priced below min_budget reports lower bound exclusion."""
    prefs = UserPreferences(
        min_budget=40000.0,
        max_budget=80000.0,
        weight_performance=0.5,
    )
    candidates = recommender_instance.filter_candidates(prefs)
    top_5 = recommender_instance.rank_baseline(candidates, prefs, top_k=5)

    # Redmi 13C is ~10,499 INR (well below 40k)
    reason = explain_why_not_phone("Redmi 13C 5G", recommender_instance, prefs, top_5)
    assert reason.category == "budget_violation"
    assert "Excluded by Minimum Budget Bound" in reason.primary_reason


def test_why_not_brand_filtered(recommender_instance: SmartPickRecommender) -> None:
    """Verify phone excluded by active brand filter is clearly reported."""
    prefs = UserPreferences(
        min_budget=10000.0,
        max_budget=40000.0,
        preferred_brands=["Motorola"],
        weight_performance=0.5,
    )
    candidates = recommender_instance.filter_candidates(prefs)
    top_5 = recommender_instance.rank_baseline(candidates, prefs, top_k=5)

    # POCO M6 Pro is in budget (10999 INR) but brand is POCO, not Motorola
    reason = explain_why_not_phone("POCO M6 Pro 5G", recommender_instance, prefs, top_5)
    assert reason.category == "brand_filtered"
    assert "Excluded by Manufacturer Filter" in reason.primary_reason
    assert "Motorola" in reason.primary_reason


def test_why_not_already_in_top_5(recommender_instance: SmartPickRecommender) -> None:
    """Verify device already in top 5 is reported as already shortlisted."""
    prefs = UserPreferences(
        min_budget=10000.0,
        max_budget=50000.0,
        weight_performance=0.5,
    )
    candidates = recommender_instance.filter_candidates(prefs)
    top_5 = recommender_instance.rank_baseline(candidates, prefs, top_k=5)

    top_phone = top_5[0].phone_name
    reason = explain_why_not_phone(top_phone, recommender_instance, prefs, top_5)
    assert reason.category == "already_top_5"
    assert "already shortlisted" in reason.primary_reason
    assert reason.rank == 1


def test_why_not_score_deficit(recommender_instance: SmartPickRecommender) -> None:
    """Verify eligible device outranked by Top 5 reports score deficit and dimension gaps."""
    prefs = UserPreferences(
        min_budget=10000.0,
        max_budget=30000.0,
        weight_performance=0.9,
        weight_battery=0.8,
    )
    candidates = recommender_instance.filter_candidates(prefs)
    all_ranked = recommender_instance.rank_baseline(
        candidates, prefs, top_k=len(candidates)
    )
    top_5 = all_ranked[:5]

    # Pick a device ranked lower (e.g. rank 10 or 15)
    if len(all_ranked) > 5:
        lower_phone = all_ranked[6].phone_name
        reason = explain_why_not_phone(lower_phone, recommender_instance, prefs, top_5)
        assert reason.category == "score_deficit"
        assert reason.rank == 7
        assert reason.score_gap is not None
        assert reason.score_gap >= 0
        assert len(reason.detailed_deficits) > 0


def test_why_not_5g_required_missing(
    recommender_instance: SmartPickRecommender,
) -> None:
    """Verify 4G device is reported as excluded when 5G is required."""
    df = recommender_instance.catalog_df
    four_g_phones = df[df["has_5g"] == False]
    if not four_g_phones.empty:
        phone_name = four_g_phones.iloc[0]["phone_name"]
        price = float(four_g_phones.iloc[0]["price_inr"])
        prefs = UserPreferences(
            min_budget=max(0, price - 2000),
            max_budget=price + 2000,
            require_5g=True,
        )
        candidates = recommender_instance.filter_candidates(prefs)
        top_5 = (
            recommender_instance.rank_baseline(candidates, prefs, top_k=5)
            if not candidates.empty
            else []
        )
        reason = explain_why_not_phone(phone_name, recommender_instance, prefs, top_5)
        assert reason.category == "5g_missing"
        assert "5G" in reason.primary_reason
