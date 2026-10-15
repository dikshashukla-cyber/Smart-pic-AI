"""Run an exhaustive randomized budget-compliance stress test over 10,000 random profiles.

Proves that:
1. 100% of returned recommendation results strictly satisfy user budget boundaries:
   min_budget <= price_inr <= max_budget.
2. Across all 4 algorithmic modes: baseline, similarity, blended, and mmr.
3. Across varying top_k, brand filter combinations, and 5G requirements.
"""

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import DataLoader
from src.exceptions import NoEligiblePhonesError
from src.preprocessing import FeaturePreprocessor
from src.recommender import SmartPickRecommender, UserPreferences


def run_randomized_budget_stress_test(num_iterations: int = 10_000) -> dict:
    data_path = Path("data/phones.csv")
    loader = DataLoader(data_path)
    df, _ = loader.load_and_validate()

    preprocessor = FeaturePreprocessor(strategy="robust_minmax")
    preprocessor.fit(df)
    recommender = SmartPickRecommender(df, preprocessor)

    # Filter out invalid prices for candidate selection
    valid_df = df[df["price_inr"] > 0]
    catalog_min_price = int(valid_df["price_inr"].min())
    catalog_max_price = int(valid_df["price_inr"].max())
    all_brands = sorted(valid_df["brand"].dropna().unique())
    modes = ["baseline", "similarity", "blended", "mmr"]

    total_profiles = num_iterations
    total_recommendations_evaluated = 0
    violations = 0
    empty_results_count = 0
    valid_results_count = 0

    random.seed(42)  # Deterministic seed for reproducible verification
    start_time = time.time()

    print(
        f"Starting randomized budget compliance stress test: {total_profiles:,} iterations...",
        flush=True,
    )

    for i in range(1, total_profiles + 1):
        # 1. Random budget window within catalog range
        b1 = random.randint(catalog_min_price, catalog_max_price)
        b2 = random.randint(catalog_min_price, catalog_max_price)
        min_b = min(b1, b2)
        max_b = max(b1, b2)

        # 2. Random weights
        weights = [round(random.uniform(0.05, 1.0), 2) for _ in range(6)]

        # 3. Optional brand filter
        brand_filter = None
        if random.random() < 0.35:
            sample_size = random.randint(1, min(4, len(all_brands)))
            brand_filter = random.sample(all_brands, sample_size)

        # 4. Optional 5G
        req_5g = None
        if random.random() < 0.30:
            req_5g = random.choice([True, False])

        # 5. Engine mode and Top K
        mode = random.choice(modes)
        top_k = random.randint(1, 10)
        blend_factor = round(random.uniform(0.1, 0.9), 2)
        diversity_lambda = round(random.uniform(0.2, 0.9), 2)

        prefs = UserPreferences(
            min_budget=float(min_b),
            max_budget=float(max_b),
            weight_performance=weights[0],
            weight_camera=weights[1],
            weight_battery=weights[2],
            weight_display=weights[3],
            weight_storage=weights[4],
            weight_value=weights[5],
            preferred_brands=brand_filter,
            require_5g=req_5g,
            ranking_mode=mode,
            blend_factor=blend_factor,
            diversity_lambda=diversity_lambda,
        )

        try:
            results = recommender.recommend(prefs, top_k=top_k)
            if not results:
                empty_results_count += 1
            else:
                valid_results_count += 1
                for r in results:
                    total_recommendations_evaluated += 1
                    if r.price_inr < min_b or r.price_inr > max_b:
                        violations += 1
                        print(
                            f"VIOLATION at iteration {i}: Phone '{r.phone_name}' price {r.price_inr} outside [{min_b}, {max_b}]"
                        )
        except NoEligiblePhonesError:
            empty_results_count += 1

        if i % 2500 == 0:
            elapsed = time.time() - start_time
            print(
                f"  Progress: {i:,} / {total_profiles:,} profiles tested ({elapsed:.2f}s elapsed, violations: {violations})",
                flush=True,
            )

    elapsed_total = time.time() - start_time
    compliance_rate = (
        100.0
        if violations == 0
        else (
            (total_recommendations_evaluated - violations)
            / total_recommendations_evaluated
        )
        * 100.0
    )

    summary = {
        "total_profiles_tested": total_profiles,
        "valid_recommendation_runs": valid_results_count,
        "empty_or_no_eligible_runs": empty_results_count,
        "total_recommendations_checked": total_recommendations_evaluated,
        "violations": violations,
        "compliance_rate_pct": compliance_rate,
        "elapsed_seconds": round(elapsed_total, 2),
        "profiles_per_second": round(total_profiles / elapsed_total, 1),
    }

    print("\n" + "=" * 60)
    print("RANDOMIZED BUDGET COMPLIANCE VERIFICATION SUMMARY")
    print("=" * 60)
    for k, v in summary.items():
        print(f"{k}: {v}")
    print("=" * 60)

    assert violations == 0, f"FAILED: {violations} budget violations detected!"
    return summary


if __name__ == "__main__":
    run_randomized_budget_stress_test(10_000)
