"""Sensitivity and What-If analysis engine for SmartPick AI.

Simulates the effect of weight shifts on device rankings and calculates rank
movements (up/down arrows) to provide users with transparent sensitivity insights.
"""

from dataclasses import dataclass

from src.recommender import SmartPickRecommender, UserPreferences


@dataclass(frozen=True)
class RankMovement:
    """Represents rank displacement of a device under a simulated weight shift."""

    phone_name: str
    original_rank: int
    simulated_rank: int | None
    delta_rank: int  # Positive means moved up, negative means moved down
    indicator: str  # e.g. "▲ +2", "▼ -1", "= Same", "▼ Dropped"
    original_score: float
    simulated_score: float


def compute_what_if_movement(
    recommender: SmartPickRecommender,
    base_prefs: UserPreferences,
    boost_dimension: str,
    boost_amount: float = 0.30,
    top_k: int = 5,
) -> list[RankMovement]:
    """Compute before-and-after ranking shifts when a single preference weight is boosted.

    Args:
        recommender: Initialized SmartPickRecommender.
        base_prefs: Baseline UserPreferences.
        boost_dimension: Dimension to adjust ('performance', 'camera', 'battery', 'display', 'storage', 'value').
        boost_amount: Amount to add to selected dimension weight (default 0.30).
        top_k: Number of top results to track.

    Returns:
        List of RankMovement records for the top baseline devices.
    """
    candidates = recommender.filter_candidates(base_prefs)
    base_results = recommender.rank_baseline(
        candidates, base_prefs, top_k=len(candidates)
    )

    # Construct modified preferences with boosted weight
    prefs_dict = base_prefs.model_dump()
    weight_key = f"weight_{boost_dimension.lower()}"
    if weight_key in prefs_dict:
        prefs_dict[weight_key] = min(
            1.0, max(0.0, prefs_dict[weight_key] + boost_amount)
        )
    else:
        prefs_dict[weight_key] = min(1.0, max(0.0, boost_amount))

    sim_prefs = UserPreferences(**prefs_dict)
    sim_results = recommender.rank_baseline(
        candidates, sim_prefs, top_k=len(candidates)
    )

    sim_rank_map = {res.phone_name: idx + 1 for idx, res in enumerate(sim_results)}
    sim_score_map = {res.phone_name: res.match_score for res in sim_results}

    movements: list[RankMovement] = []

    for orig_idx, base_res in enumerate(base_results[:top_k]):
        name = base_res.phone_name
        orig_rank = orig_idx + 1
        sim_rank = sim_rank_map.get(name)
        sim_score = sim_score_map.get(name, 0.0)

        if sim_rank is None:
            delta = -99
            indicator = "▼ Dropped"
        elif sim_rank < orig_rank:
            delta = orig_rank - sim_rank
            indicator = f"▲ +{delta}"
        elif sim_rank > orig_rank:
            delta = orig_rank - sim_rank
            indicator = f"▼ {delta}"
        else:
            delta = 0
            indicator = "= Same"

        movements.append(
            RankMovement(
                phone_name=name,
                original_rank=orig_rank,
                simulated_rank=sim_rank,
                delta_rank=delta,
                indicator=indicator,
                original_score=base_res.match_score,
                simulated_score=sim_score,
            )
        )

    return movements
