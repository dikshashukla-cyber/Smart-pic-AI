# SmartPick AI — Design System & UI Specification

**Version**: 1.0  
**Design Tier**: Premium Enterprise / Fintech-Grade Recommender  
**Compliance Standard**: WCAG 2.1 AA Accessible  

---

## 1. Visual Philosophy & Design Principles

SmartPick AI employs a **fintech-grade, high-density dashboard aesthetic** inspired by modern analytical terminals (Linear, Stripe Dashboard, Bloomberg terminal modernizations). Recommender interfaces in student projects frequently suffer from toy-like layouts, low visual hierarchy, and ambiguous scores. SmartPick AI addresses this with:

1. **Radical Transparency**: Visual components never present machine learning or heuristic scores as magic numbers. Match scores are explicitly branded as **"Preference Match Indices"**, never "quality ratings" or "purchase probabilities".
2. **Dual-Channel Accessibility**: Information is **never conveyed by color alone**. Every status badge, score metric, and warning pairs color tokens with clear iconography, text labels, and accessible contrast ratios (minimum 4.5:1 for normal text).
3. **Structured Density**: Information is organized into crisp glassmorphic cards, compact metric chips, and structured tabular comparisons, allowing decision-makers to evaluate complex smartphone hardware trade-offs in seconds.

---

## 2. Color Palette (Dark & Light Schemes)

The default application theme is **Deep Slate Dark**, optimized for extended analytical review and high contrast. A reciprocal **Clean Slate Light** theme is defined for enterprise light environments.

### 2.1 Core Neutral Palette

| Token Name | Dark Mode Value | Light Mode Value | Usage Description |
| :--- | :--- | :--- | :--- |
| `--bg-base` | `#0F172A` (Slate 900) | `#F8FAFC` (Slate 50) | Main canvas application background |
| `--bg-surface` | `#1E293B` (Slate 800) | `#FFFFFF` (Pure White) | Card containers, sidebar panels, modal surfaces |
| `--bg-surface-elevated` | `#334155` (Slate 700) | `#F1F5F9` (Slate 100) | Hover states, dropdown menus, table headers |
| `--border-subtle` | `rgba(255, 255, 255, 0.08)` | `#E2E8F0` (Slate 200) | Container outlines, subtle separators |
| `--border-active` | `rgba(59, 130, 246, 0.4)` | `#93C5FD` (Blue 300) | Active focus rings, selected card highlights |
| `--text-primary` | `#F8FAFC` (Slate 50) | `#0F172A` (Slate 900) | Card titles, key specifications, primary headings |
| `--text-secondary` | `#94A3B8` (Slate 400) | `#475569` (Slate 600) | Body descriptions, field labels, metadata timestamps |
| `--text-muted` | `#64748B` (Slate 500) | `#94A3B8` (Slate 400) | Footers, disclaimer notes, helper text |

### 2.2 Brand & Primary Accent

| Token Name | Hex Code | HSL Equivalent | Role & Contrast Ratio |
| :--- | :--- | :--- | :--- |
| `--primary-600` | `#2563EB` | `hsl(221, 83%, 53%)` | Primary button fill, active tab indicator (AA compliant against white text) |
| `--primary-500` | `#3B82F6` | `hsl(217, 91%, 60%)` | Interactive hover states, progress bar gradients |
| `--primary-400` | `#60A5FA` | `hsl(213, 94%, 68%)` | Glow accents on top-ranked recommendation |
| `--primary-900` | `#1E3A8A` | `hsl(224, 64%, 33%)` | Tinted pill backgrounds, glassmorphism card highlights |

### 2.3 Semantic Status Palette

Every semantic token maintains at least **4.5:1 contrast** against its respective container background.

| Semantic Role | Token Name | Dark Hex | Light Hex | Paired Icon & Text Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **Success / Match** | `--status-success` | `#10B981` | `#059669` | `[✔ Check]` "100% Budget Fit" / "Verified" |
| **Warning / Caveat** | `--status-warning` | `#F59E0B` | `#D97706` | `[⚠ Alert]` "Missing Spec: Battery mAh unverified" |
| **Critical / Out of Bound** | `--status-danger` | `#EF4444` | `#DC2626` | `[✖ Error]` "Exceeds Budget Constraint" |
| **Informational / Neutral** | `--status-info` | `#06B6D4` | `#0284C7` | `[ℹ Info]` "Ranking Baseline (Not a trained model)" |

---

## 3. Typography Scale & Hierarchy

### 3.1 Font Families
- **Display & Interface**: `Inter`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`, sans-serif.
- **Metrics, Spec Numbers, & Currency**: `JetBrains Mono`, `SFMono-Regular`, `Consolas`, monospace (ensures perfect tabular number alignment).

### 3.2 Type Scale

| Level | Size (rem / px) | Weight | Line Height | Tracking | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Display** | `2.0rem` / `32px` | `700 (Bold)` | `1.2` | `-0.02em` | App Header Title |
| **H1** | `1.5rem` / `24px` | `600 (SemiBold)` | `1.3` | `-0.01em` | Section Headers ("Top 5 Recommendations") |
| **H2** | `1.25rem` / `20px` | `600 (SemiBold)` | `1.35` | `0` | Device Model Card Heading |
| **H3 / Subhead**| `1.0rem` / `16px` | `500 (Medium)` | `1.4` | `0` | Filter Group Titles, Chart Titles |
| **Body Primary**| `0.875rem` / `14px` | `400 (Regular)` | `1.5` | `0` | Rationales, spec values, explanations |
| **Body Mono** | `0.875rem` / `14px` | `500 (Medium)` | `1.4` | `0` | Prices (`₹24,999`), RAM (`8 GB`), Benchmarks |
| **Caption / Pill**| `0.75rem` / `12px` | `600 (SemiBold)` | `1.4` | `+0.02em` | Feature Chips, Disclaimer notes, Badges |
| **Micro / Legal**| `0.6875rem` / `11px`| `400 (Regular)` | `1.4` | `+0.01em` | Provenance source links, timestamp notes |

---

## 4. Spacing, Grid, and Elevation System

### 4.1 4px / 8px Spatial Scale
- `space-1`: `4px` (tight icon padding, badge horizontal margins)
- `space-2`: `8px` (chip spacing, input field inner margins)
- `space-3`: `12px` (card content separation, compact table cell padding)
- `space-4`: `16px` (standard card padding, grid gap)
- `space-6`: `24px` (section gaps, sidebar container padding)
- `space-8`: `32px` (major block transitions)
- `space-12`: `48px` (page level dividers)

### 4.2 Elevation & Glassmorphism Surfaces

```css
/* Card Surface (Dark Theme Glassmorphic) */
.smartpick-card {
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.35);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.smartpick-card:hover {
  transform: translateY(-2px);
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 8px 30px -4px rgba(37, 99, 235, 0.2);
}

/* Featured / #1 Rank Badge Surface */
.smartpick-card-top {
  border: 1px solid rgba(59, 130, 246, 0.5);
  background: linear-gradient(180deg, rgba(30, 58, 138, 0.25) 0%, rgba(30, 41, 59, 0.8) 100%);
  box-shadow: 0 8px 32px -4px rgba(37, 99, 235, 0.25);
}
```

---

## 5. UI Component Specifications

### 5.1 Recommendation Device Card
Each recommendation card is structured with clear visual zones:
1. **Header Row**: Device Name (`H2`), Brand Pill, and Rank Badge (`#1 BEST MATCH`).
2. **Pricing & Constraint Badge**: Formatted Price in INR with strict `100% Budget Fit` verification badge.
3. **Preference Match Index Bar**: Visual gradient progress bar displaying normalized match index with explicit label: *"Score: 88.4/100 (Relative Heuristic Match Index)"*.
4. **Key Specs Matrix (Grid)**:
   - RAM & Storage (`8 GB / 128 GB`)
   - Battery & Charging (`5,000 mAh`)
   - Camera (`50 MP Main`)
   - Display (`120 Hz AMOLED`)
   - Processor / Benchmark (`Score: 685,000 AnTuTu v10` or `Unverified`)
   - *Missing fields explicitly marked with `NaN / Unverified` chip, never 0*.
5. **Specification Rationale**: Human-readable explanation explicitly citing the user's active weights and real specifications (e.g., *"Recommended because performance weight (40%) matches the Dimensity 7200 processor and 120Hz display within your ₹25,000 budget"*).

### 5.2 Metric Chips & Badges
- **5G Status Chip**: Solid background (`rgba(6, 182, 212, 0.15)`), border (`rgba(6, 182, 212, 0.4)`), text (`#22D3EE`), accompanied by icon `⚡ 5G Ready`.
- **Missing Spec Caveat Chip**: Solid background (`rgba(245, 158, 11, 0.12)`), text (`#FBBF24`), accompanied by icon `⚠ Spec Unverified`.
- **Budget Fit Badge**: Solid emerald badge (`#064E3B`), text (`#34D399`), accompanied by icon `✔ Within Budget`.

### 5.3 Match Index Progress Bar
- **Scale**: `0` to `100%`.
- **Gradient Fill**: `linear-gradient(90deg, #2563EB 0%, #38BDF8 100%)`.
- **Track**: `rgba(255, 255, 255, 0.1)`.
- **Height**: `8px` with `4px` border radius.
- **Accompanying Caption**: Monospace percentage text alongside a permanent disclaimer tooltip.

### 5.4 Comparison Matrix Component
- Side-by-side vertical column comparison for selected shortlisted phones.
- Row-level highlight highlighting specification advantages (e.g. Higher battery mAh, Higher refresh rate).
- Missing values styled in italicized neutral slate (`--text-muted`), never populated as `0`.

---

## 6. Accessibility & Compliance Directives (WCAG 2.1 AA)

1. **Non-Color Dependent Signifiers**:
   - Every price constraint check displays a checkmark icon `[✔]` or cross `[✖]` along with explicit textual explanation.
   - High, medium, and low scores are represented with progress bars, numerical labels, and text descriptions (*"Strong Alignment"*, *"Moderate Alignment"*), never color tints alone.
2. **Contrast Ratio Audits**:
   - Text `#F8FAFC` on `#1E293B` = **12.6:1** (Passes AAA).
   - Text `#94A3B8` on `#1E293B` = **5.4:1** (Passes AA).
   - Primary Accent `#3B82F6` on `#0F172A` = **5.8:1** (Passes AA).
   - Warning `#F59E0B` text on `#1E293B` = **4.8:1** (Passes AA).
3. **Screen Reader and Keyboard Semantics**:
   - All sliders, checkboxes, and buttons possess unique descriptive `key` attributes in Streamlit.
   - Clear markdown section headings (`#`, `##`, `###`) ensure linear document outline navigation.
4. **Data Honesty Callouts**:
   - Mandatory visible banner at the base of every recommendation list:
     > *"Notice: Recommendations are computed by a transparent multi-attribute ranking baseline and content similarity algorithm. Match scores represent relative preference alignment to your selected criteria, not an objective probability of satisfaction or verified purchasing endorsement. Specifications reflect catalog snapshot data."*
