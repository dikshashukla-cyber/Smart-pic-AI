"""Data loader and validation module for SmartPick AI.

Implements rigorous schema enforcement, exact missing-column reporting,
duplicate and variant detection (flagging variants rather than deleting them),
implausible-value auditing, row-level validation reports, and metadata tracking.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.exceptions import (
    DatasetNotFoundError,
    EmptyDatasetError,
    MalformedDataError,
    MissingRequiredColumnError,
)

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS: set[str] = {"phone_name", "price_inr"}

OPTIONAL_COLUMNS: set[str] = {
    "brand",
    "ram_gb",
    "storage_gb",
    "battery_mah",
    "camera_mp",
    "display_hz",
    "has_5g",
    "processor_score",
    "source",
    "verified_at",
    "image_path",
    "image_url",
    "image_source",
    "image_license",
    "image_attribution",
}

ALL_CANONICAL_COLUMNS: list[str] = [
    "phone_name",
    "brand",
    "price_inr",
    "ram_gb",
    "storage_gb",
    "battery_mah",
    "camera_mp",
    "display_hz",
    "has_5g",
    "processor_score",
    "source",
    "verified_at",
    "image_path",
    "image_url",
    "image_source",
    "image_license",
    "image_attribution",
]


@dataclass(frozen=True)
class ValidationIssue:
    """Detailed record of a data quality or schema issue detected at row level."""

    row_index: int
    phone_name: str | None
    column: str
    issue_type: (
        str  # MISSING_REQUIRED, IMPLAUSIBLE_VALUE, EXACT_DUPLICATE, VARIANT_DETECTED
    )
    severity: str  # ERROR, WARNING, INFO
    description: str


@dataclass(frozen=True)
class DatasetMetadata:
    """Immutable metadata describing the loaded dataset provenance and quality."""

    total_records: int
    valid_records: int
    missing_fields_summary: dict[str, int]
    source_name: str | None
    last_verified: str | None
    column_names: list[str]
    is_synthetic: bool
    issues: list[ValidationIssue]
    exact_duplicates_count: int
    variants_count: int


def normalize_model_key(brand: str | None, phone_name: str | None) -> str:
    """Normalize brand and model name into a canonical deduplication key.

    Strips punctuation, lowercases, and removes variant spec suffixes like
    '(8GB/128GB)', '5G', 'Pro', etc., to identify the underlying base device.
    """
    b = str(brand or "").strip().lower()
    p = str(phone_name or "").strip().lower()

    # If brand is already in phone name, avoid duplicate brand prefix
    combined = f"{b} {p}".strip() if b and not p.startswith(b) else p

    # Remove variant specifications in parentheses e.g. '(8gb/128gb)'
    cleaned = re.sub(r"\([^)]*\)", "", combined)
    # Remove common trailing suffixes that denote storage/RAM variants
    cleaned = re.sub(r"\b\d+\s*(?:gb|tb)\b", "", cleaned, flags=re.IGNORECASE)
    # Remove extra punctuation and whitespace
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class DataLoader:
    """Loads, validates, audits, and flags smartphone catalog datasets."""

    def __init__(self, filepath: Path | str = "data/phones.csv") -> None:
        """Initialize the DataLoader with a specific dataset file path.

        Args:
            filepath: Path to the smartphone dataset CSV.
        """
        self.filepath = Path(filepath)

    def load_and_validate(self) -> tuple[pd.DataFrame, DatasetMetadata]:
        """Load CSV data and validate schema against the canonical data contract.

        Returns:
            Tuple of (validated DataFrame, DatasetMetadata).

        Raises:
            DatasetNotFoundError: If the dataset file does not exist.
            EmptyDatasetError: If the dataset is empty (0 rows).
            MissingRequiredColumnError: If required canonical columns are missing.
            MalformedDataError: If the CSV file is corrupted.
        """
        if not self.filepath.exists():
            raise DatasetNotFoundError(str(self.filepath))

        try:
            df = pd.read_csv(self.filepath)
        except pd.errors.EmptyDataError as err:
            raise EmptyDatasetError(str(self.filepath)) from err
        except Exception as err:
            raise MalformedDataError(
                f"Failed to read CSV at '{self.filepath}': {err}", err
            ) from err

        if df.empty:
            raise EmptyDatasetError(str(self.filepath))

        # Check required schema columns
        existing_cols = list(df.columns)
        missing_required = sorted(REQUIRED_COLUMNS - set(existing_cols))
        if missing_required:
            raise MissingRequiredColumnError(
                missing_columns=missing_required,
                available_columns=existing_cols,
            )

        # Audit and normalize records
        issues: list[ValidationIssue] = []
        is_synthetic = False

        # Check for synthetic flags in source or filename
        if "synthetic" in str(self.filepath).lower():
            is_synthetic = True
        if "source" in df.columns:
            sources_combined = " ".join(
                df["source"].dropna().astype(str).tolist()
            ).lower()
            if "synthetic" in sources_combined:
                is_synthetic = True

        # Ensure all canonical columns exist in DataFrame (missing optional as NaN)
        for col in ALL_CANONICAL_COLUMNS:
            if col not in df.columns:
                df[col] = np.nan

        # Normalize has_5g to boolean / NaN
        if "has_5g" in df.columns:
            df["has_5g"] = df["has_5g"].map(
                lambda v: (
                    True
                    if v in (True, 1, "1", "True", "true", "Yes", "yes")
                    else (
                        False
                        if v in (False, 0, "0", "False", "false", "No", "no")
                        else None
                    )
                )
            )

        # Row-level audits: required values, implausible values
        valid_indices: list[int] = []

        for idx, row in df.iterrows():
            name = row.get("phone_name")
            price = row.get("price_inr")
            row_has_fatal_error = False

            # Required field 1: phone_name
            if pd.isna(name) or not str(name).strip():
                issues.append(
                    ValidationIssue(
                        row_index=idx,
                        phone_name=None,
                        column="phone_name",
                        issue_type="MISSING_REQUIRED",
                        severity="ERROR",
                        description="Missing required phone_name (empty or NaN). Row cannot be recommended.",
                    )
                )
                row_has_fatal_error = True

            # Required field 2: price_inr
            if pd.isna(price):
                issues.append(
                    ValidationIssue(
                        row_index=idx,
                        phone_name=str(name) if pd.notna(name) else None,
                        column="price_inr",
                        issue_type="MISSING_REQUIRED",
                        severity="ERROR",
                        description="Missing required price_inr (NaN). Row cannot be recommended.",
                    )
                )
                row_has_fatal_error = True
            elif not isinstance(price, (int, float)) or price <= 0:
                issues.append(
                    ValidationIssue(
                        row_index=idx,
                        phone_name=str(name) if pd.notna(name) else None,
                        column="price_inr",
                        issue_type="IMPLAUSIBLE_VALUE",
                        severity="ERROR",
                        description=f"Implausible price_inr: {price}. Price must be strictly positive.",
                    )
                )
                row_has_fatal_error = True

            # Optional field audits: Implausible values (warnings, not fatal)
            ram = row.get("ram_gb")
            if pd.notna(ram) and (ram < 1.0 or ram > 64.0):
                issues.append(
                    ValidationIssue(
                        row_index=idx,
                        phone_name=str(name),
                        column="ram_gb",
                        issue_type="IMPLAUSIBLE_VALUE",
                        severity="WARNING",
                        description=f"Implausible ram_gb: {ram} GB (expected 1 to 64 GB).",
                    )
                )

            batt = row.get("battery_mah")
            if pd.notna(batt) and (batt < 500.0 or batt > 25000.0):
                issues.append(
                    ValidationIssue(
                        row_index=idx,
                        phone_name=str(name),
                        column="battery_mah",
                        issue_type="IMPLAUSIBLE_VALUE",
                        severity="WARNING",
                        description=f"Implausible battery_mah: {batt} mAh (expected 500 to 25,000 mAh).",
                    )
                )

            disp = row.get("display_hz")
            if pd.notna(disp) and (disp < 30.0 or disp > 360.0):
                issues.append(
                    ValidationIssue(
                        row_index=idx,
                        phone_name=str(name),
                        column="display_hz",
                        issue_type="IMPLAUSIBLE_VALUE",
                        severity="WARNING",
                        description=f"Implausible display_hz: {disp} Hz (expected 30 to 360 Hz).",
                    )
                )

            storage = row.get("storage_gb")
            if pd.notna(storage) and (storage < 8.0 or storage > 4096.0):
                issues.append(
                    ValidationIssue(
                        row_index=idx,
                        phone_name=str(name),
                        column="storage_gb",
                        issue_type="IMPLAUSIBLE_VALUE",
                        severity="WARNING",
                        description=f"Implausible storage_gb: {storage} GB (expected 8 to 4,096 GB).",
                    )
                )

            # Optional image validation: verify local file existence if image_path is specified
            img_path = row.get("image_path")
            if pd.notna(img_path) and str(img_path).strip():
                p = Path(str(img_path))
                if not p.exists():
                    issues.append(
                        ValidationIssue(
                            row_index=idx,
                            phone_name=str(name),
                            column="image_path",
                            issue_type="IMAGE_FILE_NOT_FOUND",
                            severity="WARNING",
                            description=f"Local image file '{img_path}' not found on disk. Falling back to SVG silhouette placeholder.",
                        )
                    )

            if not row_has_fatal_error:
                valid_indices.append(idx)

        # Duplicate & Variant Detection
        # 1. Exact duplicates: identical phone_name, brand, price_inr
        exact_dups_mask = df.duplicated(
            subset=["phone_name", "brand", "price_inr"], keep="first"
        )
        exact_dups_count = int(exact_dups_mask.sum())
        for dup_idx in df[exact_dups_mask].index:
            row = df.loc[dup_idx]
            issues.append(
                ValidationIssue(
                    row_index=dup_idx,
                    phone_name=str(row["phone_name"]),
                    column="phone_name",
                    issue_type="EXACT_DUPLICATE",
                    severity="WARNING",
                    description=f"Exact duplicate record found for '{row['phone_name']}' ({row['brand']}).",
                )
            )

        # 2. Variant detection: same normalized base model key, but different RAM/storage/price
        df["_model_key"] = [
            normalize_model_key(r.brand, r.phone_name) for _, r in df.iterrows()
        ]
        model_key_groups = df.groupby("_model_key")
        variants_count = 0

        for key, group in model_key_groups:
            if len(group) > 1 and key:
                # If they have different RAM, storage, or price, they are genuine hardware variants
                unique_specs = group[
                    ["ram_gb", "storage_gb", "price_inr"]
                ].drop_duplicates()
                if len(unique_specs) > 1:
                    variants_count += len(group)
                    for v_idx in group.index:
                        issues.append(
                            ValidationIssue(
                                row_index=v_idx,
                                phone_name=str(df.loc[v_idx, "phone_name"]),
                                column="phone_name",
                                issue_type="VARIANT_DETECTED",
                                severity="INFO",
                                description=(
                                    f"Hardware variant of base model '{key}' "
                                    f"({df.loc[v_idx, 'ram_gb']}GB RAM / {df.loc[v_idx, 'storage_gb']}GB ROM, ₹{df.loc[v_idx, 'price_inr']}). "
                                    "Retained as distinct recommendable option."
                                ),
                            )
                        )

        # Drop temporary audit column
        df.drop(columns=["_model_key"], inplace=True)

        # Missing fields summary
        missing_summary: dict[str, int] = {}
        for col in ALL_CANONICAL_COLUMNS:
            missing_summary[col] = int(df[col].isna().sum())

        source_val = (
            df["source"].dropna().iloc[0] if not df["source"].dropna().empty else None
        )
        verified_val = (
            df["verified_at"].dropna().iloc[0]
            if not df["verified_at"].dropna().empty
            else None
        )

        metadata = DatasetMetadata(
            total_records=len(df),
            valid_records=len(valid_indices),
            missing_fields_summary=missing_summary,
            source_name=str(source_val) if source_val else None,
            last_verified=str(verified_val) if verified_val else None,
            column_names=list(df.columns),
            is_synthetic=is_synthetic,
            issues=issues,
            exact_duplicates_count=exact_dups_count,
            variants_count=variants_count,
        )

        logger.info(
            f"Loaded dataset: {metadata.total_records} total, {metadata.valid_records} valid. "
            f"Synthetic: {metadata.is_synthetic}. Issues flagged: {len(issues)}."
        )

        return df, metadata
