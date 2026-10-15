"""Unit tests for content-based similarity, blended ranking, and MMR diversity re-ranking."""

import pandas as pd
import pytest

from src.data_loader import DataLoader
from src.preprocessing import FeaturePreprocessor
from src.similarity import ContentSimilarityEngine


@pytest.fixture(scope="module")
def sample_catalog() -> pd.DataFrame:
    """Load canonical catalog DataFrame."""
    loader = DataLoader("data/phones.csv")
    df, _ = loader.load_and_validate()
    return df


@pytest.fixture(scope="module")
def similarity_engine(sample_catalog: pd.DataFrame) -> ContentSimilarityEngine:
    """Initialize fitted similarity engine."""
    preprocessor = FeaturePreprocessor(strategy="robust_minmax")
    preprocessor.fit(sample_catalog)
    return ContentSimilarityEngine(sample_catalog, preprocessor)


def test_similarity_find_similar_determinism(
    similarity_engine: ContentSimilarityEngine, sample_catalog: pd.DataFrame
) -> None:
    """Verify that find_similar_phones produces deterministic output for an anchor phone."""
    ref_phone = "OnePlus 12"
    candidates = sample_catalog[sample_catalog["phone_name"] != ref_phone]

    recs_1 = similarity_engine.find_similar_phones(ref_phone, candidates, top_k=5)
    recs_2 = similarity_engine.find_similar_phones(ref_phone, candidates, top_k=5)

    assert len(recs_1) == 5
    assert [r["phone_name"] for r in recs_1] == [r["phone_name"] for r in recs_2]
    # Cosine score should be high for similar flagships
    assert recs_1[0]["similarity_score"] > 70.0


def test_similarity_find_similar_unknown_raises(
    similarity_engine: ContentSimilarityEngine, sample_catalog: pd.DataFrame
) -> None:
    """Verify ValueError is raised if reference device does not exist."""
    with pytest.raises(ValueError, match="not found in catalog"):
        similarity_engine.find_similar_phones("NonExistentPhone", sample_catalog)


def test_blended_scoring_endpoints(similarity_engine: ContentSimilarityEngine) -> None:
    """Verify blend_scores satisfies alpha=0 (pure baseline) and alpha=1 (pure similarity)."""
    base_scores = {"Phone A": 80.0, "Phone B": 60.0}
    sim_scores = {"Phone A": 40.0, "Phone B": 90.0}

    # alpha = 0.0 -> pure baseline
    pure_base = similarity_engine.blend_scores(
        base_scores, sim_scores, blend_factor=0.0
    )
    assert pure_base["Phone A"] == 80.0
    assert pure_base["Phone B"] == 60.0

    # alpha = 1.0 -> pure similarity
    pure_sim = similarity_engine.blend_scores(base_scores, sim_scores, blend_factor=1.0)
    assert pure_sim["Phone A"] == 40.0
    assert pure_sim["Phone B"] == 90.0

    # alpha = 0.5 -> exact midpoint
    half = similarity_engine.blend_scores(base_scores, sim_scores, blend_factor=0.5)
    assert half["Phone A"] == 60.0
    assert half["Phone B"] == 75.0


def test_mmr_rerank_diversity_boost(
    similarity_engine: ContentSimilarityEngine, sample_catalog: pd.DataFrame
) -> None:
    """Verify MMR diversity re-ranking reduces redundant clustering compared to pure relevance."""
    # Group of devices where some belong to the same brand/model family
    names = [
        "Samsung Galaxy M14 5G",
        "Samsung Galaxy F14 5G",  # Nearly identical to M14
        "Samsung Galaxy M34 5G",  # Same family
        "Moto G34 5G",  # Different brand
        "POCO M6 Pro 5G",  # Different brand
        "Realme 12x 5G",  # Different brand
    ]
    relevance = {
        "Samsung Galaxy M14 5G": 95.0,
        "Samsung Galaxy F14 5G": 94.0,
        "Samsung Galaxy M34 5G": 93.0,
        "Moto G34 5G": 90.0,
        "POCO M6 Pro 5G": 89.0,
        "Realme 12x 5G": 88.0,
    }

    # Under pure relevance (lambda=1.0), all top 3 are Samsung
    pure_rel = similarity_engine.mmr_rerank(names, relevance, top_k=4, lambda_param=1.0)
    assert pure_rel[0] == "Samsung Galaxy M14 5G"
    assert pure_rel[1] == "Samsung Galaxy F14 5G"
    assert pure_rel[2] == "Samsung Galaxy M34 5G"

    # Under balanced MMR (lambda=0.5), diversity penalizes redundant Samsung devices
    diverse_mmr = similarity_engine.mmr_rerank(
        names, relevance, top_k=4, lambda_param=0.5
    )
    assert (
        diverse_mmr[0] == "Samsung Galaxy M14 5G"
    )  # First pick is still best relevance
    # Second or third pick should incorporate alternative brands (Moto or POCO)
    assert any(b in diverse_mmr[:3] for b in ["Moto G34 5G", "POCO M6 Pro 5G"])


def test_recommender_blended_and_mmr_integration(sample_catalog: pd.DataFrame) -> None:
    """Verify SmartPickRecommender rank_blended, rank_diverse_mmr, and recommend dispatcher."""
    from src.recommender import SmartPickRecommender, UserPreferences

    preprocessor = FeaturePreprocessor(strategy="robust_minmax")
    preprocessor.fit(sample_catalog)
    recommender = SmartPickRecommender(sample_catalog, preprocessor)

    prefs = UserPreferences(
        min_budget=10000,
        max_budget=40000,
        ranking_mode="blended",
        blend_factor=0.40,
        reference_phone="OnePlus 12",
    )
    blended_recs = recommender.recommend(prefs, top_k=5)
    assert len(blended_recs) == 5
    assert all("blended" in r.ranking_method for r in blended_recs)

    # Test MMR ranking mode dispatch
    prefs_mmr = UserPreferences(
        min_budget=10000,
        max_budget=40000,
        ranking_mode="mmr",
        diversity_lambda=0.60,
    )
    mmr_recs = recommender.recommend(prefs_mmr, top_k=5)
    assert len(mmr_recs) == 5
    assert all("mmr" in r.ranking_method for r in mmr_recs)

    # Test similarity mode dispatch
    prefs_sim = UserPreferences(
        min_budget=10000,
        max_budget=40000,
        ranking_mode="similarity",
        reference_phone="OnePlus 12",
    )
    sim_recs = recommender.recommend(prefs_sim, top_k=5)
    assert len(sim_recs) == 5

    # Test baseline mode dispatch
    prefs_base = UserPreferences(
        min_budget=10000,
        max_budget=40000,
        ranking_mode="baseline",
    )
    base_recs = recommender.recommend(prefs_base, top_k=5)
    assert len(base_recs) == 5
