"""Test suite for FeaturePreprocessor scaling, NaN preservation, and persistence."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.preprocessing import FeaturePreprocessor


@pytest.fixture
def sample_features_df() -> pd.DataFrame:
    """Fixture providing sample unscaled specification DataFrame with outliers and NaNs."""
    return pd.DataFrame(
        [
            {
                "processor_score": 400000.0,
                "camera_mp": 50.0,
                "battery_mah": 5000.0,
                "display_hz": 90.0,
                "storage_gb": 128.0,
                "ram_gb": 6.0,
            },
            {
                "processor_score": 800000.0,
                "camera_mp": 64.0,
                "battery_mah": 5000.0,
                "display_hz": 120.0,
                "storage_gb": 256.0,
                "ram_gb": 8.0,
            },
            {
                "processor_score": 1500000.0,
                "camera_mp": 50.0,
                "battery_mah": 5500.0,
                "display_hz": 144.0,
                "storage_gb": 256.0,
                "ram_gb": 12.0,
            },
            # Outlier row (extreme AnTuTu and extreme camera)
            {
                "processor_score": 2200000.0,
                "camera_mp": 200.0,
                "battery_mah": 6000.0,
                "display_hz": 120.0,
                "storage_gb": 1024.0,
                "ram_gb": 16.0,
            },
            # Missing values row (battery and benchmark missing)
            {
                "processor_score": np.nan,
                "camera_mp": 12.0,
                "battery_mah": np.nan,
                "display_hz": 60.0,
                "storage_gb": 64.0,
                "ram_gb": 4.0,
            },
        ]
    )


class TestFeaturePreprocessorScaling:
    """Tests for outlier robustness, scaling bounds, and NaN preservation."""

    def test_robust_minmax_preserves_nans(
        self, sample_features_df: pd.DataFrame
    ) -> None:
        """Verify missing specs remain strictly NaN and are not filled with 0."""
        preprocessor = FeaturePreprocessor(strategy="robust_minmax")
        scaled_df = preprocessor.fit_transform(sample_features_df)

        # Row 4 had NaN for processor_score and battery_mah
        assert np.isnan(scaled_df.loc[4, "processor_score"])
        assert np.isnan(scaled_df.loc[4, "battery_mah"])
        # Non-null values should be strictly within [0.0, 1.0]
        assert not np.isnan(scaled_df.loc[4, "display_hz"])
        assert 0.0 <= scaled_df.loc[4, "display_hz"] <= 1.0

    def test_robust_minmax_scaling_bounds(
        self, sample_features_df: pd.DataFrame
    ) -> None:
        """Verify scaled non-null values are bounded strictly within [0.0, 1.0]."""
        preprocessor = FeaturePreprocessor(strategy="robust_minmax")
        scaled_df = preprocessor.fit_transform(sample_features_df)

        for col in preprocessor.feature_names_in_:
            non_null = scaled_df[col].dropna()
            assert (non_null >= 0.0).all(), f"Values below 0 in {col}"
            assert (non_null <= 1.0).all(), f"Values above 1 in {col}"

    def test_minmax_strategy(self, sample_features_df: pd.DataFrame) -> None:
        """Verify standard minmax strategy functions correctly."""
        preprocessor = FeaturePreprocessor(strategy="minmax")
        scaled_df = preprocessor.fit_transform(sample_features_df)

        assert 0.0 <= scaled_df["processor_score"].dropna().min() <= 1.0
        assert 0.0 <= scaled_df["processor_score"].dropna().max() <= 1.0

    def test_robust_scaler_strategy(self, sample_features_df: pd.DataFrame) -> None:
        """Verify robust (median-IQR) strategy scales features."""
        preprocessor = FeaturePreprocessor(strategy="robust")
        scaled_df = preprocessor.fit_transform(sample_features_df)
        assert not scaled_df.empty

    def test_feature_availability_mask(self, sample_features_df: pd.DataFrame) -> None:
        """Verify get_feature_availability accurately tracks presence vs missing."""
        preprocessor = FeaturePreprocessor()
        preprocessor.fit(sample_features_df)
        avail = preprocessor.get_feature_availability(sample_features_df)

        assert bool(avail.loc[4, "battery_mah"]) is False
        assert bool(avail.loc[0, "battery_mah"]) is True


class TestFeaturePreprocessorPersistence:
    """Tests for joblib serialization and feature order preservation."""

    def test_save_and_load_roundtrip(
        self, sample_features_df: pd.DataFrame, tmp_path: Path
    ) -> None:
        """Verify fitted preprocessor can be saved with joblib and reloaded with identical behavior."""
        save_path = tmp_path / "fitted_scaler.joblib"
        orig_preprocessor = FeaturePreprocessor(strategy="robust_minmax")
        orig_scaled = orig_preprocessor.fit_transform(sample_features_df)
        orig_preprocessor.save(save_path)

        assert save_path.exists()

        loaded_preprocessor = FeaturePreprocessor.load(save_path)
        assert loaded_preprocessor.is_fitted_ is True
        assert (
            loaded_preprocessor.feature_names_in_ == orig_preprocessor.feature_names_in_
        )
        assert loaded_preprocessor.strategy == orig_preprocessor.strategy

        loaded_scaled = loaded_preprocessor.transform(sample_features_df)
        pd.testing.assert_frame_equal(orig_scaled, loaded_scaled)

    def test_save_unfitted_raises_error(self, tmp_path: Path) -> None:
        """Verify attempting to save an unfitted preprocessor raises RuntimeError."""
        unfitted = FeaturePreprocessor()
        with pytest.raises(RuntimeError):
            unfitted.save(tmp_path / "unfitted.joblib")

    def test_transform_unfitted_raises_error(
        self, sample_features_df: pd.DataFrame
    ) -> None:
        """Verify attempting to transform before fitting raises RuntimeError."""
        unfitted = FeaturePreprocessor()
        with pytest.raises(RuntimeError):
            unfitted.transform(sample_features_df)

    def test_load_nonexistent_file_error(self) -> None:
        """Verify load raises FileNotFoundError if file is missing."""
        with pytest.raises(FileNotFoundError):
            FeaturePreprocessor.load("data/missing_preprocessor_file_xyz.joblib")

    def test_load_wrong_type_error(self, tmp_path: Path) -> None:
        """Verify load raises TypeError if object is not FeaturePreprocessor."""
        import joblib

        fake_path = tmp_path / "fake.joblib"
        joblib.dump({"not": "a preprocessor"}, fake_path)
        with pytest.raises(TypeError):
            FeaturePreprocessor.load(fake_path)

    def test_identical_column_values_scaling(self) -> None:
        """Verify columns with identical values handle division by zero safely."""
        single_val_df = pd.DataFrame(
            [
                {"processor_score": 500000.0, "camera_mp": 50.0},
                {"processor_score": 500000.0, "camera_mp": 50.0},
            ]
        )
        preprocessor = FeaturePreprocessor(
            feature_columns=["processor_score", "camera_mp"]
        )
        scaled = preprocessor.fit_transform(single_val_df)
        assert not scaled.empty

    def test_transform_with_missing_columns(self) -> None:
        """Verify transforming DataFrame missing some fitted columns outputs NaNs for them."""
        df_full = pd.DataFrame(
            {"processor_score": [500000.0, 700000.0], "camera_mp": [50.0, 64.0]}
        )
        preprocessor = FeaturePreprocessor(
            feature_columns=["processor_score", "camera_mp"]
        ).fit(df_full)

        df_partial = pd.DataFrame({"processor_score": [600000.0]})
        scaled = preprocessor.transform(df_partial)
        assert "camera_mp" in scaled.columns
        assert np.isnan(scaled.loc[0, "camera_mp"])
