"""Test suite for SmartPick AI data ingestion and string parsers.

Verifies messy string normalization for prices, RAM, storage, battery, camera,
refresh rates, 5G flags, and benchmark scores, ensuring missing values strictly
remain NaN.
"""

from pathlib import Path

import numpy as np
import pytest

from src.ingest import (
    parse_battery,
    parse_camera,
    parse_display_hz,
    parse_has_5g,
    parse_price,
    parse_processor_score,
    parse_ram,
    parse_storage,
)


class TestPriceParser:
    """Tests for messy price string parsing and currency normalization."""

    @pytest.mark.parametrize(
        ("raw_input", "expected"),
        [
            ("₹24,999", 24999.0),
            ("Rs. 18,499.00", 18499.0),
            ("₹ 1,19,999", 119999.0),
            ("14999", 14999.0),
            ("Rs 9999", 9999.0),
            (29999, 29999.0),
            (29999.50, 29999.50),
        ],
    )
    def test_valid_price_parsing(self, raw_input: object, expected: float) -> None:
        """Verify valid currency strings parse to expected float."""
        result = parse_price(raw_input)
        assert result == pytest.approx(expected, 0.01)

    @pytest.mark.parametrize(
        "invalid_input", ["FREE", "N/A", "TBD", "-", "", None, np.nan, "free_unit"]
    )
    def test_invalid_price_returns_nan(self, invalid_input: object) -> None:
        """Verify unparseable and missing prices return NaN without raising exceptions."""
        result = parse_price(invalid_input)
        assert np.isnan(result)


class TestRamParser:
    """Tests for RAM capacity string parsing."""

    @pytest.mark.parametrize(
        ("raw_input", "expected"),
        [
            ("8 GB", 8.0),
            ("12GB RAM", 12.0),
            ("4GB", 4.0),
            ("16 GB (8GB + 8GB Virtual)", 16.0),
            ("6", 6.0),
            (8, 8.0),
            ("4096 MB", 4.0),
        ],
    )
    def test_valid_ram_parsing(self, raw_input: object, expected: float) -> None:
        """Verify RAM capacity strings convert to numeric GB."""
        result = parse_ram(raw_input)
        assert result == pytest.approx(expected, 0.1)

    @pytest.mark.parametrize("invalid_input", ["", "N/A", "-", None, np.nan])
    def test_missing_ram_returns_nan(self, invalid_input: object) -> None:
        """Verify missing RAM returns NaN (never 0)."""
        result = parse_ram(invalid_input)
        assert np.isnan(result)


class TestStorageParser:
    """Tests for storage capacity string parsing and TB-to-GB conversion."""

    @pytest.mark.parametrize(
        ("raw_input", "expected"),
        [
            ("128 GB", 128.0),
            ("256GB ROM", 256.0),
            ("512 GB", 512.0),
            ("1 TB", 1024.0),
            ("2 TB", 2048.0),
            ("64", 64.0),
        ],
    )
    def test_valid_storage_parsing(self, raw_input: object, expected: float) -> None:
        """Verify storage capacity parses correctly, including 1 TB = 1024 GB."""
        result = parse_storage(raw_input)
        assert result == pytest.approx(expected, 0.1)

    def test_missing_storage_returns_nan(self) -> None:
        """Verify missing storage returns NaN."""
        assert np.isnan(parse_storage(None))
        assert np.isnan(parse_storage(np.nan))


class TestBatteryParser:
    """Tests for battery capacity string parsing."""

    @pytest.mark.parametrize(
        ("raw_input", "expected"),
        [
            ("5000 mAh", 5000.0),
            ("4,500mAh", 4500.0),
            ("6000 mAh Li-Po", 6000.0),
            (5000, 5000.0),
        ],
    )
    def test_valid_battery_parsing(self, raw_input: object, expected: float) -> None:
        """Verify battery capacity parses to numeric mAh."""
        result = parse_battery(raw_input)
        assert result == pytest.approx(expected, 0.1)

    def test_missing_battery_returns_nan(self) -> None:
        """Verify missing battery capacity returns NaN (never 0 mAh)."""
        assert np.isnan(parse_battery(None))
        assert np.isnan(parse_battery(np.nan))


class TestCameraParser:
    """Tests for camera megapixel string parsing."""

    @pytest.mark.parametrize(
        ("raw_input", "expected"),
        [
            ("50 MP", 50.0),
            ("50MP + 8MP + 2MP", 50.0),
            ("108 MP OIS", 108.0),
            ("200 MP Ultra", 200.0),
            ("12 MP Main", 12.0),
        ],
    )
    def test_valid_camera_parsing(self, raw_input: object, expected: float) -> None:
        """Verify camera resolution parses to primary main sensor MP."""
        result = parse_camera(raw_input)
        assert result == pytest.approx(expected, 0.1)

    def test_missing_camera_returns_nan(self) -> None:
        """Verify missing camera returns NaN."""
        assert np.isnan(parse_camera(None))


class TestDisplayHzParser:
    """Tests for display refresh rate string parsing."""

    @pytest.mark.parametrize(
        ("raw_input", "expected"),
        [
            ("120 Hz", 120.0),
            ("120Hz AMOLED", 120.0),
            ("90 Hz", 90.0),
            ("144Hz", 144.0),
            ("60 Hz", 60.0),
        ],
    )
    def test_valid_display_hz_parsing(self, raw_input: object, expected: float) -> None:
        """Verify display refresh rate parses to numeric Hz."""
        result = parse_display_hz(raw_input)
        assert result == pytest.approx(expected, 0.1)

    def test_missing_display_hz_returns_nan(self) -> None:
        """Verify missing refresh rate returns NaN (never 0 Hz)."""
        assert np.isnan(parse_display_hz(None))


class TestHas5GParser:
    """Tests for 5G connectivity boolean normalization."""

    @pytest.mark.parametrize("val", ["Yes", "5G", "True", "1", 1, True, "yes", "Y"])
    def test_truthy_5g(self, val: object) -> None:
        """Verify positive 5G strings normalize to True."""
        assert parse_has_5g(val) is True

    @pytest.mark.parametrize(
        "val", ["No", "4G", "LTE", "False", "0", 0, False, "no", "N"]
    )
    def test_falsy_5g(self, val: object) -> None:
        """Verify non-5G / legacy network strings normalize to False."""
        assert parse_has_5g(val) is False

    @pytest.mark.parametrize("val", [None, np.nan, "Unknown", "N/A", ""])
    def test_unspecified_5g_returns_none(self, val: object) -> None:
        """Verify unspecified 5G connectivity returns None."""
        assert parse_has_5g(val) is None


class TestProcessorScoreParser:
    """Tests for processor benchmark score parsing."""

    @pytest.mark.parametrize(
        ("raw_input", "expected"),
        [
            ("720,000", 720000.0),
            ("Score: 1,450,000 (AnTuTu v10)", 1450000.0),
            ("850000", 850000.0),
            (685000, 685000.0),
        ],
    )
    def test_valid_processor_score_parsing(
        self, raw_input: object, expected: float
    ) -> None:
        """Verify benchmark scores parse to positive numeric values."""
        result = parse_processor_score(raw_input)
        assert result == pytest.approx(expected, 1.0)

    def test_missing_processor_score_returns_nan(self) -> None:
        """Verify missing processor score returns NaN (never 0)."""
        assert np.isnan(parse_processor_score(None))


class TestIngestionPipeline:
    """Tests for IngestionAdapter end-to-end ingestion and markdown logging."""

    def test_ingestion_adapter_full_flow(self, tmp_path: Path) -> None:
        """Verify IngestionAdapter reads raw, writes canonical, and logs markdown."""
        from src.generate_sample import generate_synthetic_raw_dataset
        from src.ingest import IngestionAdapter

        raw_csv = tmp_path / "raw.csv"
        out_csv = tmp_path / "clean.csv"
        log_md = tmp_path / "transformations.md"

        generate_synthetic_raw_dataset(raw_csv)
        assert raw_csv.exists()

        adapter = IngestionAdapter(raw_csv, out_csv)
        df, stats = adapter.ingest()

        assert out_csv.exists()
        assert len(df) == stats.total_rows
        assert "phone_name" in df.columns
        assert "price_inr" in df.columns

        content = adapter.generate_transformations_markdown(log_md)
        assert log_md.exists()
        assert "# SmartPick AI — Data Ingestion & Transformation Log" in content

    def test_ingestion_adapter_missing_file_error(self, tmp_path: Path) -> None:
        """Verify IngestionAdapter raises FileNotFoundError if input does not exist."""
        from src.ingest import IngestionAdapter

        adapter = IngestionAdapter(
            tmp_path / "non_existent.csv", tmp_path / "clean.csv"
        )
        with pytest.raises(FileNotFoundError):
            adapter.ingest()
