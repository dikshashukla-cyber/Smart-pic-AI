# SmartPick AI — Security and Privacy Architecture Review

**Date**: October 2026  
**Document Version**: 1.0  
**Scope**: Production hardening, data privacy compliance, threat modeling, and ethical data governance.

---

## 1. Executive Summary & Philosophy

SmartPick AI is designed as a **privacy-first, zero-knowledge decision support system**. The platform operates on the core principle that users should be empowered to explore smartphone options without sacrificing their personal privacy, surrendering identifiable information, or being tracked by commercial ad networks.

### Core Security Guarantees
- 🔒 **Zero Personal Data Collection**: No user accounts, logins, cookies, or telemetry tracking.
- 🔑 **Zero Secrets Required**: Local heuristic ranking requiring zero cloud API keys, tokens, or external RPC calls.
- 🛡️ **Defensive File I/O**: Safe path resolution and strict schema enforcement preventing path traversal or untrusted code execution.
- 🚫 **No Live Scraping**: Complete avoidance of unauthorized runtime scraping or bot traffic against retail platforms.
- 📜 **Dataset Licensing Compliance**: Strict attribution and non-redistribution compliance.

---

## 2. Privacy Review: Zero Personal Data Collection

### 2.1 Absence of Personally Identifiable Information (PII)
SmartPick AI collects, stores, and transmits **zero PII**:
- No names, email addresses, phone numbers, or physical locations are requested or accepted.
- No device fingerprinting, canvas hashing, or advertising identifiers (IDFA/GAID) are generated.
- No session cookies or persistent tracking tokens are stored in the user's browser.

### 2.2 Ephemeral In-Memory State Lifecycle
User interactions operate exclusively within volatile execution environments:
1. **Budget & Sliders**: Stored strictly within Streamlit's ephemeral `st.session_state`, residing solely in host process RAM during active browsing.
2. **Sharable URLs**: When users configure custom criteria, filters are serialized as human-readable query parameters (e.g. `?min_budget=15000&max_budget=30000`). This allows users to bookmark or share profiles without sending data to any backend persistence layer.
3. **Session Termination**: Closing the browser tab terminates the connection and purges the in-memory session state completely.

### 2.3 Regulatory Compliance
SmartPick AI adheres to global and national privacy regulations by architectural design (Privacy by Design):
- **Digital Personal Data Protection Act (DPDPA 2023, India)**: Full compliance achieved through total exemption from processing personal digital data.
- **GDPR (EU 2016/679)**: Adheres strictly to Article 5 principles:
  - *Data Minimization*: Zero data collected.
  - *Purpose Limitation*: Recommendation engine evaluates phone specs, not user traits.
  - *Storage Limitation*: Zero persistent databases.

---

## 3. Secret Management & Credential Hygiene

### 3.1 Zero Third-Party Cloud Dependencies
SmartPick AI's recommender, Pareto efficiency frontier engine, and similarity modules execute **100% locally on the host machine**:
- No proprietary LLM API keys (OpenAI, Anthropic, Gemini API keys) are required for core recommendation generation.
- No third-party analytics or tracker scripts (Google Analytics, Mixpanel, Hotjar) are embedded in HTML templates.

### 3.2 Secret Scanning & CI Enforcement
- The repository is actively scanned during CI via `ruff` and automated pre-commit hooks to detect accidental API key, token, or password commits.
- `.env` and `.env.*` patterns are strictly ignored by `.gitignore` and `.dockerignore`.

---

## 4. Secure File Handling & Input Sanitization

### 4.1 Path Traversal Prevention
File ingestion via `DataLoader` and `QualityReportGenerator` strictly verifies all target paths:
- All file targets are resolved using `pathlib.Path.resolve()`.
- Relative directory escape sequences (e.g. `../../etc/passwd` or `..\..\Windows\System32`) are rejected prior to filesystem access.
- Ingestion adapters only read files situated within the project's designated `data/` directory.

### 4.2 Strong Schema Validation with Pydantic
Catalog parsing rejects malformed, corrupted, or hostile inputs:
- Every CSV row is ingested through `DataRowSchema` in [`src/ingest.py`](file:///c:/Users/HP/OneDrive/Desktop/SmartPick-AI/src/ingest.py).
- Unrecognized or non-numeric inputs for numeric attributes (`price_inr`, `battery_mah`, `ram_gb`) are safely parsed or converted to explicit `np.nan` (missing values are never silently coerced to 0).
- Extreme or implausible specification values (e.g., negative prices, 50,000 mAh batteries) are flagged by the `QualityReportGenerator` validation pipeline.

### 4.3 Safe Artifact Serialization
- Outlier scaling bounds and metadata are serialized via `joblib` into [`artifacts/preprocessor.joblib`](file:///c:/Users/HP/OneDrive/Desktop/SmartPick-AI/artifacts/preprocessor.joblib).
- Serialization is performed strictly internally by the application during initialization. External, untrusted serialized pickles are prohibited from loading.
- If the artifact is missing or corrupted, the application automatically refits the preprocessor from the canonical catalog rather than failing ungracefully.

---

## 5. Ethical Data Governance & Zero Scraping

### 5.1 No Runtime Web Scraping
SmartPick AI deliberately avoids runtime web scraping:
- **No Headless Crawlers**: The production application contains zero Selenium, Playwright, or BeautifulSoup scripts querying live retail portals.
- **Respect for Terms of Service**: Live e-commerce websites (Amazon, Flipkart, brand stores) prohibit automated bot harvesting. SmartPick AI does not scrape live pricing or customer reviews.
- **Offline Canonical Ingestion**: All catalog data is pre-ingested, validated, and normalized offline into static, checksum-verified CSV snapshots.

### 5.2 Anti-Hallucination & Honesty Policy
In compliance with the project's **Honesty Rules**:
- The engine **never invents missing specifications**. If a camera sensor resolution or refresh rate is omitted in the raw catalog, it remains `NaN`.
- Derived metrics (such as the spec-to-price value index or composite hardware score) are explicitly labelled as **derived heuristics**, never presented as official manufacturer benchmarks or quality ratings.
- Recommendation explanations reference **only real catalog fields** and the user's active weights.

---

## 6. Security & Vulnerability Reporting

If any vulnerability, unintended data leakage, or dependency flaw is discovered in this codebase, please submit an issue or security advisory detailing:
1. Module affected and version/commit hash.
2. Reproduction steps and proof of concept.
3. Recommended remediation.
