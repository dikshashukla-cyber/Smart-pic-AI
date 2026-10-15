"""Recommender engine module for SmartPick AI.

Implements TRD Section 6.1 Baseline Engine:
- Pydantic UserPreferences validation with domain exceptions.
- Hard constraint filtering (budget bounds inclusive, brand, 5G).
- Multi-attribute preference scoring with per-phone weight renormalization.
- Deterministic secondary tie-breaking (score desc, price asc, name asc).
- Grounded explanation generator with percentiles and trade-off notes.
- Feature contribution breakdown for explainability charts.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, model_validator

from src.exceptions import (
    InvalidBudgetRangeError,
    InvalidWeightsError,
    NoEligiblePhonesError,
)
from src.preprocessing import FeaturePreprocessor
from src.similarity import ContentSimilarityEngine

logger = logging.getLogger(__name__)


class UserPreferences(BaseModel):
    """User input preference model with strict boundary and weight validation."""

    min_budget: float = Field(default=0.0, description="Minimum price bound in INR")
    max_budget: float = Field(..., description="Maximum price bound in INR")
    preferred_brands: list[str] | None = Field(
        default=None, description="Optional list of filtered brands (case-insensitive)"
    )
    require_5g: bool | None = Field(
        default=None, description="Filter for 5G capable devices if field present"
    )

    # 6 Canonical Preference Dimensions (0.0 to 1.0)
    weight_performance: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Gaming, processor speed & everyday responsiveness",
    )
    weight_camera: float = Field(
        default=0.20, ge=0.0, le=1.0, description="Main camera sensor resolution"
    )
    weight_battery: float = Field(
        default=0.20, ge=0.0, le=1.0, description="Battery capacity (mAh)"
    )
    weight_display: float = Field(
        default=0.15, ge=0.0, le=1.0, description="Display refresh rate (Hz)"
    )
    weight_storage: float = Field(
        default=0.10, ge=0.0, le=1.0, description="Internal storage capacity (GB)"
    )
    weight_value: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Derived spec-to-price ratio (baseline value index)",
    )

    # Advanced Ranking Controls (Phase 4)
    ranking_mode: str = Field(
        default="baseline",
        description="Ranking mode: 'baseline', 'similarity', 'blended', or 'mmr'",
    )
    blend_factor: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Similarity blend factor (alpha) in [0.0, 1.0]",
    )
    diversity_lambda: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="MMR relevance vs diversity trade-off in [0.0, 1.0]",
    )
    reference_phone: str | None = Field(
        default=None,
        description="Anchor reference device for similarity scoring",
    )

    @model_validator(mode="after")
    def validate_constraints(self) -> "UserPreferences":
        """Validate budget interval and verify weights are non-negative and not all zero."""
        if (
            self.min_budget < 0
            or self.max_budget <= 0
            or self.min_budget > self.max_budget
        ):
            raise InvalidBudgetRangeError(
                min_budget=self.min_budget, max_budget=self.max_budget
            )

        weights = [
            self.weight_performance,
            self.weight_camera,
            self.weight_battery,
            self.weight_display,
            self.weight_storage,
            self.weight_value,
        ]

        if any(w < 0 for w in weights):
            raise InvalidWeightsError("Preference weights cannot be negative.")

        if sum(weights) <= 0.0:
            raise InvalidWeightsError(
                "At least one preference weight must be greater than zero."
            )

        return self


@dataclass(frozen=True)
class RecommendationResult:
    """Structured representation of a single recommended device.

    NOTE: match_score is a relative heuristic ranking index (0-100), NOT an
    objective probability of satisfaction or universal quality rating.
    """

    phone_name: str
    brand: str | None
    price_inr: float
    match_score: float
    ranking_method: str
    specs: dict[str, Any]
    scaled_specs: dict[str, float]
    feature_contributions: dict[str, float]
    rationale: str
    missing_specs: list[str] = field(default_factory=list)
    trade_offs: list[str] = field(default_factory=list)
    image_path: str | None = None
    image_url: str | None = None
    image_source: str | None = None
    image_license: str | None = None
    image_attribution: str | None = None


class SmartPickRecommender:
    """Core recommendation engine combining constraint filtering, ranking, and similarity."""

    def __init__(
        self,
        catalog_df: pd.DataFrame,
        preprocessor: FeaturePreprocessor | None = None,
    ) -> None:
        """Initialize recommender with validated catalog DataFrame.

        Args:
            catalog_df: Validated DataFrame containing smartphone specifications.
            preprocessor: Optional fitted FeaturePreprocessor instance.
        """
        self.catalog_df = catalog_df.copy()

        # Fit preprocessor on catalog data if not supplied
        if preprocessor is not None and preprocessor.is_fitted_:
            self.preprocessor = preprocessor
        else:
            self.preprocessor = FeaturePreprocessor(strategy="robust_minmax")
            self.preprocessor.fit(self.catalog_df)

        # Initialize content-based similarity engine
        self.similarity_engine = ContentSimilarityEngine(
            self.catalog_df, self.preprocessor
        )

    def filter_candidates(self, prefs: UserPreferences) -> pd.DataFrame:
        """Filter catalog strictly by budget and optional criteria.

        Guarantees 100% budget compliance: min_budget <= price_inr <= max_budget.

        Args:
            prefs: Validated user preferences.

        Returns:
            Filtered candidate DataFrame.

        Raises:
            NoEligiblePhonesError: If zero phones meet the filters.
        """
        df = self.catalog_df.copy()

        # 1. Hard Budget Filter (100% compliance guarantee)
        budget_mask = (df["price_inr"] >= prefs.min_budget) & (
            df["price_inr"] <= prefs.max_budget
        )
        df = df[budget_mask]

        # 2. Brand Filter (if specified and brand column exists)
        if prefs.preferred_brands and "brand" in df.columns:
            clean_brands = {
                b.strip().lower() for b in prefs.preferred_brands if b.strip()
            }
            if clean_brands:
                brand_mask = (
                    df["brand"].astype(str).str.strip().str.lower().isin(clean_brands)
                )
                df = df[brand_mask]

        # 3. 5G Filter (if specified and has_5g column exists)
        if prefs.require_5g is not None and "has_5g" in df.columns:
            # Phones where has_5g matches user preference (ignoring NaNs if 5G is strictly required)
            if prefs.require_5g:
                df = df[df["has_5g"] == True]
            else:
                df = df[df["has_5g"] == False]

        if df.empty:
            raise NoEligiblePhonesError(
                budget_min=prefs.min_budget,
                budget_max=prefs.max_budget,
                brands=prefs.preferred_brands,
                has_5g=prefs.require_5g,
            )

        return df

    def calculate_percentile(self, value: float, series: pd.Series) -> float:
        """Compute the empirical percentile rank of a value within an eligible series."""
        clean = series.dropna().astype(float)
        if clean.empty or pd.isna(value):
            return 50.0
        less = (clean < value).sum()
        equal = (clean == value).sum()
        return round(float((less + 0.5 * equal) / len(clean) * 100), 1)

    def rank_baseline(
        self,
        candidates_df: pd.DataFrame,
        prefs: UserPreferences,
        top_k: int = 5,
    ) -> list[RecommendationResult]:
        """Rank candidates using normalized weighted preference scoring baseline.

        Missing-Feature Renormalization Policy:
        If a phone lacks a spec (e.g. processor_score is NaN), that dimension is
        excluded for that phone, and active weights are renormalized.
        Ties are broken deterministically by price_inr ascending, then phone_name ascending.

        Args:
            candidates_df: Budget-compliant candidates DataFrame.
            prefs: User preferences with weights.
            top_k: Number of recommendations to return (default 5).

        Returns:
            List of RecommendationResult sorted by descending score.
        """
        if candidates_df.empty:
            raise NoEligiblePhonesError(
                budget_min=prefs.min_budget,
                budget_max=prefs.max_budget,
                brands=prefs.preferred_brands,
                has_5g=prefs.require_5g,
            )

        # Scale features using preprocessor (NaNs remain NaN)
        scaled_df = self.preprocessor.transform(candidates_df)

        # Compute derived Value-for-Money index across eligible candidates
        # Hardware spec average / relative price index
        hw_indices = scaled_df[
            ["processor_score", "battery_mah", "display_hz", "ram_gb"]
        ].mean(axis=1, skipna=True)
        median_price = candidates_df["price_inr"].median()
        if median_price <= 0:
            median_price = 1.0
        rel_price = (candidates_df["price_inr"] / median_price).clip(lower=0.2)
        raw_value_ratio = hw_indices / rel_price
        # Normalize value index to [0, 1] within eligible set
        val_min = raw_value_ratio.min()
        val_max = raw_value_ratio.max()
        if val_max > val_min:
            scaled_df["value_for_money"] = (raw_value_ratio - val_min) / (
                val_max - val_min
            )
        else:
            scaled_df["value_for_money"] = 0.5

        # Define dimension-to-feature mapping
        dim_weights = {
            "performance": (prefs.weight_performance, "processor_score"),
            "camera": (prefs.weight_camera, "camera_mp"),
            "battery": (prefs.weight_battery, "battery_mah"),
            "display": (prefs.weight_display, "display_hz"),
            "storage": (prefs.weight_storage, "storage_gb"),
            "value": (prefs.weight_value, "value_for_money"),
        }

        results: list[RecommendationResult] = []

        for idx, row in candidates_df.iterrows():
            scaled_row = scaled_df.loc[idx]
            phone_name = str(row["phone_name"])
            brand = str(row["brand"]) if pd.notna(row.get("brand")) else None
            price = float(row["price_inr"])

            weighted_sum = 0.0
            active_weight_sum = 0.0
            missing_specs: list[str] = []
            contributions: dict[str, float] = {}
            active_scaled: dict[str, float] = {}

            for dim_name, (w, col_name) in dim_weights.items():
                if w <= 0.0:
                    continue

                scaled_val = scaled_row.get(col_name)

                # If primary feature is NaN (e.g. processor_score), check if ram_gb can stand in
                if pd.isna(scaled_val) and dim_name == "performance":
                    scaled_val = scaled_row.get("ram_gb")

                if pd.isna(scaled_val):
                    missing_specs.append(col_name)
                else:
                    weighted_sum += w * float(scaled_val)
                    active_weight_sum += w
                    active_scaled[dim_name] = round(float(scaled_val), 4)

            # Score computation with per-phone renormalization
            if active_weight_sum > 0.0:
                normalized_score = (weighted_sum / active_weight_sum) * 100.0
            else:
                normalized_score = 0.0

            # Calculate individual percentage point contributions
            for dim_name, (w, _) in dim_weights.items():
                if dim_name in active_scaled and active_weight_sum > 0.0:
                    pts = (w * active_scaled[dim_name] / active_weight_sum) * 100.0
                    contributions[dim_name] = round(pts, 2)
                else:
                    contributions[dim_name] = 0.0

            # Generate natural language explanation and trade-offs
            rationale, trade_offs = self.generate_explanation(
                phone_row=row,
                prefs=prefs,
                candidates_df=candidates_df,
                contributions=contributions,
                missing_specs=missing_specs,
            )

            # Raw specs dictionary
            raw_specs = {
                "price_inr": price,
                "ram_gb": row.get("ram_gb"),
                "storage_gb": row.get("storage_gb"),
                "battery_mah": row.get("battery_mah"),
                "camera_mp": row.get("camera_mp"),
                "display_hz": row.get("display_hz"),
                "has_5g": row.get("has_5g"),
                "processor_score": row.get("processor_score"),
            }

            results.append(
                RecommendationResult(
                    phone_name=phone_name,
                    brand=brand,
                    price_inr=price,
                    match_score=round(normalized_score, 2),
                    ranking_method="Baseline Multi-Attribute Ranking",
                    specs=raw_specs,
                    scaled_specs=active_scaled,
                    feature_contributions=contributions,
                    rationale=rationale,
                    missing_specs=missing_specs,
                    trade_offs=trade_offs,
                    image_path=str(row.get("image_path"))
                    if pd.notna(row.get("image_path"))
                    else None,
                    image_url=str(row.get("image_url"))
                    if pd.notna(row.get("image_url"))
                    else None,
                    image_source=str(row.get("image_source"))
                    if pd.notna(row.get("image_source"))
                    else None,
                    image_license=str(row.get("image_license"))
                    if pd.notna(row.get("image_license"))
                    else None,
                    image_attribution=str(row.get("image_attribution"))
                    if pd.notna(row.get("image_attribution"))
                    else None,
                )
            )

        # Deterministic sorting: score desc, price asc, phone_name asc
        results.sort(key=lambda r: (-r.match_score, r.price_inr, r.phone_name))

        return results[:top_k]

    def generate_explanation(
        self,
        phone_row: pd.Series,
        prefs: UserPreferences,
        candidates_df: pd.DataFrame,
        contributions: dict[str, float],
        missing_specs: list[str],
    ) -> tuple[str, list[str]]:
        """Generate faithful explanation grounded only in real features, percentiles, and active weights.

        Args:
            phone_row: Raw specifications series for the device.
            prefs: Active user weights.
            candidates_df: The eligible candidate pool for percentile benchmarking.
            contributions: Per-dimension percentage point contribution to score.
            missing_specs: List of missing columns for this phone.

        Returns:
            Tuple of (summary rationale paragraph, list of trade-off bullet strings).
        """
        # Find top 2 contributing dimensions
        sorted_contribs = sorted(
            contributions.items(), key=lambda item: item[1], reverse=True
        )
        top_contribs = [item for item in sorted_contribs if item[1] > 0][:2]

        explanation_parts = []
        trade_offs = []

        # 1. Top contributing strengths
        dim_labels = {
            "performance": ("Performance", "processor_score", "pts"),
            "camera": ("Camera", "camera_mp", "MP"),
            "battery": ("Battery", "battery_mah", "mAh"),
            "display": ("Display", "display_hz", "Hz"),
            "storage": ("Storage", "storage_gb", "GB"),
            "value": ("Value for Money", "price_inr", "INR"),
        }

        strength_notes = []
        for dim, pts in top_contribs:
            label, col, unit = dim_labels[dim]
            raw_val = phone_row.get(col)
            if pd.notna(raw_val) and col in candidates_df.columns:
                pct = self.calculate_percentile(float(raw_val), candidates_df[col])
                if unit == "INR":
                    strength_notes.append(
                        f"{label} ({pts:.1f} pts, spec-to-price ratio)"
                    )
                else:
                    strength_notes.append(
                        f"{label} ({raw_val} {unit}, {pct}th percentile of eligible phones)"
                    )
            else:
                strength_notes.append(f"{label} ({pts:.1f} pts)")

        if strength_notes:
            explanation_parts.append(
                f"Top matching factors: {' and '.join(strength_notes)}."
            )

        # 2. Check for trade-offs (dimensions with percentile < 40% among eligible devices)
        for dim, (_, col, unit) in dim_labels.items():
            if dim == "value":
                continue
            raw_val = phone_row.get(col)
            if pd.notna(raw_val) and col in candidates_df.columns:
                pct = self.calculate_percentile(float(raw_val), candidates_df[col])
                if pct < 40.0:
                    trade_msg = (
                        f"Lower {dim_labels[dim][0].lower()} ({raw_val} {unit}) "
                        f"than {100 - pct:.0f}% of eligible phones in this budget."
                    )
                    trade_offs.append(trade_msg)

        # 3. Add caveats for missing fields
        if missing_specs:
            readable_missing = ", ".join(missing_specs)
            trade_offs.append(
                f"Catalog caveat: Specification(s) '{readable_missing}' unverified; "
                "score computed across remaining active dimensions."
            )

        # 4. Mandatory camera disclaimer if camera weight is active
        if prefs.weight_camera > 0:
            trade_offs.append(
                "Camera notice: Score reflects primary sensor resolution (MP) only; "
                "lens optics, sensor size, and image processing are not measured by MP count."
            )

        if trade_offs:
            explanation_parts.append(f"Key trade-off: {trade_offs[0]}")

        full_rationale = " ".join(explanation_parts)
        return full_rationale, trade_offs

    def rank_similarity(
        self,
        candidates_df: pd.DataFrame,
        prefs: UserPreferences,
        reference_phone_name: str | None = None,
        top_k: int = 5,
    ) -> list[RecommendationResult]:
        """Rank candidates using cosine similarity against a reference device or ideal profile.

        Args:
            candidates_df: Budget-compliant candidates DataFrame.
            prefs: User preferences.
            reference_phone_name: Optional anchor phone name. Falls back to prefs.reference_phone.
            top_k: Number of recommendations to return.

        Returns:
            List of RecommendationResult sorted by descending similarity.
        """
        if candidates_df.empty:
            raise NoEligiblePhonesError(
                budget_min=prefs.min_budget,
                budget_max=prefs.max_budget,
                brands=prefs.preferred_brands,
                has_5g=prefs.require_5g,
            )

        ref_name = reference_phone_name or prefs.reference_phone

        if ref_name and ref_name in self.similarity_engine.name_to_idx:
            similar_items = self.similarity_engine.find_similar_phones(
                ref_name, candidates_df, top_k=len(candidates_df)
            )
            sim_score_map = {
                item["phone_name"]: item["similarity_score"] for item in similar_items
            }
            preface = f"Content similarity to anchor '{ref_name}'."
        else:
            target_specs = {
                "processor_score": prefs.weight_performance,
                "camera_mp": prefs.weight_camera,
                "battery_mah": prefs.weight_battery,
                "display_hz": prefs.weight_display,
                "storage_gb": prefs.weight_storage,
            }
            primary_brand = (
                prefs.preferred_brands[0] if prefs.preferred_brands else None
            )
            sim_score_map = self.similarity_engine.compute_profile_similarity(
                target_specs, primary_brand, candidates_df
            )
            preface = "Profile similarity match to your preference targets."

        # Compute baseline representations for spec contributions and trade-offs
        base_results = self.rank_baseline(
            candidates_df, prefs, top_k=len(candidates_df)
        )
        base_map = {r.phone_name: r for r in base_results}

        results: list[RecommendationResult] = []
        for name, sim_score in sim_score_map.items():
            base_r = base_map.get(name)
            if not base_r:
                continue

            rationale = f"{preface} {base_r.rationale}"
            results.append(
                RecommendationResult(
                    phone_name=base_r.phone_name,
                    brand=base_r.brand,
                    price_inr=base_r.price_inr,
                    match_score=sim_score,
                    ranking_method="similarity",
                    specs=base_r.specs,
                    scaled_specs=base_r.scaled_specs,
                    feature_contributions=base_r.feature_contributions,
                    rationale=rationale,
                    missing_specs=base_r.missing_specs,
                    trade_offs=base_r.trade_offs,
                    image_path=base_r.image_path,
                    image_url=base_r.image_url,
                    image_source=base_r.image_source,
                    image_license=base_r.image_license,
                    image_attribution=base_r.image_attribution,
                )
            )

        # Deterministic secondary tie-break
        results.sort(key=lambda x: (-x.match_score, x.price_inr, x.phone_name))
        return results[:top_k]

    def rank_blended(
        self,
        candidates_df: pd.DataFrame,
        prefs: UserPreferences,
        blend_factor: float | None = None,
        reference_phone_name: str | None = None,
        top_k: int = 5,
    ) -> list[RecommendationResult]:
        """Rank candidates using a documented hybrid blend of heuristic utility and content similarity.

        Formula:
            blended_score = (1 - alpha) * baseline_score + alpha * similarity_score
        Avoids double-counting by normalizing both indices to [0, 100] prior to combination.

        Args:
            candidates_df: Budget-compliant candidates DataFrame.
            prefs: User preferences.
            blend_factor: Alpha in [0.0, 1.0]. Defaults to prefs.blend_factor.
            reference_phone_name: Optional anchor phone for similarity component.
            top_k: Number of recommendations to return.

        Returns:
            List of RecommendationResult sorted by descending blended score.
        """
        alpha = prefs.blend_factor if blend_factor is None else blend_factor

        base_results = self.rank_baseline(
            candidates_df, prefs, top_k=len(candidates_df)
        )
        sim_results = self.rank_similarity(
            candidates_df,
            prefs,
            reference_phone_name=reference_phone_name,
            top_k=len(candidates_df),
        )

        base_score_map = {r.phone_name: r.match_score for r in base_results}
        sim_score_map = {r.phone_name: r.match_score for r in sim_results}
        base_obj_map = {r.phone_name: r for r in base_results}

        blended_scores = self.similarity_engine.blend_scores(
            base_score_map, sim_score_map, blend_factor=alpha
        )

        blended_results: list[RecommendationResult] = []
        for name, b_score in blended_scores.items():
            base_r = base_obj_map.get(name)
            if not base_r:
                continue

            base_pts = base_score_map.get(name, 0.0)
            sim_pts = sim_score_map.get(name, 0.0)
            rationale = (
                f"Hybrid blend ({b_score:.1f}/100) combining {int((1 - alpha) * 100)}% multi-criteria utility "
                f"({base_pts:.1f}) and {int(alpha * 100)}% content similarity ({sim_pts:.1f}). {base_r.rationale}"
            )

            blended_results.append(
                RecommendationResult(
                    phone_name=base_r.phone_name,
                    brand=base_r.brand,
                    price_inr=base_r.price_inr,
                    match_score=b_score,
                    ranking_method=f"blended (alpha={alpha:.2f})",
                    specs=base_r.specs,
                    scaled_specs=base_r.scaled_specs,
                    feature_contributions=base_r.feature_contributions,
                    rationale=rationale,
                    missing_specs=base_r.missing_specs,
                    trade_offs=base_r.trade_offs,
                    image_path=base_r.image_path,
                    image_url=base_r.image_url,
                    image_source=base_r.image_source,
                    image_license=base_r.image_license,
                    image_attribution=base_r.image_attribution,
                )
            )

        blended_results.sort(key=lambda x: (-x.match_score, x.price_inr, x.phone_name))
        return blended_results[:top_k]

    def rank_diverse_mmr(
        self,
        candidates_df: pd.DataFrame,
        prefs: UserPreferences,
        top_k: int = 5,
        lambda_param: float | None = None,
        base_mode: str = "baseline",
    ) -> list[RecommendationResult]:
        """Rank candidates using Maximal Marginal Relevance (MMR) for diversity-aware shortlists.

        Objective:
            MMR(d) = argmax_{d in C \\ S} [ lambda * Rel(d) - (1 - lambda) * max_{s in S} Sim(d, s) ]
        Reduces redundant near-duplicate models and broadens manufacturer representation.

        Args:
            candidates_df: Budget-compliant candidates DataFrame.
            prefs: User preferences.
            top_k: Number of recommendations to return.
            lambda_param: Trade-off parameter in [0.0, 1.0]. Defaults to prefs.diversity_lambda.
            base_mode: Underlying relevance scoring algorithm ('baseline', 'blended', 'similarity').

        Returns:
            List of RecommendationResult ordered by MMR selection.
        """
        lam = prefs.diversity_lambda if lambda_param is None else lambda_param

        if base_mode == "blended":
            relevance_pool = self.rank_blended(
                candidates_df, prefs, top_k=len(candidates_df)
            )
        elif base_mode == "similarity":
            relevance_pool = self.rank_similarity(
                candidates_df, prefs, top_k=len(candidates_df)
            )
        else:
            relevance_pool = self.rank_baseline(
                candidates_df, prefs, top_k=len(candidates_df)
            )

        rel_scores = {r.phone_name: r.match_score for r in relevance_pool}
        res_by_name = {r.phone_name: r for r in relevance_pool}
        candidate_names = [r.phone_name for r in relevance_pool]

        diverse_names = self.similarity_engine.mmr_rerank(
            candidate_names=candidate_names,
            relevance_scores=rel_scores,
            top_k=top_k,
            lambda_param=lam,
        )

        results: list[RecommendationResult] = []
        for rank_idx, name in enumerate(diverse_names, start=1):
            base_r = res_by_name[name]
            div_note = f"Surfaced via MMR diversity optimization (lambda={lam:.2f}) to prevent category clustering."
            results.append(
                RecommendationResult(
                    phone_name=base_r.phone_name,
                    brand=base_r.brand,
                    price_inr=base_r.price_inr,
                    match_score=base_r.match_score,
                    ranking_method=f"mmr (lambda={lam:.2f})",
                    specs=base_r.specs,
                    scaled_specs=base_r.scaled_specs,
                    feature_contributions=base_r.feature_contributions,
                    rationale=f"{div_note} {base_r.rationale}",
                    missing_specs=base_r.missing_specs,
                    trade_offs=base_r.trade_offs,
                    image_path=base_r.image_path,
                    image_url=base_r.image_url,
                    image_source=base_r.image_source,
                    image_license=base_r.image_license,
                    image_attribution=base_r.image_attribution,
                )
            )

        return results

    def recommend(
        self,
        prefs: UserPreferences,
        top_k: int = 5,
    ) -> list[RecommendationResult]:
        """Unified dispatch method executing recommendations per prefs.ranking_mode.

        Modes supported:
        - 'baseline': Multi-attribute weighted heuristic baseline (TRD 6.1).
        - 'similarity': Content-based cosine similarity (TRD 6.2).
        - 'blended': Tunable hybrid blend (TRD 6.3).
        - 'mmr': Diversity-aware Maximal Marginal Relevance re-ranking (TRD 6.3).

        100% of returned devices strictly satisfy budget bounds.
        """
        candidates = self.filter_candidates(prefs)
        mode = prefs.ranking_mode.lower()

        if "similarity" in mode:
            return self.rank_similarity(candidates, prefs, top_k=top_k)
        elif "blend" in mode:
            return self.rank_blended(candidates, prefs, top_k=top_k)
        elif "mmr" in mode or "diverse" in mode:
            return self.rank_diverse_mmr(candidates, prefs, top_k=top_k)
        else:
            return self.rank_baseline(candidates, prefs, top_k=top_k)
