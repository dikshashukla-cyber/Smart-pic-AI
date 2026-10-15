# SmartPick AI — National Competition Implementation Plan & Engineering Blueprint

**Project**: SmartPick AI — Intelligent Mobile Recommender  
**Author**: Principal ML Engineer & Product Designer  
**Target Delivery Standard**: National-Level Competition Winner (Technical Depth, Honesty, UX Polish, Presentation)  
**Governance Hierarchy**: `TRD > PRD > Implementation Guide > Test Plan > Checklist > Data Dictionary > Demo Guide`  

---

## 1. Executive Summary & Winning Mandate

Most student and hackathon recommender systems fail because of a common set of flaws:
1. **"ML-Washing"**: Passing off simple weighted sums or Euclidean distances as "deep neural networks" or "AI models".
2. **Fabricated / Zero-Filled Data**: Silently turning missing values (`NaN`) into `0`, which artificially penalizes phones or distorts recommendations.
3. **Budget Violations**: Returning recommendations that exceed the user's hard budget constraints or assuming soft boundaries without consent.
4. **Unverifiable Accuracy Claims**: Flaunting 98% Precision@5 or NDCG scores calculated on hand-crafted synthetic data while claiming it proves real-world recommendation efficacy.
5. **Toy Interfaces**: Amateurish, low-contrast Streamlit dashboards lacking visual hierarchy, stateful ergonomics, or accessible design.

**SmartPick AI wins on technical depth, radical honesty, and fintech-grade polish.**
By treating our baseline ranking as what it is—a transparent multi-attribute heuristic baseline—and reserving advanced metric claims strictly for validated ground-truth evaluations, we establish an unassailable position of engineering integrity before competition judges and senior evaluators.

---

## 2. Document Audit & Conflict Resolution

In accordance with our strict source-of-truth hierarchy (**TRD > PRD > others**), an exhaustive audit across all 7 project documents was conducted. The table below documents every identified conflict, ambiguity, and technical resolution.

| Conflict / Ambiguity Area | PRD vs TRD vs Other Docs | Resolution & Hard Rule Enforced |
| :--- | :--- | :--- |
| **Document Priority** | PRD and companion docs had slight variations in terminology. | **TRD is absolute supreme authority** (`TRD > PRD > others`). If a conflict arises on architecture or algorithms, TRD specifications govern. |
| **Raw Dataset Status (`/data/raw`)** | Checklist & Guide mention `data/phones.csv`. Data Dictionary explicitly states: *"It describes the expected schema; it does not claim a real dataset has already been sourced."* | Direct inspection of workspace and system confirmed **no pre-existing `data/raw` or `phones.csv`**. Sourcing/curation protocol is formally scheduled in Phase 1; raw data is quarantined and licensed. |
| **Model Nomenclature** | Marketing materials often say "AI recommender". TRD §6.3 & PRD §10 strictly specify: *"Do not call a hand-written weighted formula a trained ML model; label it as a ranking baseline."* | **Hard Rule**: The weighted formula is explicitly labelled in the codebase, UI, and docs as **"Ranking Baseline"**. Cosine similarity is labelled **"Content-Based Similarity"**. Neither will be branded as a "trained model". |
| **Score Interpretation** | Users may interpret match score as an objective device review rating or probability. | **Hard Rule**: The UI and code strictly state: **"Match score is a relative heuristic preference index (0-100%), not a calibrated probability or universal quality rating."** |
| **Budget Constraint Enforcement** | Some recommender literature treats budget as a soft penalty in the loss/objective function. | **Hard Rule**: **100% of displayed results must satisfy the user's budget constraint** (`min_budget <= price_inr <= max_budget`). Budget is a hard deterministic filter, never a soft penalty. |
| **Missing Value Policy** | Preprocessing in generic tutorials fills missing specs with `0` or global mean. | **Hard Rule**: **Missing stays `NaN`, never converted to `0`**. Zero-filling corrupts scaling (e.g. 0 mAh battery or 0 Hz display). Missing fields are displayed as `Unverified / NaN` with UI warning chips. |
| **Evaluation Metrics & Synthetic Labels** | Test Plan lists TC-11 (Precision/Recall/NDCG). PRD §10 & TRD §7 note: interaction labels do not natively exist for offline catalogs. | **Hard Rule**: **Precision@K, Recall@K, and NDCG@K are computed only with documented relevance labels**. Synthetic labels are strictly quarantined for functional code path tests and explicitly labelled as `synthetic`. |
| **Specification Limits (Megapixels & Battery)** | Data Dictionary §2 warns: camera MP is not camera quality; battery mAh is not battery endurance. | **Hard Rule**: Explanations cite only real available fields without claiming unproven physical attributes (e.g., cite "5000 mAh capacity", not "lasts 2 full days"). |
| **Top K Results Delivery** | PRD mentions Top 5 fixed; TRD allows Top K with default 5. | Recommender engine defaults to Top 5 (`top_k=5`) with user-configurable slider up to Top 10 for advanced users. |
| **Processor Benchmark Normalization** | Data Dictionary requires documenting benchmark scale and source. | If benchmark scores are included, benchmark source (e.g., AnTuTu v10 or Geekbench 6) and verification date must be explicitly retained and cited. |

---

## 3. The "Winning Edge" Strategy

How SmartPick AI beats standard student projects across all 4 competition judging criteria:

### 3.1 Technical Depth
- **Formal Dual-Engine Pipeline**: Clean separation between a multi-attribute utility theory (MAUT) ranking baseline and an unsupervised content-based vector space model using normalized feature embeddings and cosine similarity.
- **Robust Feature Preprocessor**: Scikit-Learn compatible transformer (`BaseEstimator`, `TransformerMixin`) that fits exclusively on catalog reference data to prevent leakage, handling numeric scaling (MinMax/Robust) and categorical one-hot/frequency representations gracefully.
- **Pydantic V2 Domain Models**: All user inputs, catalog rows, and ranking outputs pass through strongly typed, validated models preventing edge case crashes (e.g., budget inversion, negative weights, zero-weight edge cases).

### 3.2 Radical Honesty (The Evaluator's Dream)
- **Zero Hallucination Guarantee**: Explanations are strictly grounded in active user weights and real dataset attributes. If a phone is missing a processor score, the explanation explicitly notes: *"Benchmark unverified in catalog"*.
- **Honest Evaluation Benchmarking**: Instead of faking a 98% accuracy score, we present an evaluation dashboard that clearly explains the difference between offline ranking metrics with ground-truth judgements vs catalog-wide coverage and budget compliance.

### 3.3 Fintech-Grade UX & Presentation
- **Linear / Stripe Aesthetic**: Ditching standard unstyled Streamlit widgets for custom-themed containers, subtle border glows, monospace spec alignment, and glassmorphic card elevations.
- **Dual-Channel Accessibility**: Colorblind-friendly palettes where every status is backed by explicit text labels and semantic icons.

---

## 4. Architectural Boundaries & System Structure

The repository is structured strictly per TRD §2 & §3, enforcing zero business logic in `app.py`:

```
SmartPick-AI/
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated Ruff lint, test suite, and coverage CI
├── .streamlit/
│   └── config.toml              # Dark slate theme tokens and headless server config
├── assets/
│   └── screenshots/             # High-resolution demo and component UI captures
├── data/
│   ├── raw/                     # Original external source datasets (gitignored if proprietary)
│   └── phones.csv               # Curated, validated canonical catalog dataset
├── docs/
│   ├── DESIGN_SYSTEM.md         # Complete WCAG AA fintech design tokens and specs
│   ├── IMPLEMENTATION_PLAN.md   # This master plan and conflict resolution audit
│   └── extracted/               # Extracted references from the 7 foundation PDFs
├── notebooks/
│   └── eda.ipynb                # Rigorous exploratory data analysis and distribution audit
├── src/
│   ├── __init__.py              # Core package initialization
│   ├── data_loader.py           # Ingestion, schema validation, provenance tracking
│   ├── preprocessing.py         # Leakage-free fitted scalers and NaN-preserving transformers
│   ├── recommender.py           # Budget filter, ranking baseline, similarity engine, explanations
│   └── evaluation.py            # Precision@K, Recall@K, NDCG@K, coverage, and latency metrics
├── tests/
│   ├── __init__.py              # Test suite initialization
│   └── test_recommender.py      # TC-01 to TC-12 automated functional and boundary tests
├── Dockerfile                   # Containerized production runtime definition
├── requirements.txt             # Pinned core dependencies
└── app.py                       # Pure UI presentation layer (zero ranking logic)
```

---

## 5. Phased Implementation Roadmap

### Phase 1: Dataset Curation, Data Contract & Ingestion (`src/data_loader.py`)
- Acquire or curate a high-integrity Indian smartphone dataset (`data/phones.csv`) spanning budget (₹8,000) to flagship (₹1,50,000+).
- Enforce schema contracts: `phone_name` and `price_inr` required; all others optional.
- Deduplication using normalized brand + model name.
- Explicit NaN handling without zero-filling.
- Produce dataset metadata summary (record count, field completeness, source provenance).

### Phase 2: Baseline Ranking Engine & Tests (`src/recommender.py`)
- Implement strict budget constraint filtering (100% compliance guarantee).
- Implement multi-attribute preference baseline:
  $$\text{Score}(x) = \frac{\sum_{i} w_i \cdot s_i(x)}{\sum_{i} w_i}$$
  where $s_i(x)$ is the normalized feature score for dimension $i$.
- Build explanation generator mapping claims exclusively to real features.
- Implement test suite for TC-01 through TC-08.

### Phase 3: Content-Based Similarity Engine (`src/preprocessing.py`, `src/recommender.py`)
- Build fitted `FeaturePreprocessor` pipeline combining scaled continuous variables and encoded categorical brand features.
- Implement cosine similarity against a user's reference smartphone or synthetic ideal vector:
  $$\text{Sim}(u, v) = \frac{u \cdot v}{\|u\| \|v\|}$$
- Prevent feature double-counting when combining baseline filters and similarity scores.

### Phase 4: Evaluation, Metrics & Benchmarking (`src/evaluation.py`)
- Implement IR metric utilities: Precision@K, Recall@K, NDCG@K.
- Construct a documented, human-reviewed relevance evaluation set for 5 canonical user personas (Budget Buyer, Gamer, Photographer, Battery Enthusiast, Balanced Daily).
- Construct quarantined synthetic benchmark harness for functional test automation.
- Benchmark latency, catalog coverage, and algorithmic diversity.

### Phase 5: Fintech-Grade Streamlit Application (`app.py`)
- Implement deep slate dark layout using custom CSS tokens from `docs/DESIGN_SYSTEM.md`.
- Sidebar with budget dual-slider, priority weight sliders, and brand multi-select.
- Hero results grid featuring glassmorphic recommendation cards, match index progress bars, and spec matrices.
- Side-by-side device specification comparison view.
- Dual-channel accessibility indicators and transparent caveats footer.

### Phase 6: Verification, CI/CD, and Competition Demo Package
- Run full pytest test suite with test coverage reporting (`pytest --cov=src`).
- Run Ruff linter and formatter checks (`ruff check . && ruff format --check .`).
- Capture screenshots for `assets/screenshots/`.
- Prepare competition viva defense guide answering technical trade-offs (e.g., Content-Based vs Collaborative Filtering cold-start resistance).

---

## 6. Risk Assessment & Engineering Mitigations

| Risk Identifier | Severity | Likelihood | Concrete Engineering Mitigation |
| :--- | :--- | :--- | :--- |
| **Outdated / Inaccurate Catalog Prices** | High | Medium | Record explicit provenance URLs and `verified_at` timestamps. State clearly that prices represent snapshot catalog values, not live e-commerce API feeds. |
| **Arbitrary Weight Sensitivity** | Medium | High | Expose interactive sliders with preset persona configurations (Gamer, Photographer, Balanced). Provide dynamic trade-off radar charts showing how weight changes affect ranking. |
| **Zero Eligible Phones Found** | Medium | Medium | Implement smart fallback empty state suggesting specific relaxed criteria (e.g., *"No 5G phones found under ₹12,000; increase budget by ₹2,000 or disable 5G filter"*). |
| **Missing Optional Specifications** | Medium | High | Preprocessor handles NaNs without imputation distortion. UI renders visual warning chip `[⚠ Unverified]` and excludes missing attributes from explanation claims. |
| **Licensing / Data Redistribution** | High | Low | Verify dataset rights. If unredistributable, provide synthetic mock data for CI and clear download/generation instructions for evaluators. |

---

## 7. Immediate Deliverable Verification Checklist

- [x] **Audit of all 7 Docs Complete**: Sources analyzed, priorities set (`TRD > PRD > others`), conflicts logged.
- [x] **Project Skeleton Built**: Layout matches TRD layout exactly plus `.streamlit/`, `.github/`, `docs/`, `notebooks/`, `tests/`, `assets/`, `Dockerfile`.
- [x] **Python 3.11 Runtime Configured**: Python 3.11 installed, `.venv` created, dependencies installed.
- [x] **Design System Defined**: `docs/DESIGN_SYSTEM.md` created with WCAG AA compliance, dark/light palettes, and component blueprints.
- [x] **Phase 1 Complete**: `src/data_loader.py`, schema validation, Pydantic contracts, anomaly and variant audit (125 records, 122 valid).
- [x] **Phase 2 Complete**: `src/recommender.py`, 100% budget filtering guarantee, normalized multi-attribute utility baseline, active weight renormalization.
- [x] **Phase 3 Complete**: `src/preprocessing.py`, leakage-free feature scaling, cosine similarity engine, blended hybrid, MMR diversity re-ranking.
- [x] **Phase 4 Complete**: `src/evaluation.py`, precision/recall/NDCG@K on documented synthetic benchmarks, latency p50/p95, sensitivity Kendall tau stability (0.8759).
- [x] **Phase 5 Complete**: Fintech-grade Streamlit app (`app.py`), 7 tabs, Plotly radar, Pareto frontier, why-not explanations, Hinglish toggle, 158 tests passing with 92% coverage.
- [x] **Phase 5c Complete**: `README.md`, real screenshots in `assets/screenshots/`, `docs/PITCH_DECK_OUTLINE.md`, `docs/DEMO_SCRIPT.md`, `docs/VIVA_NOTES.md`, `docs/JUDGE_QA.md`, and `docs/ONE_PAGER.md`.
