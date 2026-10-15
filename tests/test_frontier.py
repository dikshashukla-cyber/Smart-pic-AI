"""Unit tests for Pareto Efficiency Frontier module."""

import pandas as pd
import pytest

from src.frontier import compute_pareto_frontier
from src.preprocessing import FeaturePreprocessor


@pytest.fixture
def sample_candidates() -> pd.DataFrame:
    """Fixture with synthetic devices for Pareto frontier verification."""
    data = [
        # Cheap and powerful: Should be on Pareto frontier
        {
            "phone_name": "Device A",
            "price_inr": 10000.0,
            "processor_score": 600000.0,
            "battery_mah": 6000.0,
            "camera_mp": 50.0,
            "display_hz": 120.0,
            "storage_gb": 128.0,
            "ram_gb": 8.0,
        },
        # More expensive than A and weaker than A: strictly dominated by A
        {
            "phone_name": "Device B",
            "price_inr": 15000.0,
            "processor_score": 400000.0,
            "battery_mah": 5000.0,
            "camera_mp": 50.0,
            "display_hz": 90.0,
            "storage_gb": 128.0,
            "ram_gb": 6.0,
        },
        # More expensive than A but significantly more powerful: on frontier
        {
            "phone_name": "Device C",
            "price_inr": 25000.0,
            "processor_score": 1400000.0,
            "battery_mah": 5500.0,
            "camera_mp": 64.0,
            "display_hz": 144.0,
            "storage_gb": 256.0,
            "ram_gb": 12.0,
        },
        # Extremely expensive flagship with highest specs: on frontier
        {
            "phone_name": "Device D",
            "price_inr": 70000.0,
            "processor_score": 2100000.0,
            "battery_mah": 5400.0,
            "camera_mp": 200.0,
            "display_hz": 144.0,
            "storage_gb": 512.0,
            "ram_gb": 16.0,
        },
        # Same price as D but weaker specs: strictly dominated by D
        {
            "phone_name": "Device E",
            "price_inr": 70000.0,
            "processor_score": 1200000.0,
            "battery_mah": 4500.0,
            "camera_mp": 50.0,
            "display_hz": 120.0,
            "storage_gb": 128.0,
            "ram_gb": 8.0,
        },
    ]
    return pd.DataFrame(data)


def test_pareto_frontier_identifies_optimal_devices(
    sample_candidates: pd.DataFrame,
) -> None:
    """Verify Pareto frontier correctly separates non-dominated devices from dominated ones."""
    preprocessor = FeaturePreprocessor(strategy="minmax")
    preprocessor.fit(sample_candidates)

    frontier_df = compute_pareto_frontier(sample_candidates, preprocessor)

    optimal_names = set(frontier_df[frontier_df["is_pareto_optimal"]]["phone_name"])

    # Device A, C, D should be on frontier
    assert "Device A" in optimal_names
    assert "Device C" in optimal_names
    assert "Device D" in optimal_names

    # Device B (worse and more expensive than A) must NOT be on frontier
    assert "Device B" not in optimal_names
    # Device E (worse than D at same price) must NOT be on frontier
    assert "Device E" not in optimal_names


def test_pareto_frontier_empty_input() -> None:
    """Verify empty candidates DataFrame returns empty without error."""
    preprocessor = FeaturePreprocessor(strategy="robust_minmax")
    empty_df = pd.DataFrame(columns=["phone_name", "price_inr"])
    res = compute_pareto_frontier(empty_df, preprocessor)
    assert res.empty
