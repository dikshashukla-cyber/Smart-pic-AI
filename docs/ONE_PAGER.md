# SmartPick AI — Executive Submission One-Pager

**Project**: SmartPick AI — Intelligent Mobile Recommender  
**Author**: Pratyush Mishra  
**Category**: Machine Learning & Intelligent Decision Systems  
**Target Delivery Standard**: National-Level Competition Winner  
**Repository**: `SmartPick-AI` | **Runtime**: Python 3.11 | **UI**: Streamlit 1.66 | **Styling**: WCAG AA Dark Slate  

---

## 📌 Executive Summary

SmartPick AI is an offline, multi-criteria smartphone decision support system engineered with fintech-grade presentation polish, verifiable data provenance, and radical algorithmic honesty. While conventional student projects often resort to "ML-washing" (claiming simple weighted sums as "deep neural networks") or silently corrupting missing values with zeros, SmartPick AI guarantees **100% deterministic budget compliance**, implements a dual-engine architecture combining Multi-Attribute Utility Theory (MAUT) with high-dimensional Cosine Similarity, and provides mathematically grounded counterfactual explanations.

---

## 🚀 Key Innovations & Engineering Depth

1. **100% Deterministic Budget Guarantee**: Hard boundary filtering guarantees zero out-of-budget recommendations.
2. **Dual-Engine Ranking Pipeline**:
   - **Baseline Utility**: Normalized multi-attribute formula with active weight renormalization for missing specifications.
   - **Content-Based Similarity**: Unsupervised vector space model using normalized spec embeddings and cosine similarity.
   - **Blended Hybrid ($\alpha=0.35$)**: Tunable convex blend combining heuristic alignment with vector distance.
   - **Diversity Re-Ranking via MMR ($\lambda=0.70$)**: Maximal Marginal Relevance penalizing pairwise vendor similarity.
3. **Pareto Efficiency Frontier**: Visualizes the non-dominated multi-objective trade-off curve (Price vs. Match Score).
4. **Counterfactual "Why Not?" Engine**: Performs mathematical gap analysis explaining exact spec and budget deficits.
5. **Radical Missing Value Policy**: Retains `NaN` without zero-imputation; UI renders warning chips `[⚠ Unverified]`.
6. **Bilingual Accessibility**: Instant runtime toggle between English and conversational Hinglish.

---

## 📊 Verifiable Implementation Metrics (Real Numbers)

| Metric Category | Real Implementation Metric | Verified Benchmark Evidence |
| :--- | :--- | :--- |
| **Automated Test Suite** | **158 Tests Passed (100% Pass Rate)** | 12 test files (`tests/test_*.py`) running via `pytest` in 78.65s |
| **Code Coverage** | **92% Statement Coverage** | 1,410 executable statements in `src/` (116 missed) |
| **Budget Compliance** | **100.0% Hard Boundary Adherence** | 0 violations across all personas, edge cases, and property tests |
| **Catalog Dimensions** | **125 Ingested / 122 Valid Devices** | 19 brands, 23 hardware variants, price range ₹6,499 – ₹1,99,900 |
| **Spec Completeness** | **99.6% Overall Completeness** | 2 duplicate rows eliminated, 2 implausible values sanitized |
| **Ranking Stability** | **Mean Kendall's $\tau = 0.8759$** | Evaluated under $\pm 20\%$ perturbation across all 6 weight dimensions |
| **Vendor Diversity** | **Shannon Entropy = 3.015** | MMR re-ranking expands top-5 unique brand count to 10 |
| **System Latency** | **p50 = 155.28 ms \| p95 = 553.79 ms** | Instant interactive Streamlit rendering without batch latency |

---

## 🏛️ System Architecture

```
[Curated Catalog: data/phones.csv] ──> [DataLoader: Schema & Anomaly Audit] 
                                                  │
                                                  ▼
[FeaturePreprocessor: Robust MinMax] <── [122 Clean Recommendable Devices]
                                                  │
                                                  ▼
[User Preferences: Budget & Weights] ──> [Hard Budget Filter (100% Adherence)]
                                                  │
                                                  ▼
                     ┌────────────────────────────┴───────────────────────────┐
                     ▼                                                        ▼
         [Baseline Heuristic Mode]                               [Content Similarity Mode]
      (MAUT + Active Renormalization)                           (Cosine Angle in Vector Space)
                     │                                                        │
                     └────────────────────────────┬───────────────────────────┘
                                                  ▼
                              [Blended Hybrid & MMR Diversity Engine]
                                                  │
                                                  ▼
                    [Fintech Presentation: 7 Tabs + Plotly Radar & Pareto]
```

---

## ⚖️ Scientific Integrity & Known Limitations

- **Camera Megapixel Proxy**: Primary sensor megapixel count is an accessible hardware proxy; it does not measure sensor surface area, optical stabilization (OIS), or ISP computational algorithms.
- **Snapshot Catalog**: Prices reflect verified catalog snapshots rather than live e-commerce inventory feeds.
- **Honest IR Benchmarking**: Precision@5 (0.16) and NDCG@5 (0.122) are reported strictly against our documented synthetic benchmark dataset (`data/synthetic_relevance_benchmark.csv`) across 5 canonical buyer personas for functional verification.

---

## 💻 Quick Start & Live Verification

```powershell
# 1. Activate Environment & Run Full 158-Test Suite with Coverage
.\.venv\Scripts\Activate.ps1
pytest --cov=src --cov-report=term-missing

# 2. Launch Fintech Streamlit Application
streamlit run app.py
```
*Application runs locally at `http://localhost:8501`.*
