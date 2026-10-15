"""Test suite for data quality report generator and metrics calculation."""

from pathlib import Path

import pandas as pd
import pytest

from src.data_loader import DataLoader
from src.quality_report import QualityReportGenerator, QualitySummary, generate_report


@pytest.fixture
def catalog_setup() -> tuple[pd.DataFrame, object]:
    """Fixture returning validated DataFrame and metadata from phones.csv."""
    loader = DataLoader("data/phones.csv")
    df, meta = loader.load_and_validate()
    return df, meta


def test_quality_summary_metrics(catalog_setup: tuple[pd.DataFrame, object]) -> None:
    """Verify QualityReportGenerator computes correct summary statistics."""
    df, meta = catalog_setup
    generator = QualityReportGenerator(df, meta)
    summary = generator.get_summary()

    assert isinstance(summary, QualitySummary)
    assert summary.total_records >= 100
    assert summary.valid_records > 0
    assert summary.overall_completeness_pct > 90.0
    assert summary.brand_count >= 10
    assert summary.price_min > 0.0
    assert summary.price_max > summary.price_min
    assert summary.is_synthetic is True


def test_markdown_report_generation(
    catalog_setup: tuple[pd.DataFrame, object], tmp_path: Path
) -> None:
    """Verify markdown quality report generation and structure."""
    df, meta = catalog_setup
    generator = QualityReportGenerator(df, meta)
    out_file = tmp_path / "test_report.md"
    content = generator.generate_markdown_report(out_file)

    assert out_file.exists()
    assert "# SmartPick AI — Catalog Data Quality & Health Audit" in content
    assert "Price Band Distribution" in content
    assert "Brand Distribution" in content
    assert "Column Completeness" in content


def test_generate_report_convenience_function(tmp_path: Path) -> None:
    """Verify generate_report standalone function."""
    out_file = tmp_path / "direct_report.md"
    content = generate_report("data/phones.csv", out_file)
    assert out_file.exists()
    assert len(content) > 500
