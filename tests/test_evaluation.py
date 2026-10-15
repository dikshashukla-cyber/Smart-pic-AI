"""Unit tests for TC-11 and evaluation metrics (Precision@K, Recall@K, NDCG@K, Kendall tau)."""

import pytest

from src.evaluation import RecommenderEvaluator


def test_tc11_refuses_to_run_without_labels() -> None:
    """TC-11: Verify evaluation metrics strictly raise ValueError when relevance labels are absent."""
    evaluator = RecommenderEvaluator(is_synthetic_benchmark=False)
    recs = ["Phone A", "Phone B", "Phone C"]

    # Precision@K without labels must fail
    with pytest.raises(
        ValueError,
        match="Precision@K requires non-empty ground-truth relevance judgements",
    ):
        evaluator.precision_at_k(recs, relevant_ids=None, k=3)

    with pytest.raises(
        ValueError,
        match="Precision@K requires non-empty ground-truth relevance judgements",
    ):
        evaluator.precision_at_k(recs, relevant_ids=[], k=3)

    # Recall@K without labels must fail
    with pytest.raises(
        ValueError,
        match="Recall@K requires non-empty ground-truth relevance judgements",
    ):
        evaluator.recall_at_k(recs, relevant_ids=None, k=3)

    with pytest.raises(
        ValueError,
        match="Recall@K requires non-empty ground-truth relevance judgements",
    ):
        evaluator.recall_at_k(recs, relevant_ids=[], k=3)

    # NDCG@K without grades must fail
    with pytest.raises(
        ValueError,
        match="NDCG@K requires non-empty graded ground-truth relevance labels",
    ):
        evaluator.ndcg_at_k(recs, relevance_grades=None, k=3)

    with pytest.raises(
        ValueError,
        match="NDCG@K requires non-empty graded ground-truth relevance labels",
    ):
        evaluator.ndcg_at_k(recs, relevance_grades={}, k=3)


def test_precision_at_k_hand_calculated() -> None:
    """Verify Precision@K calculation against hand-computed ground truth.

    Setup:
        Recommended top 5: [A, B, C, D, E]
        Relevant set: {B, D, F, G} (4 relevant total)
        Hits in top 3: {B} -> 1/3 = 0.3333
        Hits in top 5: {B, D} -> 2/5 = 0.4000
    """
    evaluator = RecommenderEvaluator(is_synthetic_benchmark=True)
    recs = ["A", "B", "C", "D", "E"]
    relevant = ["B", "D", "F", "G"]

    assert evaluator.precision_at_k(recs, relevant, k=3) == pytest.approx(
        1 / 3, abs=1e-4
    )
    assert evaluator.precision_at_k(recs, relevant, k=5) == 0.4000


def test_recall_at_k_hand_calculated() -> None:
    """Verify Recall@K calculation against hand-computed ground truth.

    Setup:
        Recommended top 5: [A, B, C, D, E]
        Relevant set: {B, D, F, G} (4 items)
        Hits in top 3: 1 hit -> 1/4 = 0.2500
        Hits in top 5: 2 hits -> 2/4 = 0.5000
    """
    evaluator = RecommenderEvaluator(is_synthetic_benchmark=True)
    recs = ["A", "B", "C", "D", "E"]
    relevant = ["B", "D", "F", "G"]

    assert evaluator.recall_at_k(recs, relevant, k=3) == 0.2500
    assert evaluator.recall_at_k(recs, relevant, k=5) == 0.5000


def test_ndcg_at_k_hand_calculated() -> None:
    """Verify NDCG@K calculation against manual mathematical expansion.

    Setup:
        Recommended top 3: [A, B, C]
        Relevance grades: {'A': 3, 'B': 0, 'C': 2, 'D': 3}
        Ideal ranking order: [3, 3, 2] (items A, D, C)

        DCG@3:
            pos 1 (A, rel=3): (2^3 - 1) / log2(2) = 7 / 1.0 = 7.0
            pos 2 (B, rel=0): 0
            pos 3 (C, rel=2): (2^2 - 1) / log2(4) = 3 / 2.0 = 1.5
            DCG@3 = 7.0 + 0 + 1.5 = 8.5

        IDCG@3:
            pos 1 (rel=3): 7 / 1.0 = 7.0
            pos 2 (rel=3): 7 / log2(3) = 7 / 1.5849625 = 4.417037
            pos 3 (rel=2): 3 / log2(4) = 1.5
            IDCG@3 = 7.0 + 4.417037 + 1.5 = 12.917037

        NDCG@3 = 8.5 / 12.917037 = 0.658046 -> ~0.6580
    """
    evaluator = RecommenderEvaluator(is_synthetic_benchmark=True)
    recs = ["A", "B", "C"]
    grades = {"A": 3.0, "B": 0.0, "C": 2.0, "D": 3.0}

    computed_ndcg = evaluator.ndcg_at_k(recs, grades, k=3)
    assert computed_ndcg == pytest.approx(0.6580, abs=1e-3)


def test_kendall_tau_sanity() -> None:
    """Verify Kendall's tau rank correlation calculation on known orderings."""
    evaluator = RecommenderEvaluator()

    # Identical rankings -> tau = +1.0
    r1 = ["A", "B", "C", "D"]
    r2 = ["A", "B", "C", "D"]
    assert evaluator.compute_kendall_tau(r1, r2) == 1.0

    # Completely reversed rankings -> tau = -1.0
    r3 = ["D", "C", "B", "A"]
    assert evaluator.compute_kendall_tau(r1, r3) == -1.0

    # One pair inverted: [A, B, D, C] (1 discordant pair out of 6 pairs)
    # tau = (5 - 1) / 6 = 4/6 = 0.6667
    r4 = ["A", "B", "D", "C"]
    assert evaluator.compute_kendall_tau(r1, r4) == pytest.approx(0.6667, abs=1e-3)


def test_calculate_coverage() -> None:
    """Verify coverage calculation for various pool and catalog sizes."""
    evaluator = RecommenderEvaluator()
    assert evaluator.calculate_coverage([], total_catalog_size=100) == 0.0
    assert evaluator.calculate_coverage(["A", "B", "C"], total_catalog_size=0) == 0.0
    assert (
        evaluator.calculate_coverage(["A", "B", "B", "C"], total_catalog_size=10)
        == 30.0
    )


def test_calculate_brand_diversity() -> None:
    """Verify brand diversity ratio and Shannon entropy computation."""
    evaluator = RecommenderEvaluator()
    empty_div = evaluator.calculate_brand_diversity([])
    assert empty_div["unique_brands"] == 0.0
    assert empty_div["shannon_entropy"] == 0.0

    single_brand = evaluator.calculate_brand_diversity(["Apple", "Apple", "Apple"])
    assert single_brand["unique_brands"] == 1.0
    assert single_brand["diversity_ratio"] == pytest.approx(1 / 3, abs=1e-3)
    assert single_brand["shannon_entropy"] == 0.0

    multi_brands = evaluator.calculate_brand_diversity(
        ["Apple", "Samsung", "Xiaomi", "OnePlus"]
    )
    assert multi_brands["unique_brands"] == 4.0
    assert multi_brands["diversity_ratio"] == 1.0
    assert multi_brands["shannon_entropy"] == pytest.approx(2.0, abs=1e-3)


def test_benchmark_latency() -> None:
    """Verify benchmark_latency reports p50, p95, mean, and min latencies."""
    evaluator = RecommenderEvaluator()
    res = evaluator.benchmark_latency(lambda: sum(range(1000)), iterations=10)
    assert "p50_latency_ms" in res
    assert "p95_latency_ms" in res
    assert "mean_latency_ms" in res
    assert "min_latency_ms" in res
    assert res["min_latency_ms"] >= 0.0


def test_load_relevance_benchmark() -> None:
    """Verify load_relevance_benchmark parses CSV and raises FileNotFoundError when absent."""
    from pathlib import Path

    from src.evaluation import load_relevance_benchmark

    with pytest.raises(FileNotFoundError):
        load_relevance_benchmark("non_existent_file.csv")

    real_path = Path("data/synthetic_relevance_benchmark.csv")
    if real_path.exists():
        profiles = load_relevance_benchmark(real_path)
        assert len(profiles) > 0
        first_pid = next(iter(profiles))
        assert "grades" in profiles[first_pid]
        assert "relevant_ids" in profiles[first_pid]


def test_evaluate_perturbation_stability() -> None:
    """Verify evaluate_perturbation_stability calculates mean tau across preference dimensions."""
    from src.data_loader import DataLoader
    from src.preprocessing import FeaturePreprocessor
    from src.recommender import SmartPickRecommender, UserPreferences

    loader = DataLoader("data/phones.csv")
    df, _ = loader.load_and_validate()
    preprocessor = FeaturePreprocessor(strategy="robust_minmax")
    preprocessor.fit(df)
    recommender = SmartPickRecommender(df, preprocessor)

    evaluator = RecommenderEvaluator()
    base_prefs = UserPreferences(min_budget=10000, max_budget=40000)
    stability = evaluator.run_sensitivity_analysis(
        recommender, base_prefs, perturbation=0.20
    )
    assert "mean_stability_tau" in stability
    assert -1.0 <= stability["mean_stability_tau"] <= 1.0
    assert "dimension_taus" in stability
