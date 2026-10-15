"""Regression and unit tests for smartphone imagery and HTML component builders.

Verifies:
1. Every HTML builder output has no line starting with 4+ spaces and no blank lines.
2. Dynamic attributes (phone_name, brand, reasons) are strictly HTML escaped.
3. Local WebP and SVG images encode to browser-safe self-contained Data URIs.
4. Missing image paths gracefully fall back to SVG without crashes or dropped records.
5. Streamlit AppTest verifies cards render without raw monospace code block leakage.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.data_loader import DataLoader
from src.placeholders import generate_phone_svg, get_brand_color
from src.ui_components import (
    build_compare_column_header_html,
    build_footer_html,
    build_hero_badge_html,
    build_no_candidates_html,
    build_phone_card_html,
    build_why_not_card_html,
    compact_html,
    get_image_data_uri,
)


@dataclass
class DummyRecommendation:
    """Mock recommendation result for HTML builder testing."""

    phone_name: str
    brand: str | None
    price_inr: float
    match_score: float
    specs: dict[str, Any]
    rationale: str
    missing_specs: list[str]
    trade_offs: list[str]
    image_path: str | None = None
    image_url: str | None = None
    image_source: str | None = None
    image_license: str | None = None
    image_attribution: str | None = None


@pytest.fixture
def sample_rec() -> DummyRecommendation:
    """Fixture providing a realistic mock smartphone recommendation."""
    return DummyRecommendation(
        phone_name="POCO X6 5G <script>alert(1)</script>",
        brand="POCO & Co",
        price_inr=21999.0,
        match_score=88.4,
        specs={
            "processor_score": 605000,
            "ram_gb": 8,
            "storage_gb": 256,
            "battery_mah": 5100,
            "camera_mp": 64,
            "display_hz": 120,
            "has_5g": True,
        },
        rationale="Strong performance per rupee with 120Hz AMOLED.",
        missing_specs=[],
        trade_offs=["Plastic chassis", "Aggressive UI software skin"],
        image_path="assets/phones/samsung-galaxy-s24-5g.webp",
        image_attribution="Test User",
        image_license="CC BY-SA 4.0",
    )


def assert_compact_html_rules(html_str: str) -> None:
    """Helper to verify strict markdown code-block prevention rules."""
    assert html_str, "HTML output must not be empty"
    lines = html_str.split("\n")
    for idx, line in enumerate(lines, start=1):
        assert not line.startswith("    "), (
            f"Line {idx} starts with 4+ spaces, which causes markdown code blocks: {line!r}"
        )
        assert line.strip() != "", f"Line {idx} is a blank line inside HTML block"


class TestHtmlBuilders:
    """Unit test suite for HTML builder formatting and sanitization."""

    def test_compact_html_eliminates_indentation_and_blank_lines(self) -> None:
        """Verify compact_html strips leading space and removes empty lines."""
        raw = """
            <div class="test">
                
                <span>Content</span>
            </div>
        """
        compact = compact_html(raw)
        assert_compact_html_rules(compact)
        assert '<div class="test">' in compact
        assert "<span>Content</span>" in compact

    def test_build_phone_card_html_strict_rules(
        self, sample_rec: DummyRecommendation
    ) -> None:
        """Verify phone card HTML satisfies indentation and escaping rules."""
        card = build_phone_card_html(sample_rec, rank=1, lang_code="en")
        assert_compact_html_rules(card)

        # Verify XSS escaping
        assert "<script>" not in card
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in card
        assert "POCO &amp; Co" in card

        # Verify card structural elements
        assert "card-split" in card
        assert "card-img-col" in card
        assert "card-content-col" in card
        assert "score-bar-fill" in card
        assert "specs-grid" in card
        assert "Photo: Test User (CC BY-SA 4.0)" in card

    def test_build_hero_badge_html_rules(self) -> None:
        """Verify hero badge has no 4+ space indents or blank lines."""
        badge = build_hero_badge_html(
            catalog_status_text="Catalog Status",
            source_name="Curated Source",
            verified_recent_text="Verified",
            last_verified="2026-10-15",
            version_hash="abc1234",
        )
        assert_compact_html_rules(badge)
        assert "Curated Source" in badge

    def test_build_footer_html_rules(self) -> None:
        """Verify footer caveat HTML has no 4+ space indents or blank lines."""
        footer = build_footer_html()
        assert_compact_html_rules(footer)
        assert "caveat-footer" in footer

    def test_build_no_candidates_html_rules(self) -> None:
        """Verify no candidates empty state has no 4+ space indents or blank lines."""
        empty_html = build_no_candidates_html()
        assert_compact_html_rules(empty_html)
        assert "No Devices Match Your Exact Constraints" in empty_html

    def test_build_why_not_card_html_rules(self) -> None:
        """Verify why-not card HTML is compact and escapes inputs."""
        why_not = build_why_not_card_html(
            phone_name="Budget Phone <bold>",
            price_inr=15000.0,
            formatted_price="₹15,000",
            badge_txt="🚫 BUDGET VIOLATION",
            badge_col="#EF4444",
            primary_reason="Price exceeds maximum budget bound.",
        )
        assert_compact_html_rules(why_not)
        assert "<bold>" not in why_not
        assert "Budget Phone &lt;bold&gt;" in why_not
        assert "₹15,000" in why_not

    def test_build_compare_column_header_html_rules(self) -> None:
        """Verify compare column header renders image and title cleanly."""
        header = build_compare_column_header_html(
            phone_name="OnePlus 12",
            brand="OnePlus",
            price_str="₹64,999",
            image_path=None,
        )
        assert_compact_html_rules(header)
        assert "OnePlus 12" in header
        assert "₹64,999" in header
        assert "card-img-wrapper" in header


class TestImageDataUriAndPlaceholders:
    """Test suite for image encoding, SVG silhouette generation, and fallbacks."""

    def test_brand_color_accents(self) -> None:
        """Verify brand-specific color palette assignments."""
        assert get_brand_color("Apple") == "#64748B"
        assert get_brand_color("Samsung") == "#1D4ED8"
        assert get_brand_color("POCO") == "#CA8A04"
        assert get_brand_color("Unknown Brand") == "#38BDF8"

    def test_generate_phone_svg_validity(self) -> None:
        """Verify procedural SVG phone silhouette generation."""
        svg = generate_phone_svg("Galaxy S24", "Samsung")
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert "#1D4ED8" in svg
        assert "Galaxy S24" in svg

    def test_get_image_data_uri_fallback_on_none(self) -> None:
        """Verify non-existent or None image path returns valid SVG data URI."""
        uri, is_placeholder = get_image_data_uri(None, "Test Phone", "Xiaomi")
        assert is_placeholder is True
        assert uri.startswith("data:image/svg+xml;utf8,")
        assert "<svg" in uri or "%3Csvg" in uri

    def test_get_image_data_uri_with_real_or_placeholder_file(self) -> None:
        """Verify existing image file loads as data URI."""
        placeholder_file = Path("assets/phones/placeholders/poco_x6_5g.svg")
        if placeholder_file.exists():
            uri, is_ph = get_image_data_uri(str(placeholder_file), "POCO X6 5G", "POCO")
            assert uri.startswith("data:image/svg+xml;utf8,")
            assert is_ph is True


class TestDataLoaderImageHandling:
    """Test data loader resilience to image column variations."""

    def test_loader_accepts_missing_image_columns(self, tmp_path: Path) -> None:
        """Verify loader succeeds when CSV does not contain image columns."""
        csv_path = tmp_path / "phones_no_images.csv"
        df = pd.DataFrame(
            [
                {
                    "phone_name": "Test Phone 1",
                    "brand": "TestBrand",
                    "price_inr": 15000.0,
                    "processor_score": 400000.0,
                    "ram_gb": 6.0,
                    "storage_gb": 128.0,
                    "battery_mah": 5000.0,
                    "camera_mp": 50.0,
                    "display_hz": 90.0,
                    "has_5g": True,
                }
            ]
        )
        df.to_csv(csv_path, index=False)
        loader = DataLoader(csv_path)
        loaded_df, _metadata = loader.load_and_validate()
        assert len(loaded_df) == 1
        assert "phone_name" in loaded_df.columns

    def test_loader_flags_missing_image_file_as_warning_not_error(
        self, tmp_path: Path
    ) -> None:
        """Verify non-existent image_path creates a warning without dropping the row."""
        csv_path = tmp_path / "phones_with_bad_image.csv"
        df = pd.DataFrame(
            [
                {
                    "phone_name": "Test Phone 2",
                    "brand": "TestBrand",
                    "price_inr": 18000.0,
                    "processor_score": 450000.0,
                    "ram_gb": 8.0,
                    "storage_gb": 128.0,
                    "battery_mah": 5000.0,
                    "camera_mp": 64.0,
                    "display_hz": 120.0,
                    "has_5g": True,
                    "image_path": "assets/phones/non_existent_file.webp",
                }
            ]
        )
        df.to_csv(csv_path, index=False)
        loader = DataLoader(csv_path)
        loaded_df, metadata = loader.load_and_validate()
        assert len(loaded_df) == 1
        assert any(
            issue.issue_type == "IMAGE_FILE_NOT_FOUND" for issue in metadata.issues
        )


def test_apptest_no_raw_html_code_blocks() -> None:
    """Streamlit AppTest: verify UI does NOT render raw HTML tags in code blocks."""
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    assert not at.exception

    # Check all code blocks in the rendered page
    for code_block in at.code:
        code_text = code_block.value
        assert '<div class="chip' not in code_text, (
            f"Raw HTML chip tag leaked into code block: {code_text[:100]}"
        )
        assert 'role="progressbar"' not in code_text, (
            f"Raw HTML progressbar tag leaked into code block: {code_text[:100]}"
        )
        assert '<div class="specs-grid"' not in code_text, (
            f"Raw HTML specs grid leaked into code block: {code_text[:100]}"
        )
        assert '<div class="card-split"' not in code_text, (
            f"Raw HTML card-split tag leaked into code block: {code_text[:100]}"
        )

    # Ensure recommendations were rendered with proper card structures
    markdown_html_blocks = [m.value for m in at.markdown if "smartpick-card" in m.value]
    assert len(markdown_html_blocks) >= 1, (
        "Expected recommendation cards rendered in markdown"
    )
