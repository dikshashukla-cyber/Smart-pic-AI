"""Data quality report generator for SmartPick AI.

Calculates completeness per column, statistical outliers, duplicate and variant
counts, price band coverage, and brand distribution. Emits data/QUALITY_REPORT.md
and exposes structured metrics for UI rendering.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.data_loader import DataLoader, DatasetMetadata


@dataclass(frozen=True)
class QualitySummary:
    """Compact structured summary of data quality for UI rendering."""

    total_records: int
    valid_records: int
    overall_completeness_pct: float
    brand_count: int
    price_min: float
    price_max: float
    price_median: float
    exact_duplicates: int
    hardware_variants: int
    implausible_values: int
    is_synthetic: bool


class QualityReportGenerator:
    """Generates exhaustive audit reports and metrics on catalog data."""

    def __init__(self, df: pd.DataFrame, metadata: DatasetMetadata) -> None:
        self.df = df
        self.metadata = metadata

    def get_summary(self) -> QualitySummary:
        """Extract high-level quality metrics for application dashboard."""
        valid_prices = self.df["price_inr"].dropna()
        valid_prices = valid_prices[valid_prices > 0]

        total_cells = len(self.df) * len(self.df.columns)
        non_null_cells = int(self.df.notna().sum().sum())
        completeness = (
            round((non_null_cells / total_cells) * 100, 1) if total_cells > 0 else 0.0
        )

        implausible = sum(
            1
            for issue in self.metadata.issues
            if issue.issue_type == "IMPLAUSIBLE_VALUE"
        )

        return QualitySummary(
            total_records=self.metadata.total_records,
            valid_records=self.metadata.valid_records,
            overall_completeness_pct=completeness,
            brand_count=int(self.df["brand"].dropna().nunique()),
            price_min=float(valid_prices.min()) if not valid_prices.empty else 0.0,
            price_max=float(valid_prices.max()) if not valid_prices.empty else 0.0,
            price_median=float(valid_prices.median())
            if not valid_prices.empty
            else 0.0,
            exact_duplicates=self.metadata.exact_duplicates_count,
            hardware_variants=self.metadata.variants_count,
            implausible_values=implausible,
            is_synthetic=self.metadata.is_synthetic,
        )

    def generate_markdown_report(
        self, output_path: Path | str = "data/QUALITY_REPORT.md"
    ) -> str:
        """Generate comprehensive markdown report detailing data health."""
        summary = self.get_summary()
        out = Path(output_path)

        lines = [
            "# SmartPick AI — Catalog Data Quality & Health Audit",
            "",
            "**Audit Date**: 2026-10-15  ",
            f"**Dataset Source**: `{self.metadata.source_name or 'Local Curated Catalog'}`  ",
            f"**Evaluation Status**: `{'SYNTHETIC SAMPLE (Labelled)' if summary.is_synthetic else 'GENUINE CATALOG'}`  ",
            f"**Total Catalog Records**: `{summary.total_records}` (Valid recommendable: `{summary.valid_records}`)  ",
            f"**Overall Completeness**: `{summary.overall_completeness_pct}%`  ",
            "",
            "---",
            "",
            "## 1. Column Completeness & Specification Integrity",
            "",
            "| Canonical Column | Present Count | Missing (NaN) | Completeness | Distinct Values | Notes & Policy |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for col in self.df.columns:
            total = len(self.df)
            missing = int(self.df[col].isna().sum())
            present = total - missing
            pct = round((present / total) * 100, 1)
            distinct = int(self.df[col].nunique(dropna=True))

            policy = (
                "Required (MVP)"
                if col in {"phone_name", "price_inr"}
                else "Optional (NaN preserved)"
            )
            lines.append(
                f"| `{col}` | {present} | {missing} | {pct}% | {distinct} | {policy} |"
            )

        # Price band coverage
        valid_prices = self.df["price_inr"].dropna()
        valid_prices = valid_prices[valid_prices > 0]

        bands = [
            ("Budget (< ₹15,000)", valid_prices < 15000),
            (
                "Mid-Range (₹15,000 - ₹30,000)",
                (valid_prices >= 15000) & (valid_prices < 30000),
            ),
            (
                "Upper Mid-Range (₹30,000 - ₹50,000)",
                (valid_prices >= 30000) & (valid_prices < 50000),
            ),
            (
                "Flagship (₹50,000 - ₹80,000)",
                (valid_prices >= 50000) & (valid_prices < 80000),
            ),
            ("Ultra-Flagship (>= ₹80,000)", valid_prices >= 80000),
        ]

        lines.extend(
            [
                "",
                "## 2. Price Band Distribution & Catalog Coverage",
                "",
                "| Price Segment | Device Count | Share of Catalog | Min Price | Max Price | Median Price |",
                "| :--- | :--- | :--- | :--- | :--- | :--- |",
            ]
        )

        total_valid_prices = len(valid_prices)
        for band_name, mask in bands:
            subset = valid_prices[mask]
            count = len(subset)
            share = (
                round((count / total_valid_prices) * 100, 1)
                if total_valid_prices > 0
                else 0.0
            )
            p_min = f"₹{int(subset.min()):,}" if count > 0 else "N/A"
            p_max = f"₹{int(subset.max()):,}" if count > 0 else "N/A"
            p_med = f"₹{int(subset.median()):,}" if count > 0 else "N/A"
            lines.append(
                f"| {band_name} | {count} | {share}% | {p_min} | {p_max} | {p_med} |"
            )

        # Brand distribution
        lines.extend(
            [
                "",
                "## 3. Brand Distribution & Market Diversity",
                "",
                "| Brand | Models Count | Share of Catalog | Price Range |",
                "| :--- | :--- | :--- | :--- |",
            ]
        )

        brand_counts = self.df["brand"].value_counts(dropna=False)
        for brand, count in brand_counts.items():
            b_name = str(brand) if pd.notna(brand) else "*(Missing / Inferred)*"
            share = round((count / len(self.df)) * 100, 1)
            b_prices = self.df[self.df["brand"] == brand]["price_inr"].dropna()
            b_prices = b_prices[b_prices > 0]
            p_span = (
                f"₹{int(b_prices.min()):,} - ₹{int(b_prices.max()):,}"
                if not b_prices.empty
                else "N/A"
            )
            lines.append(f"| **{b_name}** | {count} | {share}% | {p_span} |")

        # Duplicates and Outliers
        lines.extend(
            [
                "",
                "## 4. Duplicate & Variant Audit",
                "",
                f"- **Exact Duplicate Rows**: `{summary.exact_duplicates}` (Identified for warning, verified in test suite).",
                f"- **Legitimate Hardware Variants**: `{summary.hardware_variants}` records detected with identical base model keys but distinct RAM/storage/price tiers.",
                "- **Deduplication Policy**: Exact duplicates flagged for inspection; hardware variants are preserved as distinct purchase options.",
                "",
                "## 5. Row-Level Validation & Outlier Findings",
                "",
                "| Row Index | Device Name | Column | Issue Type | Severity | Description |",
                "| :--- | :--- | :--- | :--- | :--- | :--- |",
            ]
        )

        for issue in self.metadata.issues[:20]:  # Top 20 issues
            d_name = issue.phone_name or "*(Missing)*"
            lines.append(
                f"| {issue.row_index} | {d_name} | `{issue.column}` | `{issue.issue_type}` | **{issue.severity}** | {issue.description} |"
            )

        if len(self.metadata.issues) > 20:
            lines.append(
                f"| ... | *({len(self.metadata.issues) - 20} additional issues logged in memory)* | | | | |"
            )

        lines.extend(
            [
                "",
                "---",
                "*Report auto-generated by `src/quality_report.py` QualityReportGenerator.*",
            ]
        )

        content = "\n".join(lines)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)
        return content


def generate_report(
    filepath: Path | str = "data/phones.csv",
    output_path: Path | str = "data/QUALITY_REPORT.md",
) -> str:
    """Convenience function to load data and produce data/QUALITY_REPORT.md."""
    loader = DataLoader(filepath)
    df, meta = loader.load_and_validate()
    generator = QualityReportGenerator(df, meta)
    return generator.generate_markdown_report(output_path)


if __name__ == "__main__":
    generate_report()
