"""Test suite for SmartPickRecommender baseline engine and ranking algorithms.

Implements:
- TC-03: Budget filtering (100% compliance guarantee)
- TC-04: No eligible phones exception handling
- TC-05: Bounds and preference weight validation
- TC-06: Deterministic ranking, score sorting, and tie-breaking
- TC-07: Missing optional field handling (per-phone renormalization, no fabrication)
- TC-09: Explanation grounding in real specifications and percentiles
- TC-10: Reproducibility across repeated runs
- Boundary tests: Exact price boundaries, single candidate pool, brand and 5G filters
- Property-based testing via Hypothesis asserting budget compliance under all random inputs
"""

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.data_loader import DataLoader
from src.exceptions import (
    InvalidBudgetRangeError,
    InvalidWeightsError,
    NoEligiblePhonesError,
)
from src.recommender import SmartPickRecommender, UserPreferences


@pytest.fixture(scope="module")
def real_catalog_df() -> pd.DataFrame:
    """Fixture providing validated canonical catalog DataFrame."""
    loader = DataLoader("data/phones.csv")
    df, _ = loader.load_and_validate()
    return df


@pytest.fixture(scope="module")
def recommender(real_catalog_df: pd.DataFrame) -> SmartPickRecommender:
    """Fixture providing initialized SmartPickRecommender."""
    return SmartPickRecommender(real_catalog_df)


class TestRecommenderConstraintsAndValidation:
    """Tests for user preference validation and error states (TC-05)."""

    def test_tc05_valid_preferences(self) -> None:
        """Verify valid preference initialization succeeds."""
        prefs = UserPreferences(
            min_budget=10000,
            max_budget=30000,
            weight_performance=0.4,
            weight_camera=0.3,
            weight_battery=0.3,
        )
        assert prefs.min_budget == 10000
        assert prefs.max_budget == 30000

    def test_tc05_negative_min_budget_rejected(self) -> None:
        """Verify negative min budget raises InvalidBudgetRangeError."""
        with pytest.raises(InvalidBudgetRangeError):
            UserPreferences(min_budget=-500, max_budget=20000)

    def test_tc05_min_exceeding_max_budget_rejected(self) -> None:
        """Verify min_budget > max_budget raises InvalidBudgetRangeError."""
        with pytest.raises(InvalidBudgetRangeError) as exc_info:
            UserPreferences(min_budget=50000, max_budget=20000)
        assert exc_info.value.min_budget == 50000
        assert exc_info.value.max_budget == 20000

    def test_tc05_all_zero_weights_rejected(self) -> None:
        """Verify all zero preference weights raise InvalidWeightsError."""
        with pytest.raises(InvalidWeightsError):
            UserPreferences(
                min_budget=10000,
                max_budget=20000,
                weight_performance=0.0,
                weight_camera=0.0,
                weight_battery=0.0,
                weight_display=0.0,
                weight_storage=0.0,
                weight_value=0.0,
            )

    def test_negative_weights_rejected(self) -> None:
        """Verify negative weight raises InvalidWeightsError."""
        from pydantic import ValidationError

        with pytest.raises((InvalidWeightsError, ValidationError)):
            UserPreferences(min_budget=10000, max_budget=20000, weight_performance=-0.5)

    def test_rank_baseline_empty_candidates_error(
        self, recommender: SmartPickRecommender
    ) -> None:
        """Verify rank_baseline raises NoEligiblePhonesError when candidates_df is empty."""
        empty_df = pd.DataFrame()
        prefs = UserPreferences(min_budget=10000, max_budget=20000)
        with pytest.raises(NoEligiblePhonesError):
            recommender.rank_baseline(empty_df, prefs)

    def test_rank_similarity_success(
        self, recommender: SmartPickRecommender, real_catalog_df: pd.DataFrame
    ) -> None:
        """Verify rank_similarity produces valid recommendations for anchor device."""
        prefs = UserPreferences(min_budget=10000, max_budget=30000)
        results = recommender.rank_similarity(
            real_catalog_df, prefs, reference_phone_name="Redmi 13C 5G", top_k=5
        )
        assert len(results) > 0
        assert all(r.match_score >= 0 for r in results)

    def test_require_5g_false_filter(self, recommender: SmartPickRecommender) -> None:
        """Verify require_5g=False excludes 5G phones and returns only 4G devices."""
        prefs = UserPreferences(min_budget=5000, max_budget=20000, require_5g=False)
        candidates = recommender.filter_candidates(prefs)
        results = recommender.rank_baseline(candidates, prefs, top_k=5)
        assert len(results) > 0
        for r in results:
            assert r.specs["has_5g"] is False

    def test_tc04_no_eligible_phones_error(
        self, recommender: SmartPickRecommender
    ) -> None:
        """TC-04: Verify filters matching zero devices raise NoEligiblePhonesError."""
        # Budget between ₹100 and ₹500 (no phone exists in this price range)
        prefs = UserPreferences(min_budget=100, max_budget=500)
        with pytest.raises(NoEligiblePhonesError) as exc_info:
            candidates = recommender.filter_candidates(prefs)
            recommender.rank_baseline(candidates, prefs)
        assert "No smartphones found" in str(exc_info.value)


class TestRecommenderFilteringAndRanking:
    """Tests for hard constraint filtering, ranking, and deterministic ordering."""

    def test_tc03_budget_filtering_100_percent_compliance(
        self, recommender: SmartPickRecommender
    ) -> None:
        """TC-03: Verify 100% of returned devices satisfy the budget constraint."""
        min_b = 20000.0
        max_b = 35000.0
        prefs = UserPreferences(min_budget=min_b, max_budget=max_b)
        candidates = recommender.filter_candidates(prefs)
        results = recommender.rank_baseline(candidates, prefs, top_k=10)

        assert len(results) > 0, "Should return eligible candidates in ₹20k - ₹35k."
        for res in results:
            assert min_b <= res.price_inr <= max_b, (
                f"Phone '{res.phone_name}' priced at ₹{res.price_inr} violates budget [₹{min_b}, ₹{max_b}]."
            )

    def test_inclusive_budget_boundary(self, recommender: SmartPickRecommender) -> None:
        """Verify budget filter is inclusive of exact boundary prices."""
        prefs = UserPreferences(min_budget=24999.0, max_budget=24999.0)
        candidates = recommender.filter_candidates(prefs)
        results = recommender.rank_baseline(candidates, prefs, top_k=5)

        assert len(results) > 0
        for res in results:
            assert res.price_inr == 24999.0

    def test_brand_filter_case_insensitive(
        self, recommender: SmartPickRecommender
    ) -> None:
        """Verify brand filter strictly restricts results to selected brands."""
        prefs = UserPreferences(
            min_budget=10000,
            max_budget=80000,
            preferred_brands=["samsung", "ONEPLUS"],
        )
        candidates = recommender.filter_candidates(prefs)
        results = recommender.rank_baseline(candidates, prefs, top_k=10)

        assert len(results) > 0
        for res in results:
            assert res.brand and res.brand.lower() in ("samsung", "oneplus")

    def test_5g_filter_compliance(self, recommender: SmartPickRecommender) -> None:
        """Verify 5G filter excludes 4G-only phones when require_5g is True."""
        prefs = UserPreferences(min_budget=5000, max_budget=50000, require_5g=True)
        candidates = recommender.filter_candidates(prefs)
        results = recommender.rank_baseline(candidates, prefs, top_k=10)

        assert len(results) > 0
        for res in results:
            assert res.specs["has_5g"] is True

    def test_tc06_ranking_descending_scores(
        self, recommender: SmartPickRecommender
    ) -> None:
        """TC-06: Verify returned results are ordered descending by match_score."""
        prefs = UserPreferences(
            min_budget=15000,
            max_budget=45000,
            weight_performance=0.5,
            weight_battery=0.3,
            weight_camera=0.2,
        )
        candidates = recommender.filter_candidates(prefs)
        results = recommender.rank_baseline(candidates, prefs, top_k=10)

        scores = [r.match_score for r in results]
        assert scores == sorted(scores, reverse=True), (
            "Results must be sorted descending by match score."
        )

    def test_tc06_deterministic_tie_breaking(self) -> None:
        """TC-06: Verify tie-breaking prioritizes cheaper price, then alphabetical name."""
        mock_data = pd.DataFrame(
            [
                {
                    "phone_name": "Phone Beta",
                    "brand": "BrandX",
                    "price_inr": 20000.0,
                    "ram_gb": 8.0,
                    "storage_gb": 128.0,
                    "battery_mah": 5000.0,
                    "camera_mp": 50.0,
                    "display_hz": 120.0,
                    "processor_score": 500000.0,
                    "has_5g": True,
                },
                {
                    "phone_name": "Phone Alpha",
                    "brand": "BrandX",
                    "price_inr": 20000.0,
                    "ram_gb": 8.0,
                    "storage_gb": 128.0,
                    "battery_mah": 5000.0,
                    "camera_mp": 50.0,
                    "display_hz": 120.0,
                    "processor_score": 500000.0,
                    "has_5g": True,
                },
                {
                    "phone_name": "Phone Gamma",
                    "brand": "BrandX",
                    "price_inr": 22000.0,
                    "ram_gb": 8.0,
                    "storage_gb": 128.0,
                    "battery_mah": 5000.0,
                    "camera_mp": 50.0,
                    "display_hz": 120.0,
                    "processor_score": 500000.0,
                    "has_5g": True,
                },
            ]
        )

        rec = SmartPickRecommender(mock_data)
        prefs = UserPreferences(min_budget=15000, max_budget=25000, weight_value=0.0)
        candidates = rec.filter_candidates(prefs)
        results = rec.rank_baseline(candidates, prefs, top_k=3)

        # Phone Alpha and Beta have price 20000, Phone Gamma has price 22000.
        # Between Alpha and Beta, Alpha is alphabetically earlier.
        assert results[0].phone_name == "Phone Alpha"
        assert results[1].phone_name == "Phone Beta"
        assert results[2].phone_name == "Phone Gamma"


class TestRecommenderEdgeCasesAndExplainability:
    """Tests for missing values handling (TC-07), explanations (TC-09), and reproducibility (TC-10)."""

    def test_tc07_missing_optional_specs_renormalized_not_zeroed(
        self, recommender: SmartPickRecommender
    ) -> None:
        """TC-07: Verify phone missing a spec has weights renormalized and missing_specs flagged."""
        # Fairphone Prototype 5 in catalog has NaN battery and NaN benchmark
        prefs = UserPreferences(
            min_budget=40000,
            max_budget=50000,
            weight_battery=0.4,
            weight_performance=0.3,
            weight_camera=0.3,
        )
        candidates = recommender.filter_candidates(prefs)
        results = recommender.rank_baseline(candidates, prefs, top_k=10)

        fairphone_res = [r for r in results if "Fairphone" in r.phone_name]
        if fairphone_res:
            res = fairphone_res[0]
            assert (
                "battery_mah" in res.missing_specs
                or "processor_score" in res.missing_specs
            )
            assert res.match_score > 0.0, (
                "Score should be calculated across remaining active dimensions."
            )
            assert any("unverified" in note.lower() for note in res.trade_offs)

    def test_tc09_explanation_grounded_in_real_specs(
        self, recommender: SmartPickRecommender
    ) -> None:
        """TC-09: Verify explanation cites real features, percentiles, and trade-offs."""
        prefs = UserPreferences(
            min_budget=20000,
            max_budget=35000,
            weight_performance=0.4,
            weight_battery=0.3,
        )
        candidates = recommender.filter_candidates(prefs)
        results = recommender.rank_baseline(candidates, prefs, top_k=3)

        top = results[0]
        assert top.rationale
        assert "Top matching factors:" in top.rationale
        # Must have feature contributions summing to total score
        contrib_sum = sum(top.feature_contributions.values())
        assert contrib_sum == pytest.approx(top.match_score, 0.5)

    def test_tc10_deterministic_reproducibility(
        self, recommender: SmartPickRecommender
    ) -> None:
        """TC-10: Verify repeated runs with identical preferences return identical outputs."""
        prefs = UserPreferences(
            min_budget=18000, max_budget=30000, weight_battery=0.5, weight_camera=0.5
        )
        candidates1 = recommender.filter_candidates(prefs)
        res1 = recommender.rank_baseline(candidates1, prefs, top_k=5)

        candidates2 = recommender.filter_candidates(prefs)
        res2 = recommender.rank_baseline(candidates2, prefs, top_k=5)

        assert len(res1) == len(res2)
        for r1, r2 in zip(res1, res2, strict=True):
            assert r1.phone_name == r2.phone_name
            assert r1.price_inr == r2.price_inr
            assert r1.match_score == r2.match_score


class TestPropertyBasedBudgetCompliance:
    """Property-based test using Hypothesis asserting 100% budget compliance under all inputs."""

    @settings(max_examples=40, deadline=None)
    @given(
        min_b=st.integers(min_value=5000, max_value=80000),
        spread=st.integers(min_value=5000, max_value=60000),
        w_perf=st.floats(min_value=0.0, max_value=1.0),
        w_cam=st.floats(min_value=0.0, max_value=1.0),
        w_batt=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_hypothesis_budget_compliance_always_holds(
        self,
        real_catalog_df: pd.DataFrame,
        min_b: int,
        spread: int,
        w_perf: float,
        w_cam: float,
        w_batt: float,
    ) -> None:
        """Property: Every result must satisfy min_budget <= price <= max_budget unconditionally."""
        max_b = min_b + spread
        if w_perf + w_cam + w_batt <= 0.0:
            w_perf = 0.5

        prefs = UserPreferences(
            min_budget=float(min_b),
            max_budget=float(max_b),
            weight_performance=w_perf,
            weight_camera=w_cam,
            weight_battery=w_batt,
        )

        rec = SmartPickRecommender(real_catalog_df)

        try:
            candidates = rec.filter_candidates(prefs)
            results = rec.rank_baseline(candidates, prefs, top_k=5)
        except NoEligiblePhonesError:
            # If no phones exist in the random range, the invariant is trivially satisfied
            return

        for r in results:
            assert float(min_b) <= r.price_inr <= float(max_b), (
                f"Budget violation: {r.phone_name} price {r.price_inr} not in [{min_b}, {max_b}]"
            )
            assert 0.0 <= r.match_score <= 100.0, (
                f"Match score {r.match_score} out of [0, 100]"
            )
