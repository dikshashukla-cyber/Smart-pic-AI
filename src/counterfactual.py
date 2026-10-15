"""Counterfactual 'Why NOT this phone' explainer module for SmartPick AI.

Implements Phase P5a Requirement 1:
Explains transparently why a user-selected smartphone did not make the Top 5
recommendations, referencing exclusively verified catalog fields and user constraints.
"""

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.recommender import RecommendationResult, SmartPickRecommender, UserPreferences

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DisqualificationReason:
    """Structured explanation of why a device was not recommended."""

    phone_name: str
    brand: str | None
    price_inr: float
    category: str  # 'already_top_5', 'budget_violation', 'brand_filtered', '5g_missing', 'score_deficit'
    primary_reason: str
    detailed_deficits: list[str]
    candidate_specs: dict[str, Any]
    comparison_specs: dict[str, Any]  # Median specs of top 5
    score_gap: float | None = None
    rank: int | None = None


def explain_why_not_phone(
    phone_name: str,
    recommender: SmartPickRecommender,
    prefs: UserPreferences,
    top_5_results: list[RecommendationResult],
) -> DisqualificationReason:
    """Analyze why a specific catalog smartphone failed to make the Top 5 shortlist.

    Args:
        phone_name: Exact device name to inspect.
        recommender: Initialized SmartPickRecommender.
        prefs: Active user preferences.
        top_5_results: Top 5 recommendations currently surfaced.

    Returns:
        DisqualificationReason object with verified factual explanation.
    """
    catalog_df = recommender.catalog_df
    matching_rows = catalog_df[catalog_df["phone_name"] == phone_name]

    if matching_rows.empty:
        raise ValueError(f"Smartphone '{phone_name}' does not exist in active catalog.")

    phone_row = matching_rows.iloc[0]
    price = float(phone_row["price_inr"])
    brand = str(phone_row["brand"]) if pd.notna(phone_row.get("brand")) else "Unknown"

    specs = {
        "price_inr": price,
        "ram_gb": phone_row.get("ram_gb"),
        "storage_gb": phone_row.get("storage_gb"),
        "battery_mah": phone_row.get("battery_mah"),
        "camera_mp": phone_row.get("camera_mp"),
        "display_hz": phone_row.get("display_hz"),
        "has_5g": phone_row.get("has_5g"),
        "processor_score": phone_row.get("processor_score"),
    }

    # 1. Check if device is already in Top 5
    top_names = [r.phone_name for r in top_5_results]
    if phone_name in top_names:
        rank = top_names.index(phone_name) + 1
        return DisqualificationReason(
            phone_name=phone_name,
            brand=brand,
            price_inr=price,
            category="already_top_5",
            primary_reason=f"This device is already shortlisted in your Top 5 (Ranked #{rank})!",
            detailed_deficits=[],
            candidate_specs=specs,
            comparison_specs={},
            score_gap=0.0,
            rank=rank,
        )

    # 2. Check for Hard Budget Constraint Violation
    if price > prefs.max_budget:
        excess = price - prefs.max_budget
        pct_excess = (excess / prefs.max_budget) * 100.0
        return DisqualificationReason(
            phone_name=phone_name,
            brand=brand,
            price_inr=price,
            category="budget_violation",
            primary_reason=(
                f"Disqualified by Hard Budget Constraint: Price of ₹{int(price):,} exceeds "
                f"your maximum budget limit of ₹{int(prefs.max_budget):,} by ₹{int(excess):,} (+{pct_excess:.1f}%)."
            ),
            detailed_deficits=[
                f"Configured budget ceiling: ₹{int(prefs.max_budget):,}",
                f"Device catalog retail price: ₹{int(price):,}",
                "Strict policy: 100% of recommendations must strictly satisfy budget bounds.",
            ],
            candidate_specs=specs,
            comparison_specs={"max_budget": prefs.max_budget},
        )

    if price < prefs.min_budget:
        deficit = prefs.min_budget - price
        return DisqualificationReason(
            phone_name=phone_name,
            brand=brand,
            price_inr=price,
            category="budget_violation",
            primary_reason=(
                f"Excluded by Minimum Budget Bound: Price of ₹{int(price):,} is below "
                f"your configured lower budget floor of ₹{int(prefs.min_budget):,} by ₹{int(deficit):,}."
            ),
            detailed_deficits=[
                f"Configured budget floor: ₹{int(prefs.min_budget):,}",
                f"Device catalog retail price: ₹{int(price):,} (₹{int(deficit):,} below floor)",
            ],
            candidate_specs=specs,
            comparison_specs={"min_budget": prefs.min_budget},
        )

    # 3. Check for Brand Filter Disqualification
    if prefs.preferred_brands and "brand" in phone_row:
        clean_brands = {b.strip().lower() for b in prefs.preferred_brands}
        if brand.strip().lower() not in clean_brands:
            return DisqualificationReason(
                phone_name=phone_name,
                brand=brand,
                price_inr=price,
                category="brand_filtered",
                primary_reason=(
                    f"Excluded by Manufacturer Filter: Brand '{brand}' is not included in "
                    f"your active brand shortlist ({', '.join(prefs.preferred_brands)})."
                ),
                detailed_deficits=[
                    f"Selected brands: {', '.join(prefs.preferred_brands)}",
                    f"Device manufacturer: {brand}",
                ],
                candidate_specs=specs,
                comparison_specs={},
            )

    # 4. Check for 5G Constraint Disqualification
    if prefs.require_5g and not bool(phone_row.get("has_5g")):
        return DisqualificationReason(
            phone_name=phone_name,
            brand=brand,
            price_inr=price,
            category="5g_missing",
            primary_reason=(
                "Excluded by 5G Constraint: Strict 5G connectivity was requested, "
                "but this smartphone only supports 4G LTE cellular networks."
            ),
            detailed_deficits=[
                "User constraint: Require 5G = True",
                "Device cellular spec: 4G LTE (has_5g = False)",
            ],
            candidate_specs=specs,
            comparison_specs={},
        )

    # 5. Device was Eligible, but was outscored by Top 5 candidates
    candidates_df = recommender.filter_candidates(prefs)
    all_ranked = recommender.rank_baseline(
        candidates_df, prefs, top_k=len(candidates_df)
    )

    # Locate candidate in ranked results
    cand_res = next((r for r in all_ranked if r.phone_name == phone_name), None)
    if not cand_res:
        return DisqualificationReason(
            phone_name=phone_name,
            brand=brand,
            price_inr=price,
            category="score_deficit",
            primary_reason="Device was eligible but was ranked lower than the top recommendations.",
            detailed_deficits=[],
            candidate_specs=specs,
            comparison_specs={},
        )

    cand_rank = all_ranked.index(cand_res) + 1
    cand_score = cand_res.match_score

    cutoff_res = top_5_results[-1] if top_5_results else cand_res
    cutoff_score = cutoff_res.match_score
    score_gap = round(cutoff_score - cand_score, 1)

    # Compute comparison medians of top 5
    top_5_df = catalog_df[
        catalog_df["phone_name"].isin([r.phone_name for r in top_5_results])
    ]
    median_specs = {
        "price_inr": float(top_5_df["price_inr"].median())
        if "price_inr" in top_5_df
        else price,
        "battery_mah": float(top_5_df["battery_mah"].median())
        if "battery_mah" in top_5_df
        else 5000,
        "processor_score": float(top_5_df["processor_score"].median())
        if "processor_score" in top_5_df
        else 600000,
        "camera_mp": float(top_5_df["camera_mp"].median())
        if "camera_mp" in top_5_df
        else 50,
        "display_hz": float(top_5_df["display_hz"].median())
        if "display_hz" in top_5_df
        else 120,
        "storage_gb": float(top_5_df["storage_gb"].median())
        if "storage_gb" in top_5_df
        else 128,
        "ram_gb": float(top_5_df["ram_gb"].median()) if "ram_gb" in top_5_df else 8,
    }

    # Identify primary deficit dimensions
    deficits: list[str] = []

    # Processor deficit
    proc_val = phone_row.get("processor_score")
    if pd.notna(proc_val) and prefs.weight_performance > 0.15:
        proc_med = median_specs["processor_score"]
        if float(proc_val) < proc_med * 0.85:
            pct_below = ((proc_med - float(proc_val)) / proc_med) * 100.0
            deficits.append(
                f"🚀 Processor Throughput: Benchmark score of {int(proc_val):,} is {pct_below:.0f}% lower than Top-5 median ({int(proc_med):,})."
            )

    # Battery deficit
    bat_val = phone_row.get("battery_mah")
    if pd.notna(bat_val) and prefs.weight_battery > 0.15:
        bat_med = median_specs["battery_mah"]
        if float(bat_val) < bat_med:
            diff = int(bat_med - float(bat_val))
            deficits.append(
                f"🔋 Battery Capacity: {int(bat_val)} mAh is {diff} mAh lower than Top-5 median ({int(bat_med)} mAh)."
            )

    # Camera deficit
    cam_val = phone_row.get("camera_mp")
    if pd.notna(cam_val) and prefs.weight_camera > 0.15:
        cam_med = median_specs["camera_mp"]
        if float(cam_val) < cam_med:
            deficits.append(
                f"📸 Camera Sensor: {int(cam_val)} MP resolution vs Top-5 median of {int(cam_med)} MP."
            )

    # Display deficit
    disp_val = phone_row.get("display_hz")
    if pd.notna(disp_val) and prefs.weight_display > 0.15:
        disp_med = median_specs["display_hz"]
        if float(disp_val) < disp_med:
            deficits.append(
                f"📺 Display Refresh: {int(disp_val)} Hz panel vs smoother {int(disp_med)} Hz Top-5 standard."
            )

    # Storage deficit
    stor_val = phone_row.get("storage_gb")
    if pd.notna(stor_val) and prefs.weight_storage > 0.15:
        stor_med = median_specs["storage_gb"]
        if float(stor_val) < stor_med:
            deficits.append(
                f"💾 Storage Capacity: {int(stor_val)} GB vs Top-5 median of {int(stor_med)} GB."
            )

    if not deficits:
        deficits.append(
            f"Overall preference alignment deficit: Scored {cand_score:.1f}/100 across composite dimensions, falling just short of the #{len(top_5_results)} cutoff ({cutoff_score:.1f}/100)."
        )

    return DisqualificationReason(
        phone_name=phone_name,
        brand=brand,
        price_inr=price,
        category="score_deficit",
        primary_reason=(
            f"Satisfied budget and hard constraints, but ranked #{cand_rank} out of {len(all_ranked)} eligible phones "
            f"with a Match Score of {cand_score:.1f}/100 (a deficit of {score_gap:.1f} pts behind the #{len(top_5_results)} cutoff of {cutoff_score:.1f}/100)."
        ),
        detailed_deficits=deficits,
        candidate_specs=specs,
        comparison_specs=median_specs,
        score_gap=score_gap,
        rank=cand_rank,
    )
