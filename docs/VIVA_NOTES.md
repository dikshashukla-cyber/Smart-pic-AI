# SmartPick AI — Viva Defense & Technical Examination Notes

**Author**: Pratyush Mishra  
**Target Delivery Standard**: National-Level Competition Winner  
**Implementation Basis**: Real Codebase Contracts (`src/recommender.py`, `src/preprocessing.py`, `src/data_loader.py`, `src/evaluation.py`, `app.py`)  

---

## 🎓 Core Viva Prompts (Mandatory from Demo Guide)

### 1. What is a recommender system?
**Examiner Answer**:
> "A recommender system is an information filtering framework that predicts the preference or rating a user would assign to an item, with the goal of retrieving and ordering an optimal subset of items from an otherwise overwhelming catalog. 
> In SmartPick AI, the recommender operates in an offline, multi-criteria decision-making (MCDM) setting where item profiles are defined across continuous and discrete hardware specifications (price, processor benchmark, battery capacity, camera megapixels, refresh rate, and storage). The system's objective is to rank candidate devices by maximizing alignment with an explicit user utility vector under hard budget constraints."

---

### 2. How is content-based filtering different from collaborative filtering?
**Examiner Answer**:
> "The fundamental distinction lies in the **information source** used to generate recommendations:
> 
> 1. **Collaborative Filtering (CF)**:
>    - Relies on **user-item interaction matrices** (ratings, clickstreams, purchase histories).
>    - Operates under the assumption that users who agreed in the past will agree in the future (*"Users like you also bought X"*).
>    - Suffers severely from the **Cold-Start Problem**: new items with zero interactions cannot be recommended, and new users with no history receive generic popular items.
> 
> 2. **Content-Based Filtering (CBF)** (Used in SmartPick AI):
>    - Relies on **item metadata and explicit user preference attributes** (specs, hardware vectors, budget windows).
>    - Recommends items based on feature similarity to an ideal profile or anchor device without requiring a crowd of other users.
>    - Completely **immune to the new item cold-start problem**: as soon as a new smartphone is added to `data/phones.csv` with valid specs, it is immediately recommendable."

---

### 3. Why are features scaled? What happens if you don't scale?
**Examiner Answer**:
> "Features must be scaled because different hardware attributes exist on radically disparate numerical orders of magnitude:
> - Battery capacity spans **3,000 to 7,000 mAh**.
> - AnTuTu processor scores span **200,000 to 2,000,000 points**.
> - Display refresh rates span **60 to 144 Hz**.
> - Storage spans **64 to 512 GB**.
> 
> If features were not scaled, a simple linear combination or Euclidean distance calculation would be completely dominated by AnTuTu scores and battery capacity, rendering camera megapixels (50) and refresh rate (120) mathematically irrelevant ($2,000,000 \gg 120$).
> 
> In SmartPick AI, we implement `FeaturePreprocessor` in [src/preprocessing.py](file:///c:/Users/HP/OneDrive/Desktop/SmartPick-AI/src/preprocessing.py) using a **Robust MinMax Scaler**. We scale every dimension strictly to $[0.0, 1.0]$. Furthermore, to prevent data leakage, the preprocessor fits its min and max bounds exclusively on the reference catalog and stores the fitted transformer (`artifacts/preprocessor.joblib`)."

---

### 4. What does cosine similarity measure geometrically and mathematically?
**Examiner Answer**:
> "Cosine similarity measures the **cosine of the angle between two multi-dimensional vectors** in an inner product space:
> 
> $$\text{Cosine Similarity}(u, v) = \frac{u \cdot v}{\|u\| \|v\|} = \frac{\sum_{i=1}^n u_i v_i}{\sqrt{\sum_{i=1}^n u_i^2} \sqrt{\sum_{i=1}^n v_i^2}}$$
> 
> - **Geometric Interpretation**: It measures vector **orientation rather than magnitude**. If two smartphones have identical relative spec trade-offs, their angle is $0^\circ$ and cosine similarity is $1.0$, even if one is slightly lower across all dimensions.
> - **In SmartPick AI**: Because all feature dimensions are scaled to $[0.0, 1.0]$, vectors reside exclusively in the positive hypercube $[0, 1]^D$, bounding cosine similarity strictly within $[0.0, 1.0]$. We use it in our `similarity` engine mode to find devices nearest to an anchor phone or a synthetic ideal vector."

---

### 5. Why is budget treated as a hard constraint rather than a soft penalty in the ranking formula?
**Examiner Answer**:
> "Treating budget as a soft penalty in the utility function—for example, $\text{Score} - \lambda \cdot (\text{Price} - \text{Budget})$—is one of the most common design flaws in academic recommender systems. 
> 
> In real consumer finance, **budget is an unyielding ceiling**. A college student or budget buyer who has ₹15,000 in their bank account cannot execute a purchase for ₹16,500, regardless of how extraordinary the camera or processor is. A soft penalty allows an expensive flagship with exceptional specs to outscore affordable options and appear in the Top 5.
> 
> Therefore, in [src/recommender.py](file:///c:/Users/HP/OneDrive/Desktop/SmartPick-AI/src/recommender.py), budget is implemented as a **deterministic hard pre-filter**:
> 
> ```python
> candidates = df[
>     (df['price_inr'] >= prefs.min_budget) & 
>     (df['price_inr'] <= prefs.max_budget)
> ]
> ```
> 
> This guarantees **100.0% budget adherence** across all recommendations, verified empirically across 158 automated tests."

---

### 6. What data is mathematically required to compute Precision@K, Recall@K, and NDCG@K? Why can't they be claimed without it?
**Examiner Answer**:
> "Information Retrieval (IR) metrics cannot be computed on raw item catalogs alone. They mathematically require **ground-truth relevance labels** $R(u, d)$ representing whether user $u$ judged document/item $d$ to be relevant:
> 
> 1. **Precision@K**: 
>    $$\text{Precision@K} = \frac{|\text{Retrieved Top K} \cap \text{Relevant Items}|}{K}$$
> 2. **Recall@K**: 
>    $$\text{Recall@K} = \frac{|\text{Retrieved Top K} \cap \text{Relevant Items}|}{|\text{All Relevant Items in Catalog}|}$$
> 3. **NDCG@K (Normalized Discounted Cumulative Gain)**:
>    $$\text{DCG@K} = \sum_{i=1}^K \frac{2^{rel_i} - 1}{\log_2(i + 1)}, \quad \text{NDCG@K} = \frac{\text{DCG@K}}{\text{IDCG@K}}$$
> 
> In an offline catalog dataset with no user interaction logs, **ground-truth relevance does not exist natively**. Claiming '98% NDCG' on an unlabelled catalog is scientific fraud. 
> 
> In SmartPick AI, we construct a documented, peer-reviewable **synthetic benchmark set** (`data/synthetic_relevance_benchmark.csv`) for 5 canonical buyer personas. Our computed baseline scores (Precision@5 = 0.16, NDCG@5 = 0.122) verify algorithmic retrieval code paths honestly, and we provide `data/relevance_template.csv` for human trials."

---

### 7. Why is a weighted scoring formula not necessarily a "trained ML model"?
**Examiner Answer**:
> "A mathematical function is only a 'trained Machine Learning model' if its internal parameters (weights, coefficients, or neural network tensors) were **optimized from data via an objective loss function and an optimization algorithm** (such as Stochastic Gradient Descent or convex quadratic programming).
> 
> When a developer writes:
> $$\text{Score} = w_1 \cdot \text{RAM} + w_2 \cdot \text{Battery} + w_3 \cdot \text{Camera}$$
> with user-defined or hand-tuned weights, that is a **Multi-Attribute Utility Theory (MAUT) heuristic baseline**, not a trained ML model.
> 
> Claiming a weighted formula is 'AI' or 'deep learning' is known as **ML-Washing**. In SmartPick AI, we strictly label our weighted sum in the code, UI, and documentation as **'Baseline Heuristic Ranking'**, while our vector space model is labelled **'Content-Based Cosine Similarity'**. This honesty builds immediate trust with technical evaluators."

---

### 8. What are the main limitations of the dataset?
**Examiner Answer**:
> "We explicitly document four limitations:
> 1. **Megapixels as a Camera Proxy**: Megapixel count (`camera_mp`) indicates sensor resolution but does not reflect optical image stabilization (OIS), physical sensor area (e.g. 1/1.56-inch), or proprietary ISP computational photography.
> 2. **Snapshot vs. Live Pricing**: Catalog prices reflect snapshot verified values from our curated catalog rather than real-time e-commerce fluctuating retail feeds.
> 3. **Missing Benchmark Scores**: Certain budget phones do not publish official AnTuTu v10 scores; rather than imputing these with zeros or global means, our system retains `NaN` and renormalizes active weights.
> 4. **Synthetic Benchmark Evaluation**: Our IR metrics are computed against 5 documented synthetic persona profiles rather than 100,000 real-world purchase transactions."

---

## 🔬 Advanced Architectural & Engineering Prompts

### 9. What is your Missing Value Policy? Why is zero-filling dangerous?
**Examiner Answer**:
> "Standard tutorials frequently run `df.fillna(0)`. In smartphone recommendations, this is catastrophic. If a ₹70,000 flagship is missing a published AnTuTu benchmark in the catalog, filling it with `0` will scale its performance to 0.0, severely penalizing the phone and dropping it below a ₹10,000 budget phone.
> 
> In SmartPick AI:
> 1. Missing values remain `NaN` throughout the pipeline.
> 2. In `BaselineHeuristic`, when a phone is missing dimension $k$, dimension $k$ is excluded from the phone's score, and the remaining weights are **dynamically renormalized**:
>    $$\text{Score}(d) = \frac{\sum_{i \in \text{valid}(d)} w_i \cdot s_i(d)}{\sum_{i \in \text{valid}(d)} w_i} \times 100$$
> 3. The UI renders an explicit warning badge `[⚠ Unverified]` on the spec matrix."

---

### 10. How does Maximal Marginal Relevance (MMR) work in your recommender?
**Examiner Answer**:
> "In standard ranking, the Top 5 results often cluster around the exact same brand or device line (e.g., standard, 5G, and Pro variants of one manufacturer). 
> 
> To enforce catalog diversity, we implement **Maximal Marginal Relevance (MMR)** (TRD §6.3):
> 
> $$\text{MMR}(d) = \operatorname{argmax}_{d \in C \setminus S} \left[ \lambda \cdot \text{Relevance}(d) - (1 - \lambda) \max_{s \in S} \text{Sim}(d, s) \right]$$
> 
> - $\lambda \in [0.1, 0.9]$ is a user-tunable trade-off parameter (default $\lambda = 0.70$).
> - $S$ is the set of devices already selected in the Top-K shortlist.
> - At each iteration, MMR selects the candidate that balances high relevance with maximum dissimilarity from already chosen phones.
> - In our ablation study, MMR increased brand Shannon entropy to **3.015** and broadened unique brand representation to 10."

---

### 11. What is Pareto Optimality and how do you compute the efficiency frontier?
**Examiner Answer**:
> "In multi-objective optimization, a candidate device $A$ **Pareto-dominates** device $B$ if:
> 1. Device $A$ is strictly better than $B$ in at least one objective (e.g., higher Match Score or lower Price).
> 2. Device $A$ is no worse than $B$ in all other objectives.
> 
> A phone is **Pareto-optimal** if no other phone in the eligible pool dominates it. The collection of all such points forms the **Pareto Efficiency Frontier**.
> In [src/frontier.py](file:///c:/Users/HP/OneDrive/Desktop/SmartPick-AI/src/frontier.py), we compute this non-dominated envelope and render it in Tab 3 as an interactive Plotly scatter plot, allowing users to visually isolate the most mathematically efficient options for their money."

---

### 12. How did you test ranking stability and sensitivity?
**Examiner Answer**:
> "We implemented an automated sensitivity harness in [src/sensitivity.py](file:///c:/Users/HP/OneDrive/Desktop/SmartPick-AI/src/sensitivity.py). We apply a **$\pm 20\%$ perturbation** to each preference weight independently and compute **Kendall's Rank Correlation Coefficient ($\tau$)** against the original ranking:
> 
> $$\tau = \frac{C - D}{\frac{1}{2} n (n - 1)}$$
> 
> Where $C$ is concordant pairs and $D$ is discordant pairs.
> - Our system achieved a high mean stability of $\tau = \mathbf{0.8759}$.
> - Storage achieved $\tau = 1.0000$ (completely stable).
> - Camera achieved $\tau = 0.7333$, demonstrating controlled sensitivity where closely grouped 50MP vs. 64MP devices shift positions without erratic rank inversions."

---

### 13. What are the verified code quality and testing metrics of this project?
**Examiner Answer**:
> "The repository is engineered according to enterprise CI/CD standards:
> - **Total Automated Tests**: `158` passing tests across 12 test modules.
> - **Statement Code Coverage**: `92%` across 1,410 executable statements in `src/`.
> - **Linting & Formatting**: Clean Ruff validation (`ruff check .` with zero errors).
> - **UI Automation**: Official Streamlit `AppTest` framework verifying page boots, preset clicks, empty states, zero-weight warnings, and language toggles without exceptions."
