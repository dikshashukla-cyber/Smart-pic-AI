"""Test suite for DataLoader, schema validation, and data quality audits.

Validates:
- TC-01: Valid dataset loads required columns and valid records.
- TC-02: Missing required column throws MissingRequiredColumnError with exact names.
- TC-08: Empty dataset throws EmptyDatasetError.
- Exact duplicates detection.
- Hardware variant detection (retained, not deleted).
- Implausible values flagging (negative prices, absurd battery).
- Custom exceptions on non-existent files.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.data_loader import DataLoader, normalize_model_key
from src.exceptions import (
    DatasetNotFoundError,
    EmptyDatasetError,
    MissingRequiredColumnError,
)


class TestDataLoaderCore:
    """Core functional and validation tests for DataLoader."""

    def test_tc01_load_valid_canonical_dataset(self) -> None:
        """TC-01: Verify canonical phones.csv loads successfully with valid metadata."""
        dataset_path = Path("data/phones.csv")
        assert dataset_path.exists(), "data/phones.csv must exist before running TC-01."

        loader = DataLoader(dataset_path)
        df, metadata = loader.load_and_validate()

        assert not df.empty, "DataFrame should not be empty."
        assert "phone_name" in df.columns
        assert "price_inr" in df.columns
        assert metadata.total_records >= 100, "Dataset should have 100+ records."
        assert metadata.valid_records > 0, (
            "There should be valid recommendable records."
        )
        assert metadata.is_synthetic is True, (
            "Synthetic catalog should be flagged as synthetic."
        )

    def test_tc02_missing_required_column_exact_reporting(self, tmp_path: Path) -> None:
        """TC-02: Verify missing required column raises MissingRequiredColumnError with exact names."""
        bad_csv = tmp_path / "missing_price.csv"
        # CSV with phone_name and ram_gb, but missing required price_inr
        bad_df = pd.DataFrame({"phone_name": ["Phone A", "Phone B"], "ram_gb": [8, 12]})
        bad_df.to_csv(bad_csv, index=False)

        loader = DataLoader(bad_csv)
        with pytest.raises(MissingRequiredColumnError) as exc_info:
            loader.load_and_validate()

        err = exc_info.value
        assert "price_inr" in err.missing_columns
        assert "phone_name" in err.available_columns
        assert "MissingRequiredColumnError" in type(err).__name__

    def test_tc08_empty_dataset_error(self, tmp_path: Path) -> None:
        """TC-08: Verify loading an empty CSV file raises EmptyDatasetError."""
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("", encoding="utf-8")

        loader = DataLoader(empty_csv)
        with pytest.raises(EmptyDatasetError):
            loader.load_and_validate()

    def test_tc08_headers_only_dataset_error(self, tmp_path: Path) -> None:
        """TC-08: Verify loading a CSV with headers only (0 data rows) raises EmptyDatasetError."""
        headers_csv = tmp_path / "headers_only.csv"
        headers_csv.write_text("phone_name,price_inr,brand\n", encoding="utf-8")

        loader = DataLoader(headers_csv)
        with pytest.raises(EmptyDatasetError):
            loader.load_and_validate()

    def test_nonexistent_dataset_error(self) -> None:
        """Verify non-existent dataset path raises DatasetNotFoundError."""
        loader = DataLoader("data/non_existent_path_xyz.csv")
        with pytest.raises(DatasetNotFoundError) as exc_info:
            loader.load_and_validate()
        assert "non_existent_path_xyz.csv" in str(exc_info.value)

    def test_malformed_csv_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify corrupted CSV raises MalformedDataError."""
        from src.exceptions import MalformedDataError

        corrupt_csv = tmp_path / "corrupt.csv"
        corrupt_csv.write_text("some,data\n1,2", encoding="utf-8")

        def mock_read_csv(*args: object, **kwargs: object) -> None:
            raise pd.errors.ParserError("Simulated corrupt CSV parse failure")

        monkeypatch.setattr(pd, "read_csv", mock_read_csv)
        loader = DataLoader(corrupt_csv)
        with pytest.raises(MalformedDataError) as exc_info:
            loader.load_and_validate()
        assert "Failed to read CSV" in str(exc_info.value)


class TestDataQualityAndAuditing:
    """Tests for duplicate detection, variant auditing, and implausible values."""

    def test_exact_duplicate_detection(self) -> None:
        """Verify exact duplicates in catalog are flagged with EXACT_DUPLICATE."""
        loader = DataLoader("data/phones.csv")
        _, metadata = loader.load_and_validate()

        assert metadata.exact_duplicates_count > 0
        exact_dup_issues = [
            i for i in metadata.issues if i.issue_type == "EXACT_DUPLICATE"
        ]
        assert len(exact_dup_issues) == metadata.exact_duplicates_count

    def test_hardware_variants_flagged_not_deleted(self) -> None:
        """Verify hardware variants are identified with VARIANT_DETECTED and retained."""
        loader = DataLoader("data/phones.csv")
        df, metadata = loader.load_and_validate()

        variant_issues = [
            i for i in metadata.issues if i.issue_type == "VARIANT_DETECTED"
        ]
        assert len(variant_issues) > 0, (
            "Hardware variants should be audited and logged."
        )

        # Verify OnePlus 12R variants are both present in the DataFrame
        oneplus_12r = df[df["phone_name"].str.contains("OnePlus 12R", na=False)]
        assert len(oneplus_12r) >= 2, (
            "Variants must be retained in DataFrame, not deleted."
        )

    def test_implausible_values_flagged(self) -> None:
        """Verify negative price and implausible battery mAh are flagged."""
        loader = DataLoader("data/phones.csv")
        _, metadata = loader.load_and_validate()

        implausible_issues = [
            i for i in metadata.issues if i.issue_type == "IMPLAUSIBLE_VALUE"
        ]
        assert len(implausible_issues) >= 2

        # Check negative price issue
        price_issues = [i for i in implausible_issues if i.column == "price_inr"]
        assert any(
            "negative" in i.description.lower() or "price" in i.description.lower()
            for i in price_issues
        )

        # Check absurd battery issue
        batt_issues = [i for i in implausible_issues if i.column == "battery_mah"]
        assert any("999999" in i.description for i in batt_issues)

    def test_missing_required_phone_name_flagged(self) -> None:
        """Verify records with null phone_name are flagged as fatal errors and excluded from valid count."""
        loader = DataLoader("data/phones.csv")
        _, metadata = loader.load_and_validate()

        missing_name_issues = [
            i
            for i in metadata.issues
            if i.column == "phone_name" and i.issue_type == "MISSING_REQUIRED"
        ]
        assert len(missing_name_issues) >= 1
        assert metadata.valid_records < metadata.total_records


class TestModelKeyNormalization:
    """Tests for model key normalization in duplicate detection."""

    def test_normalize_model_key_removes_specs(self) -> None:
        """Verify storage/RAM strings in parentheses are cleaned for base key."""
        key1 = normalize_model_key("OnePlus", "OnePlus 12R (8GB/128GB)")
        key2 = normalize_model_key("OnePlus", "OnePlus 12R (16GB/256GB)")
        assert key1 == key2
        assert "128gb" not in key1
