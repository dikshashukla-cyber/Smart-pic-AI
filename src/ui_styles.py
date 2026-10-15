"""Custom CSS styles and design system token injection for SmartPick AI.

Implements the fintech-grade Deep Slate Dark aesthetic defined in docs/DESIGN_SYSTEM.md:
- Glassmorphic card surfaces with subtle borders and hover elevation
- Progress bar styling with sapphire-to-cyan gradients
- Dual-channel accessible chips and badges (color + icon + text)
- Monospace spec value alignment
- Responsive mobile container adjustments
"""

import streamlit as st


def inject_custom_styles() -> None:
    """Inject custom CSS matching the SmartPick AI Design System."""
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Typography and Variables */
    :root {
        --bg-base: #0F172A;
        --bg-surface: #1E293B;
        --bg-elevated: #334155;
        --border-subtle: rgba(255, 255, 255, 0.08);
        --border-active: rgba(59, 130, 246, 0.5);
        --primary-blue: #2563EB;
        --accent-cyan: #06B6D4;
        --text-primary: #F8FAFC;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;
        --status-success: #10B981;
        --status-warning: #F59E0B;
        --status-danger: #EF4444;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Monospace Numeric Styling */
    .mono-num {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        letter-spacing: -0.02em;
    }

    /* Recommendation Card (Fintech Glassmorphic Surface) */
    .smartpick-card {
        background: rgba(30, 41, 59, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.35);
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }

    .smartpick-card:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 8px 30px -4px rgba(37, 99, 235, 0.2);
    }

    /* Top Ranked (#1) Featured Card Glow */
    .smartpick-card-top {
        border: 1px solid rgba(59, 130, 246, 0.6);
        background: linear-gradient(180deg, rgba(30, 58, 138, 0.28) 0%, rgba(30, 41, 59, 0.85) 100%);
        box-shadow: 0 8px 32px -4px rgba(37, 99, 235, 0.3);
    }

    /* Rank Badges */
    .rank-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .rank-badge-top {
        background: #2563EB;
        color: #FFFFFF;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);
    }

    .rank-badge-sub {
        background: rgba(51, 65, 85, 0.8);
        color: #94A3B8;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Dual-Channel Chips (Color + Icon + Text) */
    .chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }

    .chip-brand {
        background: rgba(30, 41, 59, 0.9);
        color: #E2E8F0;
        border: 1px solid rgba(255, 255, 255, 0.12);
    }

    .chip-budget-fit {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }

    .chip-5g {
        background: rgba(6, 182, 212, 0.15);
        color: #22D3EE;
        border: 1px solid rgba(6, 182, 212, 0.4);
    }

    .chip-warning {
        background: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }

    /* Score Progress Bar */
    .score-container {
        margin: 12px 0;
    }

    .score-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.85rem;
        margin-bottom: 6px;
    }

    .score-bar-bg {
        width: 100%;
        height: 8px;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 4px;
        overflow: hidden;
    }

    .score-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #2563EB 0%, #06B6D4 100%);
        border-radius: 4px;
        transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* Specifications Grid */
    .specs-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 10px;
        background: rgba(15, 23, 42, 0.45);
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.04);
        margin: 14px 0;
    }

    .spec-item {
        display: flex;
        flex-direction: column;
    }

    .spec-label {
        font-size: 0.7rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .spec-val {
        font-size: 0.875rem;
        color: #F8FAFC;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Explanation and Trade-off callouts */
    .rationale-box {
        font-size: 0.875rem;
        line-height: 1.5;
        color: #E2E8F0;
        margin: 10px 0;
        padding-left: 12px;
        border-left: 3px solid #3B82F6;
    }

    .trade-off-tag {
        font-size: 0.8rem;
        color: #FBBF24;
        background: rgba(245, 158, 11, 0.1);
        padding: 4px 8px;
        border-radius: 4px;
        margin-top: 6px;
        display: inline-block;
        border-left: 2px solid #F59E0B;
    }

    /* Footer disclaimer styling */
    .caveat-footer {
        margin-top: 48px;
        padding: 20px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        font-size: 0.8rem;
        color: #94A3B8;
        line-height: 1.5;
    }

    /* Split Card Layout with Phone Image */
    .card-split {
        display: flex;
        gap: 20px;
        align-items: stretch;
    }

    .card-img-col {
        width: 160px;
        min-width: 160px;
        max-width: 160px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
    }

    .card-img-wrapper {
        width: 100%;
        height: 220px;
        border-radius: 8px;
        overflow: hidden;
        background: #0B0F17;
        border: 1px solid rgba(255, 255, 255, 0.08);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .card-img-wrapper img {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }

    .card-img-caption {
        font-size: 0.68rem;
        color: #64748B;
        text-align: center;
        margin-top: 6px;
        line-height: 1.25;
        word-break: break-word;
    }

    .card-img-caption-muted {
        color: #475569;
        font-style: italic;
    }

    .card-content-col {
        flex: 1;
        min-width: 0;
    }

    /* Preset Buttons in Sidebar: Full label visibility & text wrapping */
    [data-testid="stSidebar"] button {
        white-space: normal !important;
        word-wrap: break-word !important;
        height: auto !important;
        min-height: 40px !important;
        padding: 6px 8px !important;
        font-size: 0.82rem !important;
        line-height: 1.2 !important;
    }

    /* Mobile Responsive Optimizations */
    @media (max-width: 768px) {
        .smartpick-card {
            padding: 16px;
        }
        .card-split {
            flex-direction: column;
            align-items: center;
        }
        .card-img-col {
            width: 100%;
            max-width: 220px;
            margin-bottom: 12px;
        }
        .card-img-wrapper {
            height: 240px;
        }
        .specs-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    </style>
    """
    st.markdown(custom_css.strip(), unsafe_allow_html=True)
