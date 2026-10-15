"""SVG Phone Silhouette and Placeholder Generator for SmartPick AI.

Generates sleek, modern, fintech-styled SVG phone silhouettes with brand-specific
color accents, device screen outlines, and model names for devices lacking
a real licensed photo. Guarantees the UI never renders broken images.
"""

import re
from pathlib import Path

BRAND_ACCENT_COLORS: dict[str, str] = {
    "samsung": "#1D4ED8",  # Samsung Blue
    "apple": "#64748B",  # Apple Slate
    "xiaomi": "#EA580C",  # Xiaomi Orange
    "oneplus": "#DC2626",  # OnePlus Red
    "google": "#2563EB",  # Google Blue
    "nothing": "#475569",  # Nothing Monochrome
    "poco": "#CA8A04",  # POCO Yellow
    "realme": "#D97706",  # Realme Gold
    "motorola": "#0284C7",  # Motorola Cyan
    "vivo": "#4F46E5",  # Vivo Indigo
    "iqoo": "#EAB308",  # iQOO Amber
    "infinix": "#16A34A",  # Infinix Green
    "tecno": "#0284C7",  # Tecno Blue
    "fairphone": "#0D9488",  # Fairphone Teal
}

DEFAULT_BRAND_COLOR = "#38BDF8"  # SmartPick Sky Blue


def slugify_phone_name(phone_name: str) -> str:
    """Convert phone name to a clean filesystem-safe slug.

    Example: 'Samsung Galaxy S24 Ultra (12GB/256GB)' -> 'samsung-galaxy-s24-ultra'
    """
    cleaned = re.sub(r"\([^)]*\)", "", str(phone_name or ""))
    cleaned = re.sub(r"[^\w\s-]", "", cleaned).strip().lower()
    slug = re.sub(r"[\s_]+", "-", cleaned)
    return slug or "smartphone"


def get_brand_color(brand: str | None) -> str:
    """Return canonical hexadecimal accent color for a manufacturer."""
    b = str(brand or "").strip().lower()
    return BRAND_ACCENT_COLORS.get(b, DEFAULT_BRAND_COLOR)


def generate_phone_svg(phone_name: str, brand: str | None = None) -> str:
    """Generate high-contrast, fintech-themed SVG phone silhouette.

    Dimensions: 600 x 800 (3:4 portrait aspect ratio matching device photos).
    """
    brand_color = get_brand_color(brand)
    brand_name = (brand or "Smartphone").upper()
    clean_name = re.sub(r"\([^)]*\)", "", str(phone_name or "")).strip()

    # Split clean name into lines if too long for clean SVG rendering
    words = clean_name.split()
    line1 = " ".join(words[:3]) if words else "Device"
    line2 = " ".join(words[3:6]) if len(words) > 3 else ""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" width="600" height="800">
  <defs>
    <linearGradient id="bodyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1E293B"/>
      <stop offset="100%" stop-color="#0F172A"/>
    </linearGradient>
    <linearGradient id="screenGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#090D16"/>
      <stop offset="50%" stop-color="#0F172A"/>
      <stop offset="100%" stop-color="#1E293B"/>
    </linearGradient>
    <linearGradient id="accentGlow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{brand_color}" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="{brand_color}" stop-opacity="0.05"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#000000" flood-opacity="0.6"/>
    </filter>
  </defs>

  <!-- Neutral Canvas Background -->
  <rect width="600" height="800" fill="#0B0F17" rx="16"/>

  <!-- Phone Chassis Outer Shadow & Body -->
  <g filter="url(#shadow)">
    <!-- Outer Bezel -->
    <rect x="90" y="50" width="420" height="700" rx="44" fill="#334155" stroke="#475569" stroke-width="2"/>
    <!-- Inner Frame -->
    <rect x="96" y="56" width="408" height="688" rx="38" fill="url(#bodyGrad)"/>
    <!-- Screen Glass -->
    <rect x="110" y="72" width="380" height="656" rx="28" fill="url(#screenGrad)"/>
    <!-- Subtle Brand Ambient Glow -->
    <rect x="110" y="72" width="380" height="656" rx="28" fill="url(#accentGlow)"/>
  </g>

  <!-- Speaker Grill / Punch-hole Camera -->
  <circle cx="300" cy="96" r="6" fill="#020617" stroke="#334155" stroke-width="1.5"/>
  <rect x="270" y="80" width="60" height="3" rx="1.5" fill="#1E293B"/>

  <!-- Screen Content: Brand Pill -->
  <rect x="230" y="240" width="140" height="28" rx="14" fill="{brand_color}" fill-opacity="0.2" stroke="{brand_color}" stroke-width="1.5"/>
  <text x="300" y="259" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="700" fill="{brand_color}" text-anchor="middle" letter-spacing="1.5">{brand_name}</text>

  <!-- Phone Silhouette Icon -->
  <path d="M280 320 H320 A8 8 0 0 1 328 328 V400 A8 8 0 0 1 320 408 H280 A8 8 0 0 1 272 400 V328 A8 8 0 0 1 280 320 Z" fill="none" stroke="{brand_color}" stroke-width="3" stroke-dasharray="4 2"/>
  <circle cx="300" cy="336" r="2.5" fill="{brand_color}"/>
  <line x1="290" y1="398" x2="310" y2="398" stroke="{brand_color}" stroke-width="2" stroke-linecap="round"/>

  <!-- Phone Model Name -->
  <text x="300" y="460" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="700" fill="#F8FAFC" text-anchor="middle">{line1}</text>
  <text x="300" y="490" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="18" font-weight="600" fill="#CBD5E1" text-anchor="middle">{line2}</text>

  <!-- Spec Quality Label -->
  <text x="300" y="550" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="500" fill="#64748B" text-anchor="middle" letter-spacing="0.5">SMARTPICK AI SPEC CATALOG</text>
  <text x="300" y="572" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="400" fill="#475569" text-anchor="middle">Image Not Available</text>

  <!-- Home Indicator Bar -->
  <rect x="250" y="712" width="100" height="4" rx="2" fill="#475569"/>
</svg>"""
    return svg


def save_phone_placeholder_svg(
    phone_name: str,
    brand: str | None = None,
    output_dir: Path | str = "assets/phones/placeholders",
) -> Path:
    """Generate and write a phone placeholder SVG file to disk."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify_phone_name(phone_name)
    target_path = out_dir / f"{slug}.svg"
    svg_content = generate_phone_svg(phone_name, brand)
    target_path.write_text(svg_content, encoding="utf-8")
    return target_path
