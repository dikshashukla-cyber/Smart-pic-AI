# SmartPick AI — Dataset Provenance & Data Handling Record

In accordance with the SmartPick AI Dataset & Data Dictionary and TRD Section 5, this document records the origin, legal terms, validation history, and missing-value characteristics of the catalog data used by the recommender system.

---

## 1. Canonical Provenance Record

| Provenance Field | Documented Value |
| :--- | :--- |
| **Dataset name** | SmartPick AI Synthetic Benchmark Catalog (Sample v1.0) |
| **Source URL/name** | Procedurally generated synthetic catalog sample (`src/generate_sample.py`) with intentional edge cases for academic evaluation, testing, and UI verification. Real-world target dataset: `[fill in: e.g. Kaggle / GSMArena scrape / Flipkart API]` |
| **Licence/usage terms** | Creative Commons Zero (CC0) / MIT for synthetic benchmark artifacts. External dataset licence: `[fill in: e.g. CC-BY-4.0 / Proprietary (Personal Use Only)]` |
| **Retrieved on** | 2026-10-15 |
| **Last verified** | 2026-10-15 |
| **Fields with missing values** | `phone_name` (1 missing deliberate edge case row), `price_inr` (1 unparseable string set to NaN, 1 negative price flagged), `battery_mah` (1 missing), `camera_mp` (1 missing), `display_hz` (1 missing), `processor_score` (1 missing). All missing fields remain strictly `NaN` without zero-fill imputation. |
| **Redistribution allowed** | **Yes** for synthetic benchmark dataset (`data/phones.csv` and `data/raw/synthetic_phones_raw.csv`). For external scraped datasets: `[yes/no/unclear — verify before publishing]` |

---

## 2. Responsible Data Handling Directives

1. **No Artificial Zeroes**: Incomplete specifications remain `NaN` at all times. A missing battery capacity is displayed as *"Unverified"*, never `0 mAh`.
2. **Provenance Traceability**: When an evaluator substitutes an external smartphone dataset, they must place the raw CSV into `data/raw/`, run `python -m src.ingest`, and update Section 1 above with the actual retrieval URL and licensing terms.
3. **Price and Stock Volatility Notice**: Stored prices reflect snapshot catalog values at the time of retrieval (`verified_at`). They do not represent real-time retailer stock or dynamic flash-sale prices.
4. **Fair Evaluation Policy**: Synthetic benchmark labels and samples are designed for functional, architectural, and edge-case testing; they must not be presented as empirical consumer behavioral studies.
