"""Content-based similarity engine and diversity-aware re-ranking module for SmartPick AI.

Implements TRD Section 6.2 and 6.3:
1. Feature Matrix Construction:
   - Scaled numeric features from FeaturePreprocessor.
   - One-hot encoded brand representations.
   - Cosine similarity with strict budget independence.
2. Similarity Ranking:
   - Reference-based similarity: "Find similar" given an anchor device.
   - Profile-based similarity: Cosine match against user target spec profile.
3. Blended Hybrid Scoring:
   - Weighted blend: (1 - alpha) * baseline_score + alpha * similarity_score.
   - Avoids feature double-counting by normalizing baseline and similarity indices to [0, 100].
4. Maximal Marginal Relevance (MMR) Diversity Re-ranker:
   - Iterative greedy selection balancing relevance vs pairwise similarity:
     MMR(d) = lambda * Sim(d, query) - (1 - lambda) * max_{s in S} Sim(d, s)
   - Prevents Top-K saturation by near-duplicate variants and same-brand clusters.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from src.preprocessing import DEFAULT_FEATURE_COLUMNS, FeaturePreprocessor

logger = logging.getLogger(__name__)


class ContentSimilarityEngine:
    """Content-based similarity model and diversity-aware re-ranking engine."""

    def __init__(
        self,
        catalog_df: pd.DataFrame,
        preprocessor: FeaturePreprocessor,
        feature_columns: list[str] | None = None,
    ) -> None:
        """Initialize similarity engine with catalog data and fitted feature preprocessor.

        Args:
            catalog_df: Canonical DataFrame of smartphones.
            preprocessor: Fitted FeaturePreprocessor instance.
            feature_columns: List of numeric spec columns to include.
        """
        self.catalog_df = catalog_df.copy()
        self.preprocessor = preprocessor
        self.feature_columns = feature_columns or DEFAULT_FEATURE_COLUMNS.copy()

        # Build device index mapping
        self.phone_names = self.catalog_df["phone_name"].tolist()
        self.name_to_idx = {name: idx for idx, name in enumerate(self.phone_names)}

        # Build feature matrix
        self.feature_matrix, self.feature_names = self._build_feature_matrix()

    def _build_feature_matrix(self) -> tuple[np.ndarray, list[str]]:
        """Construct normalized composite feature matrix (scaled numeric specs + one-hot brand).

        Missing numeric specifications are imputed with median of scaled specs (0.50)
        exclusively for cosine distance calculations without corrupting catalog data.
        """
        # 1. Scaled numeric features
        scaled_df = self.preprocessor.transform(self.catalog_df)
        numeric_matrix = scaled_df[self.feature_columns].to_numpy(dtype=float)

        # Impute NaNs with neutral 0.50 (midpoint of [0, 1]) for distance vector algebra only
        numeric_matrix = np.nan_to_num(numeric_matrix, nan=0.50)

        # 2. One-hot encoded brand features
        brand_series = self.catalog_df["brand"].fillna("Unknown").astype(str)
        brand_dummies = pd.get_dummies(brand_series, prefix="brand", dtype=float)
        brand_matrix = brand_dummies.to_numpy()

        # Combine with weight scaling: brand given 0.35 relative weight to prevent dominating specs
        brand_weight = 0.35
        composite_matrix = np.hstack([numeric_matrix, brand_matrix * brand_weight])

        all_names = list(self.feature_columns) + list(brand_dummies.columns)
        return composite_matrix, all_names

    def get_device_vector(self, phone_name: str) -> np.ndarray | None:
        """Retrieve composite feature vector for a device by exact name."""
        idx = self.name_to_idx.get(phone_name)
        if idx is None:
            return None
        return self.feature_matrix[idx]

    def compute_pairwise_similarity(self, idx1: int, idx2: int) -> float:
        """Compute cosine similarity between two devices by index."""
        v1 = self.feature_matrix[idx1].reshape(1, -1)
        v2 = self.feature_matrix[idx2].reshape(1, -1)
        return float(cosine_similarity(v1, v2)[0, 0])

    def find_similar_phones(
        self,
        reference_phone_name: str,
        candidates_df: pd.DataFrame,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Find devices most similar to an anchor device using cosine similarity.

        Budget and brand constraints are applied independently via candidates_df.

        Args:
            reference_phone_name: Target phone name to compare against.
            candidates_df: Eligible devices meeting hard filters.
            top_k: Number of similar devices to return.

        Returns:
            List of device records with 'similarity_score' in [0, 100].
        """
        ref_idx = self.name_to_idx.get(reference_phone_name)
        if ref_idx is None:
            raise ValueError(
                f"Reference device '{reference_phone_name}' not found in catalog."
            )

        ref_vector = self.feature_matrix[ref_idx].reshape(1, -1)

        candidate_indices = [
            self.name_to_idx[name]
            for name in candidates_df["phone_name"]
            if name in self.name_to_idx and name != reference_phone_name
        ]

        if not candidate_indices:
            return []

        cand_matrix = self.feature_matrix[candidate_indices]
        sims = cosine_similarity(ref_vector, cand_matrix)[0]

        # Pair candidates with similarity scores
        scored_candidates = []
        for cand_idx, score in zip(candidate_indices, sims):
            row = self.catalog_df.iloc[cand_idx]
            # Rescale cosine [-1, 1] to [0, 100]
            pct_score = float(np.clip((score + 1.0) / 2.0 * 100.0, 0.0, 100.0))
            scored_candidates.append(
                {
                    "phone_name": row["phone_name"],
                    "brand": row["brand"],
                    "price_inr": float(row["price_inr"]),
                    "similarity_score": pct_score,
                    "raw_cosine": float(score),
                }
            )

        # Deterministic sort: similarity_score desc, price asc, name asc
        scored_candidates.sort(
            key=lambda x: (-x["similarity_score"], x["price_inr"], x["phone_name"])
        )
        return scored_candidates[:top_k]

    def compute_profile_similarity(
        self,
        target_specs: dict[str, float],
        preferred_brand: str | None,
        candidates_df: pd.DataFrame,
    ) -> dict[str, float]:
        """Compute cosine similarity between an idealized user profile vector and candidates.

        Args:
            target_specs: Dict of normalized spec targets in [0, 1] (e.g. {'battery_mah': 0.8}).
            preferred_brand: Primary preferred brand if specified.
            candidates_df: Eligible candidates.

        Returns:
            Mapping from phone_name to similarity score in [0, 100].
        """
        # Construct synthetic profile vector matching composite matrix shape
        profile_vec = np.zeros(len(self.feature_names), dtype=float)

        for col_idx, col_name in enumerate(self.feature_columns):
            if col_name in target_specs:
                profile_vec[col_idx] = float(np.clip(target_specs[col_name], 0.0, 1.0))
            else:
                profile_vec[col_idx] = 0.50  # Neutral default

        if preferred_brand:
            brand_col = f"brand_{preferred_brand.lower()}"
            for idx, fname in enumerate(self.feature_names):
                if fname.lower() == brand_col:
                    profile_vec[idx] = 0.35

        profile_vec_2d = profile_vec.reshape(1, -1)

        candidate_indices = [
            self.name_to_idx[name]
            for name in candidates_df["phone_name"]
            if name in self.name_to_idx
        ]

        if not candidate_indices:
            return {}

        cand_matrix = self.feature_matrix[candidate_indices]
        sims = cosine_similarity(profile_vec_2d, cand_matrix)[0]

        scores_by_name = {}
        for cand_idx, score in zip(candidate_indices, sims):
            name = self.phone_names[cand_idx]
            pct_score = float(np.clip((score + 1.0) / 2.0 * 100.0, 0.0, 100.0))
            scores_by_name[name] = pct_score

        return scores_by_name

    def blend_scores(
        self,
        baseline_scores: dict[str, float],
        similarity_scores: dict[str, float],
        blend_factor: float = 0.35,
    ) -> dict[str, float]:
        """Blend baseline heuristic scores with content similarity scores.

        Formula:
            blended_score = (1 - alpha) * baseline_score + alpha * similarity_score

        Args:
            baseline_scores: Mapping from phone_name to baseline score [0, 100].
            similarity_scores: Mapping from phone_name to similarity score [0, 100].
            blend_factor: Alpha weight in [0.0, 1.0] for similarity contribution.

        Returns:
            Mapping from phone_name to blended score [0, 100].
        """
        alpha = float(np.clip(blend_factor, 0.0, 1.0))
        blended = {}
        for name, b_score in baseline_scores.items():
            sim_score = similarity_scores.get(name, b_score)
            blended[name] = round((1.0 - alpha) * b_score + alpha * sim_score, 2)
        return blended

    def mmr_rerank(
        self,
        candidate_names: list[str],
        relevance_scores: dict[str, float],
        top_k: int = 5,
        lambda_param: float = 0.70,
    ) -> list[str]:
        """Apply Maximal Marginal Relevance (MMR) greedy selection for diversity-aware ranking.

        Objective:
            MMR(d) = argmax_{d in C \\ S} [ lambda * Rel(d) - (1 - lambda) * max_{s in S} Sim(d, s) ]

        Args:
            candidate_names: List of candidate devices to consider.
            relevance_scores: Mapping from phone_name to relevance/match score in [0, 100].
            top_k: Target number of diverse recommendations.
            lambda_param: Trade-off parameter in [0.0, 1.0].
                1.0 = Pure relevance (identical to standard baseline).
                0.0 = Maximum diversity (disregards relevance after first pick).
                0.7 = Standard balanced recommender setting.

        Returns:
            Ordered list of top_k diverse device names.
        """
        if not candidate_names:
            return []

        lambda_val = float(np.clip(lambda_param, 0.0, 1.0))

        # Filter valid candidate indices
        valid_candidates = [
            name for name in candidate_names if name in self.name_to_idx
        ]
        if not valid_candidates:
            return candidate_names[:top_k]

        # Normalize relevance scores to [0, 1]
        max_rel = max(
            (relevance_scores.get(n, 0.0) for n in valid_candidates), default=1.0
        )
        rel_norm = {
            n: relevance_scores.get(n, 0.0) / (max_rel if max_rel > 0 else 1.0)
            for n in valid_candidates
        }

        selected: list[str] = []
        remaining = list(valid_candidates)

        # 1. First pick is strictly the highest relevance device
        first_pick = max(remaining, key=lambda n: rel_norm[n])
        selected.append(first_pick)
        remaining.remove(first_pick)

        # 2. Iteratively pick devices maximizing marginal relevance
        while len(selected) < min(top_k, len(valid_candidates)) and remaining:
            best_mmr_score = -float("inf")
            best_candidate = remaining[0]

            for cand_name in remaining:
                cand_idx = self.name_to_idx[cand_name]
                cand_vec = self.feature_matrix[cand_idx].reshape(1, -1)

                # Find maximum similarity to any already selected device
                selected_indices = [self.name_to_idx[s] for s in selected]
                selected_matrix = self.feature_matrix[selected_indices]
                pairwise_sims = cosine_similarity(cand_vec, selected_matrix)[0]
                max_sim_to_selected = float(np.max(pairwise_sims))

                # MMR score formula
                rel_component = rel_norm[cand_name]
                div_penalty = max_sim_to_selected
                mmr_score = (
                    lambda_val * rel_component - (1.0 - lambda_val) * div_penalty
                )

                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_candidate = cand_name

            selected.append(best_candidate)
            remaining.remove(best_candidate)

        return selected
