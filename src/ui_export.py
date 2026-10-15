"""Export utilities for SmartPick AI recommendations.

Generates:
1. Clean structured CSV export.
2. Self-contained printable HTML/PDF report with styled specification matrices
   and natural-language rationales (free of personal information).
"""

from typing import Any

import pandas as pd

from src.data_loader import DatasetMetadata
from src.recommender import RecommendationResult, UserPreferences


def export_recommendations_csv(results: list[RecommendationResult]) -> str:
    """Format recommendation results into downloadable CSV string."""
    rows: list[dict[str, Any]] = []
    for rank, r in enumerate(results, start=1):
        rows.append(
            {
                "Rank": rank,
                "Phone Name": r.phone_name,
                "Brand": r.brand or "N/A",
                "Price (INR)": r.price_inr,
                "Match Score (0-100)": r.match_score,
                "RAM (GB)": r.specs.get("ram_gb"),
                "Storage (GB)": r.specs.get("storage_gb"),
                "Battery (mAh)": r.specs.get("battery_mah"),
                "Camera (MP)": r.specs.get("camera_mp"),
                "Display (Hz)": r.specs.get("display_hz"),
                "5G Supported": r.specs.get("has_5g"),
                "Processor Score": r.specs.get("processor_score"),
                "Rationale": r.rationale,
            }
        )
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def export_recommendations_html(
    results: list[RecommendationResult],
    prefs: UserPreferences,
    metadata: DatasetMetadata,
) -> str:
    """Generate self-contained, printable HTML report of recommendations."""
    cards_html = []
    for rank, r in enumerate(results, start=1):
        missing_note = (
            f"<div style='color: #b45309; font-size: 12px; margin-top: 4px;'>⚠ Unverified specs: {', '.join(r.missing_specs)}</div>"
            if r.missing_specs
            else ""
        )

        cards_html.append(f"""
        <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px; background: #ffffff;">
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <h3 style="margin: 0; color: #0f172a; font-size: 18px;">#{rank} {r.phone_name}</h3>
                <span style="font-size: 16px; font-weight: bold; color: #2563eb;">₹{int(r.price_inr):,}</span>
            </div>
            <div style="color: #64748b; font-size: 13px; margin: 4px 0 10px 0;">
                Brand: <b>{r.brand or "N/A"}</b> | Match Score: <b>{r.match_score:.1f}/100</b> (Relative Preference Index)
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 10px;">
                <tr style="background: #f8fafc;">
                    <th style="padding: 6px; border: 1px solid #e2e8f0; text-align: left;">RAM</th>
                    <th style="padding: 6px; border: 1px solid #e2e8f0; text-align: left;">Storage</th>
                    <th style="padding: 6px; border: 1px solid #e2e8f0; text-align: left;">Battery</th>
                    <th style="padding: 6px; border: 1px solid #e2e8f0; text-align: left;">Camera</th>
                    <th style="padding: 6px; border: 1px solid #e2e8f0; text-align: left;">Display</th>
                    <th style="padding: 6px; border: 1px solid #e2e8f0; text-align: left;">5G</th>
                </tr>
                <tr>
                    <td style="padding: 6px; border: 1px solid #e2e8f0;">{r.specs.get("ram_gb", "N/A")} GB</td>
                    <td style="padding: 6px; border: 1px solid #e2e8f0;">{r.specs.get("storage_gb", "N/A")} GB</td>
                    <td style="padding: 6px; border: 1px solid #e2e8f0;">{r.specs.get("battery_mah", "N/A")} mAh</td>
                    <td style="padding: 6px; border: 1px solid #e2e8f0;">{r.specs.get("camera_mp", "N/A")} MP</td>
                    <td style="padding: 6px; border: 1px solid #e2e8f0;">{r.specs.get("display_hz", "N/A")} Hz</td>
                    <td style="padding: 6px; border: 1px solid #e2e8f0;">{"Yes" if r.specs.get("has_5g") else "No"}</td>
                </tr>
            </table>
            <div style="font-size: 13px; color: #334155; line-height: 1.4; padding-left: 8px; border-left: 3px solid #3b82f6;">
                <b>Rationale:</b> {r.rationale}
            </div>
            {missing_note}
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>SmartPick AI — Smartphone Recommendation Report</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px; color: #0f172a; }}
            .header {{ border-bottom: 2px solid #2563eb; padding-bottom: 12px; margin-bottom: 24px; }}
            .meta-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin-bottom: 24px; font-size: 13px; }}
            .footer {{ margin-top: 40px; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 12px; }}
            @media print {{ body {{ margin: 20px; }} }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin: 0; color: #1e3a8a; font-size: 24px;">SmartPick AI — Personalized Recommendation Report</h1>
            <div style="color: #64748b; font-size: 13px; margin-top: 4px;">Transparent, Specification-Grounded Smartphone Shortlist</div>
        </div>

        <div class="meta-box">
            <b>Configured Constraints:</b> Budget: ₹{int(prefs.min_budget):,} - ₹{int(prefs.max_budget):,} |
            Performance: {prefs.weight_performance:.2f} | Camera: {prefs.weight_camera:.2f} | Battery: {prefs.weight_battery:.2f} | Display: {prefs.weight_display:.2f}<br>
            <b>Catalog Provenance:</b> {metadata.source_name or "Curated Catalog"} (Verified: {metadata.last_verified or "2026-10-15"}) |
            <b>Status:</b> {"Synthetic Benchmark Sample" if metadata.is_synthetic else "Verified Catalog"}
        </div>

        <div>
            {"".join(cards_html)}
        </div>

        <div class="footer">
            <b>Notice:</b> This report was automatically generated by SmartPick AI. Match scores reflect relative heuristic preference alignment
            derived from catalog snapshot specifications. Stored prices and availability do not represent real-time retailer checkout guarantees.
            No personal data was stored or collected.
        </div>
    </body>
    </html>
    """
    return html_content
