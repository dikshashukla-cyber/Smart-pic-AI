"""Pure, compact, XSS-safe HTML component builders for SmartPick AI.

Solves the Streamlit markdown code-block bug by:
1. Guaranteeing zero lines start with 4+ spaces.
2. Eliminating blank lines inside HTML blocks.
3. Escaping all dynamic model attributes with html.escape().
4. Embedding images as self-contained data URIs (WebP / SVG) to prevent broken links.
"""

import base64
import html
import urllib.parse
from pathlib import Path
from typing import Any

from src.placeholders import generate_phone_svg


def compact_html(raw_html: str) -> str:
    """Strip leading indentation and eliminate blank lines to prevent markdown code-block rendering.

    Markdown parsers treat any line indented by 4+ spaces or lines following blank lines
    inside HTML blocks as <pre><code> blocks. This function strips all indentation
    and removes blank lines, returning a compact, safe single-block HTML string.
    """
    lines = [line.strip() for line in raw_html.splitlines()]
    non_empty = [line for line in lines if line]
    return "\n".join(non_empty)


def get_image_data_uri(
    image_path: str | None, phone_name: str, brand: str | None = None
) -> tuple[str, bool]:
    """Return a browser-safe data URI and placeholder flag for a device image.

    Args:
        image_path: Relative or absolute path to local image.
        phone_name: Model name for placeholder fallback.
        brand: Brand name for placeholder accent colors.

    Returns:
        Tuple of (data_uri_string, is_placeholder_bool).
    """
    if image_path:
        p = Path(image_path)
        if p.exists() and p.is_file():
            suffix = p.suffix.lower()
            if suffix == ".svg":
                svg_text = p.read_text(encoding="utf-8")
                encoded = urllib.parse.quote(svg_text)
                return f"data:image/svg+xml;utf8,{encoded}", "placeholders" in str(
                    image_path
                )
            elif suffix in (".webp", ".png", ".jpg", ".jpeg"):
                mime = (
                    "image/webp"
                    if suffix == ".webp"
                    else ("image/png" if suffix == ".png" else "image/jpeg")
                )
                b64 = base64.b64encode(p.read_bytes()).decode("ascii")
                return f"data:{mime};base64,{b64}", False

    # Fallback to dynamically generated SVG silhouette
    fallback_svg = generate_phone_svg(phone_name, brand)
    encoded = urllib.parse.quote(fallback_svg)
    return f"data:image/svg+xml;utf8,{encoded}", True


def compute_spec_completeness(specs: dict[str, Any]) -> int:
    """Calculate percentage completeness across 6 core canonical specifications."""
    core_keys = [
        "processor_score",
        "camera_mp",
        "battery_mah",
        "display_hz",
        "storage_gb",
        "ram_gb",
    ]
    valid_count = sum(
        1
        for k in core_keys
        if k in specs and specs[k] is not None and str(specs[k]).lower() != "nan"
    )
    return int((valid_count / len(core_keys)) * 100)


def build_phone_card_html(
    r: Any,
    rank: int,
    lang_code: str,
    top_match_text: str = "Top Match",
    shortlisted_text: str = "Shortlisted",
    within_budget_text: str = "Within Budget",
    match_score_label: str = "Match Score",
    trade_offs_label: str = "Key Trade-offs",
    formatted_price: str = "",
) -> str:
    """Build compact, safe, responsive recommendation card HTML with phone image."""
    is_top = rank == 1
    card_class = "smartpick-card smartpick-card-top" if is_top else "smartpick-card"
    badge_class = "rank-badge rank-badge-top" if is_top else "rank-badge rank-badge-sub"
    badge_label = (
        f"⭐ #{rank} {top_match_text}" if is_top else f"#{rank} {shortlisted_text}"
    )

    # Escaped safe text
    safe_name = html.escape(str(r.phone_name or "Smartphone"))
    safe_brand = html.escape(str(r.brand or "General"))
    safe_price = html.escape(formatted_price or f"₹{r.price_inr:,.0f}")

    # Image URI and attribution caption
    img_uri, is_placeholder = get_image_data_uri(
        getattr(r, "image_path", None), r.phone_name, r.brand
    )

    if not is_placeholder and getattr(r, "image_attribution", None):
        attr_text = html.escape(str(r.image_attribution))
        lic_text = html.escape(str(getattr(r, "image_license", "") or "CC"))
        caption_html = f'<div class="card-img-caption" title="{attr_text}">Photo: {attr_text} ({lic_text})</div>'
    else:
        caption_html = '<div class="card-img-caption card-img-caption-muted">Image not available</div>'

    completeness = compute_spec_completeness(r.specs)
    trust_chip_class = "chip-budget-fit" if completeness == 100 else "chip-warning"
    trust_label = (
        "🛡️ 100% Spec Verified" if completeness == 100 else f"⚠️ {completeness}% Verified"
    )

    chips_html = f"""<div style="margin-top: 6px; margin-bottom: 12px;" role="group" aria-label="Device Attributes">
<span class="chip chip-brand">🏷️ {safe_brand}</span>
<span class="chip chip-budget-fit">{html.escape(within_budget_text)}</span>
{'<span class="chip chip-5g">⚡ 5G</span>' if r.specs.get("has_5g") else ""}
<span class="chip {trust_chip_class}">{trust_label}</span>
</div>"""

    missing_html = ""
    if r.missing_specs:
        missing_clean = html.escape(", ".join(r.missing_specs))
        missing_html = f"""<div class="trade-off-tag" style="background: rgba(239, 68, 68, 0.12); color: #F87171; border-left: 2px solid #EF4444;" role="alert">
⚠ Unverified attributes: {missing_clean} (Weights renormalized)
</div>"""

    trade_offs_html = ""
    if r.trade_offs:
        items = "".join(f"<div>• {html.escape(t)}</div>" for t in r.trade_offs)
        trade_offs_html = f"""<div class="trade-off-tag" role="note" aria-label="Trade-off details">
<div style="font-weight: 600; margin-bottom: 2px;">{html.escape(trade_offs_label)}</div>
{items}
</div>"""

    rationale_html = ""
    if r.rationale:
        rationale_html = f"""<div class="rationale-box" role="region" aria-label="Recommendation rationale">
💡 <b>Why this phone:</b> {html.escape(r.rationale)}
</div>"""

    proc_val = r.specs.get("processor_score")
    proc_str = (
        f"{int(proc_val):,}"
        if proc_val and str(proc_val).lower() != "nan"
        else "Unverified"
    )
    ram_str = str(r.specs.get("ram_gb", "N/A"))
    stor_str = str(r.specs.get("storage_gb", "N/A"))
    batt_str = str(r.specs.get("battery_mah", "N/A"))
    cam_str = str(r.specs.get("camera_mp", "N/A"))
    disp_str = str(r.specs.get("display_hz", "N/A"))

    raw_card = f"""<div class="{card_class}" role="region" aria-label="Recommendation #{rank}: {safe_name}" tabindex="0">
<div class="card-split">
<div class="card-img-col">
<div class="card-img-wrapper">
<img src="{img_uri}" alt="{safe_name} photo" loading="lazy"/>
</div>
{caption_html}
</div>
<div class="card-content-col">
<div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
<div>
<span class="{badge_class}" role="status">{badge_label}</span>
<h3 style="margin: 8px 0 2px 0; color: #F8FAFC; font-size: 1.25rem;">{safe_name}</h3>
</div>
<div style="text-align: right;">
<div class="mono-num" style="font-size: 1.45rem; font-weight: 700; color: #38BDF8;" aria-label="Price: {safe_price}">{safe_price}</div>
<div style="font-size: 0.72rem; color: #94A3B8;">Hard Budget Qualified</div>
</div>
</div>
{chips_html}
<div class="score-container" role="progressbar" aria-valuenow="{r.match_score:.1f}" aria-valuemin="0" aria-valuemax="100">
<div class="score-header">
<span style="font-weight: 600; color: #E2E8F0;">{html.escape(match_score_label)}</span>
<span class="mono-num" style="font-weight: 700; color: #38BDF8;">{r.match_score:.1f} / 100</span>
</div>
<div class="score-bar-bg">
<div class="score-bar-fill" style="width: {min(100.0, max(0.0, r.match_score))}%;"></div>
</div>
</div>
<div class="specs-grid" role="table" aria-label="Smartphone Specifications">
<div class="spec-item" role="row">
<span class="spec-label">Processor</span>
<span class="spec-val" aria-label="Processor Benchmark Score">{proc_str}</span>
</div>
<div class="spec-item" role="row">
<span class="spec-label">RAM / Storage</span>
<span class="spec-val" aria-label="Memory Configuration">{ram_str}GB / {stor_str}GB</span>
</div>
<div class="spec-item" role="row">
<span class="spec-label">Battery</span>
<span class="spec-val" aria-label="Battery Capacity">{batt_str} mAh</span>
</div>
<div class="spec-item" role="row">
<span class="spec-label">Camera</span>
<span class="spec-val" aria-label="Primary Camera Resolution">{cam_str} MP</span>
</div>
<div class="spec-item" role="row">
<span class="spec-label">Display</span>
<span class="spec-val" aria-label="Display Refresh Rate">{disp_str} Hz</span>
</div>
</div>
{rationale_html}
{missing_html}
{trade_offs_html}
</div>
</div>
</div>"""

    return compact_html(raw_card)


def build_hero_badge_html(
    catalog_status_text: str,
    source_name: str,
    verified_recent_text: str,
    last_verified: str,
    version_hash: str,
) -> str:
    """Build compact single-block hero badge HTML."""
    raw = f"""<div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 10px 14px; text-align: right; margin-top: 10px;">
<div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">{html.escape(catalog_status_text)}</div>
<div style="font-size: 0.85rem; font-weight: 600; color: #34D399;">● {html.escape(source_name)}</div>
<div style="font-size: 0.72rem; color: #64748B;">{html.escape(verified_recent_text)}: {html.escape(last_verified)} | v:{html.escape(version_hash)}</div>
</div>"""
    return compact_html(raw)


def build_footer_html() -> str:
    """Build compact single-block caveat footer HTML."""
    raw = """<div class="caveat-footer" role="contentinfo" aria-label="Legal Disclaimer">
<b>⚖️ Algorithmic Transparency & Consumer Caveat:</b>
SmartPick AI is an academic and competitive engineering project designed for transparent multi-criteria decision making.
The <b>Match Score</b> represents a mathematical preference alignment index relative to the active catalog and user weights.
It does <b>not</b> denote build quality, software longevity, camera color science, or user review ratings.
100% of displayed recommendations strictly satisfy the selected budget constraint.
Prices and specifications reflect catalog snapshots and do not constitute live e-commerce availability guarantees.
</div>"""
    return compact_html(raw)


def build_compare_column_header_html(
    phone_name: str,
    brand: str | None,
    price_str: str,
    image_path: str | None = None,
    attribution: str | None = None,
    license_str: str | None = None,
) -> str:
    """Build compact header HTML for a phone column in Tab 2 Compare."""
    safe_name = html.escape(str(phone_name))
    safe_price = html.escape(str(price_str))
    img_uri, is_placeholder = get_image_data_uri(image_path, phone_name, brand)

    if not is_placeholder and attribution:
        caption = f'<div class="card-img-caption" style="font-size: 0.65rem;">Photo: {html.escape(attribution)}</div>'
    else:
        caption = '<div class="card-img-caption card-img-caption-muted" style="font-size: 0.65rem;">Image not available</div>'

    raw = f"""<div style="text-align: center; margin-bottom: 14px;">
<div class="card-img-wrapper" style="height: 180px; max-width: 160px; margin: 0 auto;">
<img src="{img_uri}" alt="{safe_name}" loading="lazy"/>
</div>
{caption}
<h4 style="margin: 8px 0 2px 0; color: #F8FAFC; font-size: 1.05rem;">{safe_name}</h4>
<div class="mono-num" style="font-weight: 700; color: #38BDF8; font-size: 1.15rem;">{safe_price}</div>
</div>"""
    return compact_html(raw)


def build_no_candidates_html() -> str:
    """Build compact empty state alert HTML when no candidates match budget and filters."""
    raw = """<div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 24px; text-align: center; margin: 20px 0;">
<h3 style="color: #F87171; margin-top: 0;">🔍 No Devices Match Your Exact Constraints</h3>
<p style="color: #94A3B8; max-width: 600px; margin: 0 auto 16px auto;">
None of the devices in our catalog satisfied your combined budget window, brand filter, and 5G requirement.
</p>
<div style="text-align: left; display: inline-block; color: #CBD5E1; font-size: 0.9rem;">
<b>Actionable suggestions to broaden results:</b>
<ul style="margin: 8px 0 0 0; padding-left: 20px;">
<li>Widen your budget slider (e.g. adjust upper limit).</li>
<li>Uncheck brand restrictions to consider alternatives.</li>
<li>Toggle off the strict 5G requirement.</li>
</ul>
</div>
</div>"""
    return compact_html(raw)


def build_why_not_card_html(
    phone_name: str,
    price_inr: float,
    formatted_price: str,
    badge_txt: str,
    badge_col: str,
    primary_reason: str,
) -> str:
    """Build compact why-not counterfactual card HTML without indentation."""
    safe_name = html.escape(str(phone_name))
    safe_price = html.escape(str(formatted_price or f"₹{price_inr:,.0f}"))
    safe_reason = html.escape(str(primary_reason))
    safe_badge_txt = html.escape(str(badge_txt))
    safe_badge_col = html.escape(str(badge_col))

    raw = f"""<div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 20px; margin-top: 14px;">
<div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 8px;">
<div>
<span style="background: {safe_badge_col}; color: #FFFFFF; font-size: 0.75rem; font-weight: 700; padding: 4px 10px; border-radius: 6px; letter-spacing: 0.05em;">{safe_badge_txt}</span>
<h3 style="margin: 8px 0 2px 0; color: #F8FAFC;">{safe_name}</h3>
</div>
<div style="font-size: 1.4rem; font-weight: 700; color: #38BDF8; font-family: 'JetBrains Mono', monospace;">{safe_price}</div>
</div>
<div style="font-size: 0.95rem; color: #E2E8F0; margin-top: 12px; line-height: 1.5; padding-left: 10px; border-left: 3px solid {safe_badge_col};">
<b>Primary Finding:</b> {safe_reason}
</div>
</div>"""
    return compact_html(raw)
