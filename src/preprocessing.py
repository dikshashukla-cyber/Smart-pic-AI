"""Data preprocessing and feature scaling module for SmartPick AI.

Implements fitted feature scaling with joblib persistence, outlier-resilient
transformations, and an explicit missing-value policy (preserving NaNs for
per-phone weight renormalization rather than fabricating values).

SCALING STRATEGY COMPARISON & EVIDENCE:
----------------------------------------
1. Standard Min-Max Scaling:
   x_scaled = (x - min) / (max - min)
   - Weakness: Vulnerable to catalog outliers (e.g., 200 MP sensors, 2.2M AnTuTu
     scores, or catalog anomalies like 999,999 mAh battery). Extreme values
     compress 95% of mainstream smartphones into narrow bands (0.1 - 0.3),
     collapsing recommendation discriminability.

2. RobustScaler (Median & IQR):
   x_scaled = (x - median) / IQR
   - Weakness: Yields unbounded outputs with negative values (e.g. [-2.5, +4.8]).
     Negative feature scores break multi-attribute linear utility baselines
     unless arbitrarily re-centered.

3. QuantileTransformer (Empirical CDF):
   - Weakness: Replaces linear physical spec intervals with rank intervals,
     distorting real proportional hardware advantages (e.g. shrinking the real gap
     between 5,000 mAh and 6,000 mAh).

4. Robust Min-Max (Empirical Percentile Clipping + Min-Max) [CHOSEN STRATEGY]:
   x_clipped = clip(x, P_1, P_99)
   x_scaled = (x_clipped - P_1) / (P_99 - P_1)
   - Evidence & Rationale:
     a) Guaranteed strict [0.0, 1.0] bounds, essential for linear preference scoring.
     b) Complete immunity to extreme catalog outliers without distorting mainstream specs.
     c) Preserves proportional physical differences for 98% of the distribution.
     d) Deterministic, fully serializable via joblib, and strictly reproducible.
"""

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

logger = logging.getLogger(__name__)

# Default canonical feature order for scaling and recommendation
DEFAULT_FEATURE_COLUMNS: list[str] = [
    "processor_score",
    "camera_mp",
    "battery_mah",
    "display_hz",
    "storage_gb",
    "ram_gb",
]


class FeaturePreprocessor(BaseEstimator, TransformerMixin):
    """Fitted feature transformer for numeric smartphone specifications."""

    def __init__(
        self,
        feature_columns: list[str] | None = None,
        strategy: str = "robust_minmax",
        lower_quantile: float = 0.01,
        upper_quantile: float = 0.99,
    ) -> None:
        """Initialize preprocessor with selected feature columns and scaling strategy.

        Args:
            feature_columns: Ordered list of specification columns to scale.
            strategy: Scaling algorithm ('robust_minmax', 'minmax', 'robust').
            lower_quantile: Lower clip percentile for robust_minmax (default 0.01).
            upper_quantile: Upper clip percentile for robust_minmax (default 0.99).
        """
        self.feature_columns = feature_columns or DEFAULT_FEATURE_COLUMNS.copy()
        self.strategy = strategy
        self.lower_quantile = lower_quantile
        self.upper_quantile = upper_quantile

        # Fitted state
        self.is_fitted_ = False
        self.feature_names_in_: list[str] = []
        self.bounds_: dict[
            str, tuple[float, float]
        ] = {}  # {col: (min_or_p1, max_or_p99)}
        self.medians_: dict[str, float] = {}
        self.iqrs_: dict[str, float] = {}

    def fit(
        self, df: pd.DataFrame, y: pd.Series | None = None
    ) -> "FeaturePreprocessor":
        """Compute feature bounds and scaling parameters on catalog data.

        Missing values (NaN) are ignored during quantile and bound estimation
        and are strictly NOT imputed.

        Args:
            df: Input catalog DataFrame.
            y: Ignored (recommender is unsupervised).

        Returns:
            Fitted instance of FeaturePreprocessor.
        """
        self.feature_names_in_ = [
            col for col in self.feature_columns if col in df.columns
        ]
        self.bounds_.clear()
        self.medians_.clear()
        self.iqrs_.clear()

        for col in self.feature_names_in_:
            valid_vals = df[col].dropna().astype(float)
            if valid_vals.empty:
                self.bounds_[col] = (0.0, 1.0)
                self.medians_[col] = 0.0
                self.iqrs_[col] = 1.0
                continue

            if self.strategy == "robust_minmax":
                p_low = float(valid_vals.quantile(self.lower_quantile))
                p_high = float(valid_vals.quantile(self.upper_quantile))
                # Prevent division by zero if all values in column are identical
                if p_high <= p_low:
                    p_low = float(valid_vals.min())
                    p_high = float(valid_vals.max())
                if p_high <= p_low:
                    p_high = p_low + 1.0
                self.bounds_[col] = (p_low, p_high)

            elif self.strategy == "minmax":
                v_min = float(valid_vals.min())
                v_max = float(valid_vals.max())
                if v_max <= v_min:
                    v_max = v_min + 1.0
                self.bounds_[col] = (v_min, v_max)

            elif self.strategy == "robust":
                med = float(valid_vals.median())
                q75 = float(valid_vals.quantile(0.75))
                q25 = float(valid_vals.quantile(0.25))
                iqr = q75 - q25
                if iqr <= 0:
                    iqr = 1.0
                self.medians_[col] = med
                self.iqrs_[col] = iqr

        self.is_fitted_ = True
        logger.info(
            f"Fitted FeaturePreprocessor using '{self.strategy}' on {len(self.feature_names_in_)} features."
        )
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform catalog specifications into normalized scores [0.0, 1.0].

        CRITICAL HONESTY RULE:
        Missing values (NaN) remain strictly NaN in the output DataFrame.
        They are NOT filled with 0.0 or column means.

        Args:
            df: DataFrame containing raw feature columns.

        Returns:
            DataFrame with normalized features in [0.0, 1.0] (or NaN where missing).
        """
        if not self.is_fitted_:
            raise RuntimeError(
                "FeaturePreprocessor must be fitted before calling transform()."
            )

        scaled_dict: dict[str, Any] = {}

        for col in self.feature_names_in_:
            if col not in df.columns:
                scaled_dict[col] = pd.Series(np.nan, index=df.index)
                continue

            series = pd.to_numeric(df[col], errors="coerce")

            if self.strategy in ("robust_minmax", "minmax"):
                low, high = self.bounds_[col]
                # Clip bounds for robust_minmax
                if self.strategy == "robust_minmax":
                    clipped = series.clip(lower=low, upper=high)
                else:
                    clipped = series
                # Min-max scale to [0, 1]
                scaled = (clipped - low) / (high - low)
                # Ensure strictly in [0, 1] for valid entries
                scaled = scaled.clip(lower=0.0, upper=1.0)
                scaled_dict[col] = scaled

            elif self.strategy == "robust":
                med = self.medians_[col]
                iqr = self.iqrs_[col]
                scaled_dict[col] = (series - med) / iqr

        return pd.DataFrame(scaled_dict, index=df.index)

    def fit_transform(
        self, df: pd.DataFrame, y: pd.Series | None = None
    ) -> pd.DataFrame:
        """Fit preprocessor on DataFrame and return transformed features."""
        return self.fit(df, y).transform(df)

    def get_feature_availability(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return boolean DataFrame indicating feature presence (True) vs missing (False)."""
        if not self.is_fitted_:
            raise RuntimeError(
                "Preprocessor must be fitted before checking feature availability."
            )
        availability = {}
        for col in self.feature_names_in_:
            if col in df.columns:
                availability[col] = df[col].notna()
            else:
                availability[col] = pd.Series(False, index=df.index)
        return pd.DataFrame(availability, index=df.index)

    def save(self, filepath: Path | str) -> None:
        """Persist fitted preprocessor instance and configuration using joblib.

        Args:
            filepath: Target file path (e.g., 'data/preprocessor.joblib').
        """
        if not self.is_fitted_:
            raise RuntimeError("Cannot save an unfitted FeaturePreprocessor.")
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info(f"Saved fitted FeaturePreprocessor to '{path}'")

    @classmethod
    def load(cls, filepath: Path | str) -> "FeaturePreprocessor":
        """Load a persisted FeaturePreprocessor instance from disk.

        Args:
            filepath: Path to persisted joblib file.

        Returns:
            Fitted FeaturePreprocessor instance.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Preprocessor file not found at '{path}'")
        instance = joblib.load(path)
        if not isinstance(instance, cls):
            raise TypeError(
                f"Loaded object is of type {type(instance)}, expected {cls}."
            )
        return instance
