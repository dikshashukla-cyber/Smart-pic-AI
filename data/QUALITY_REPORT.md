# SmartPick AI — Catalog Data Quality & Health Audit

**Audit Date**: 2026-10-15  
**Dataset Source**: `Synthetic Catalog`  
**Evaluation Status**: `SYNTHETIC SAMPLE (Labelled)`  
**Total Catalog Records**: `125` (Valid recommendable: `122`)  
**Overall Completeness**: `99.6%`  

---

## 1. Column Completeness & Specification Integrity

| Canonical Column | Present Count | Missing (NaN) | Completeness | Distinct Values | Notes & Policy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `phone_name` | 124 | 1 | 99.2% | 121 | Required (MVP) |
| `brand` | 125 | 0 | 100.0% | 19 | Optional (NaN preserved) |
| `price_inr` | 124 | 1 | 99.2% | 101 | Required (MVP) |
| `ram_gb` | 125 | 0 | 100.0% | 6 | Optional (NaN preserved) |
| `storage_gb` | 125 | 0 | 100.0% | 5 | Optional (NaN preserved) |
| `battery_mah` | 124 | 1 | 99.2% | 24 | Optional (NaN preserved) |
| `camera_mp` | 124 | 1 | 99.2% | 6 | Optional (NaN preserved) |
| `display_hz` | 124 | 1 | 99.2% | 4 | Optional (NaN preserved) |
| `has_5g` | 125 | 0 | 100.0% | 2 | Optional (NaN preserved) |
| `processor_score` | 124 | 1 | 99.2% | 101 | Optional (NaN preserved) |
| `source` | 125 | 0 | 100.0% | 2 | Optional (NaN preserved) |
| `verified_at` | 125 | 0 | 100.0% | 1 | Optional (NaN preserved) |

## 2. Price Band Distribution & Catalog Coverage

| Price Segment | Device Count | Share of Catalog | Min Price | Max Price | Median Price |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Budget (< ₹15,000) | 19 | 15.4% | ₹6,499 | ₹14,550 | ₹11,490 |
| Mid-Range (₹15,000 - ₹30,000) | 33 | 26.8% | ₹15,900 | ₹29,999 | ₹23,999 |
| Upper Mid-Range (₹30,000 - ₹50,000) | 19 | 15.4% | ₹30,999 | ₹49,999 | ₹41,999 |
| Flagship (₹50,000 - ₹80,000) | 31 | 25.2% | ₹50,400 | ₹79,900 | ₹66,600 |
| Ultra-Flagship (>= ₹80,000) | 21 | 17.1% | ₹80,100 | ₹199,900 | ₹99,999 |

## 3. Brand Distribution & Market Diversity

| Brand | Models Count | Share of Catalog | Price Range |
| :--- | :--- | :--- | :--- |
| **Samsung** | 20 | 16.0% | ₹11,490 - ₹164,999 |
| **Xiaomi** | 13 | 10.4% | ₹10,499 - ₹99,999 |
| **OnePlus** | 13 | 10.4% | ₹15,900 - ₹80,100 |
| **Realme** | 12 | 9.6% | ₹11,999 - ₹81,450 |
| **Motorola** | 12 | 9.6% | ₹8,999 - ₹85,500 |
| **Vivo** | 11 | 8.8% | ₹13,499 - ₹89,999 |
| **POCO** | 10 | 8.0% | ₹10,999 - ₹86,850 |
| **iQOO** | 10 | 8.0% | ₹12,999 - ₹84,150 |
| **Apple** | 7 | 5.6% | ₹70,999 - ₹199,900 |
| **Google** | 5 | 4.0% | ₹36,999 - ₹109,999 |
| **Infinix** | 2 | 1.6% | ₹6,499 - ₹8,999 |
| **Tecno** | 2 | 1.6% | ₹10,499 - ₹17,999 |
| **Nothing** | 2 | 1.6% | ₹23,999 - ₹27,999 |
| **Fairphone** | 1 | 0.8% | ₹45,000 - ₹45,000 |
| **Minimal** | 1 | 0.8% | ₹28,500 - ₹28,500 |
| **Unknown** | 1 | 0.8% | N/A |
| **Glitch** | 1 | 0.8% | N/A |
| **Atomic** | 1 | 0.8% | ₹89,999 - ₹89,999 |
| **Generic** | 1 | 0.8% | ₹9,999 - ₹9,999 |

## 4. Duplicate & Variant Audit

- **Exact Duplicate Rows**: `2` (Identified for warning, verified in test suite).
- **Legitimate Hardware Variants**: `23` records detected with identical base model keys but distinct RAM/storage/price tiers.
- **Deduplication Policy**: Exact duplicates flagged for inspection; hardware variants are preserved as distinct purchase options.

## 5. Row-Level Validation & Outlier Findings

| Row Index | Device Name | Column | Issue Type | Severity | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 76 | Mystery Phone X | `price_inr` | `MISSING_REQUIRED` | **ERROR** | Missing required price_inr (NaN). Row cannot be recommended. |
| 77 | Glitch Phone Beta | `price_inr` | `IMPLAUSIBLE_VALUE` | **ERROR** | Implausible price_inr: -15000.0. Price must be strictly positive. |
| 78 | Nuclear Phone Atomic | `battery_mah` | `IMPLAUSIBLE_VALUE` | **WARNING** | Implausible battery_mah: 999999.0 mAh (expected 500 to 25,000 mAh). |
| 79 | *(Missing)* | `phone_name` | `MISSING_REQUIRED` | **ERROR** | Missing required phone_name (empty or NaN). Row cannot be recommended. |
| 26 | Samsung Galaxy M34 5G | `phone_name` | `EXACT_DUPLICATE` | **WARNING** | Exact duplicate record found for 'Samsung Galaxy M34 5G' (Samsung). |
| 73 | Redmi 13C 5G | `phone_name` | `EXACT_DUPLICATE` | **WARNING** | Exact duplicate record found for 'Redmi 13C 5G' (Xiaomi). |
| 67 | Apple iPhone 15 Pro Max | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'apple iphone 15 pro max' (8.0GB RAM / 256.0GB ROM, ₹148900.0). Retained as distinct recommendable option. |
| 68 | Apple iPhone 15 Pro Max 1TB | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'apple iphone 15 pro max' (8.0GB RAM / 1024.0GB ROM, ₹199900.0). Retained as distinct recommendable option. |
| 37 | iQOO Neo9 Pro 5G | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'iqoo neo9 pro 5g' (8.0GB RAM / 128.0GB ROM, ₹34999.0). Retained as distinct recommendable option. |
| 38 | iQOO Neo9 Pro 5G (12GB/256GB) | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'iqoo neo9 pro 5g' (12.0GB RAM / 256.0GB ROM, ₹38999.0). Retained as distinct recommendable option. |
| 30 | Motorola Edge 50 Fusion | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'motorola edge 50 fusion' (8.0GB RAM / 128.0GB ROM, ₹22999.0). Retained as distinct recommendable option. |
| 31 | Motorola Edge 50 Fusion (12GB/256GB) | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'motorola edge 50 fusion' (12.0GB RAM / 256.0GB ROM, ₹24999.0). Retained as distinct recommendable option. |
| 50 | OnePlus 12 | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'oneplus 12' (12.0GB RAM / 256.0GB ROM, ₹64999.0). Retained as distinct recommendable option. |
| 51 | OnePlus 12 (16GB/512GB) | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'oneplus 12' (16.0GB RAM / 512.0GB ROM, ₹69999.0). Retained as distinct recommendable option. |
| 35 | OnePlus 12R | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'oneplus 12r' (8.0GB RAM / 128.0GB ROM, ₹39999.0). Retained as distinct recommendable option. |
| 36 | OnePlus 12R (16GB/256GB) | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'oneplus 12r' (16.0GB RAM / 256.0GB ROM, ₹45999.0). Retained as distinct recommendable option. |
| 19 | OnePlus Nord CE4 5G | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'oneplus nord ce4 5g' (8.0GB RAM / 128.0GB ROM, ₹24999.0). Retained as distinct recommendable option. |
| 20 | OnePlus Nord CE4 5G (8GB/256GB) | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'oneplus nord ce4 5g' (8.0GB RAM / 256.0GB ROM, ₹26999.0). Retained as distinct recommendable option. |
| 2 | POCO M6 Pro 5G | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'poco m6 pro 5g' (4.0GB RAM / 128.0GB ROM, ₹10999.0). Retained as distinct recommendable option. |
| 3 | POCO M6 Pro 5G (8GB/256GB) | `phone_name` | `VARIANT_DETECTED` | **INFO** | Hardware variant of base model 'poco m6 pro 5g' (8.0GB RAM / 256.0GB ROM, ₹13499.0). Retained as distinct recommendable option. |
| ... | *(9 additional issues logged in memory)* | | | | |

---
*Report auto-generated by `src/quality_report.py` QualityReportGenerator.*