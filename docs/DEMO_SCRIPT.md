# SmartPick AI — 5-Minute Timed Live Demo Script

**Presenter**: Pratyush Mishra  
**Target Duration**: Exactly 5 Minutes (300 Seconds)  
**Tone**: Confident, Methodical, Engineering-Driven, Radically Honest  
**Prerequisites Check**: App running locally at `http://localhost:8501`, Chrome or Edge open in full screen (F11), dark theme active.

---

## ⏱️ Timeline Breakdown

```
00:00 ─── [0:45] ─── User Profile & Strict Budget Setup
00:45 ─── [1:00] ─── Top-5 Results & Mathematically Grounded Explanation
01:45 ─── [1:00] ─── What-If Analysis & Dynamic Preference Perturbation
02:45 ─── [1:00] ─── Side-by-Side Comparison (Radar Chart & Pareto Frontier)
03:45 ─── [0:45] ─── Radical Honesty: Limitation Disclosures
04:30 ─── [0:30] ─── Future Work & Seamless Viva Handover
05:00 ─── END
```

---

## 🎬 Section 1: User Profile & Budget Constraints (0:00 – 0:45)

### Screen Action:
- Open `http://localhost:8501`.
- Point cursor to the top hero: highlight the **Curated Catalog v1.0** freshness badge (125 records, 122 valid).
- In the sidebar, set the dual-slider budget window to **₹15,000 – ₹25,000**.
- Click the **🎓 Student** preset button.

### Presenter Script:
> *"Respected judges, let us begin with a realistic consumer scenario: a college student with a hard budget of ₹15,000 to ₹25,000 looking for an all-round smartphone that offers maximum hardware value and dependable battery life for long days on campus.
> Notice our first core differentiator in the sidebar: budget is an absolute, deterministic hard boundary. In SmartPick AI, 100% of candidate phones satisfy this ₹15,000 to ₹25,000 window—no device at ₹25,999 will ever slip through.
> By clicking our documented 'Student' preset, the system instantly sets our value-for-money weight to 0.90, battery weight to 0.80, and balances performance and display. All weights are transparently visible in the UI."*

---

## 🎬 Section 2: Recommendations & Transparent Explanations (0:45 – 1:45)

### Screen Action:
- Point to the **#1 Top Match** recommendation card.
- Highlight the **Match Index progress bar (e.g. 84%)**.
- Highlight the spec pill matrix: RAM, Storage, Battery, Refresh Rate, AnTuTu Processor Score.
- Point to the explanation text below the card.

### Presenter Script:
> *"Instantly, our recommendation pipeline scores all eligible candidates. Notice our #1 ranked device. 
> Crucially, look at the Match Index: we explicitly tell the user that 84% is a mathematical preference alignment index relative to their active weights—it is not an arbitrary user review score or a fabricated probability.
> Notice the explanation below the card: every claim is directly grounded in real catalog fields. If a device is missing a benchmark score, our pipeline never hallucinates or converts it to zero; instead, it renders an explicit warning chip and renormalizes the scoring denominator.
> Furthermore, users can click 'Export CSV' or 'Export Report' to download an executive specification breakdown immediately."*

---

## 🎬 Section 3: "What-If" Perturbation & Ranking Movement (1:45 – 2:45)

### Screen Action:
- Move cursor to the sidebar sliders.
- Drag the **Performance / Gaming** slider from `0.50` up to `1.00`.
- Reduce the **Battery** slider from `0.80` down to `0.30`.
- Show the live rerun and observe the top rank shift.
- Navigate to **Tab 4: "Why Not This Phone?"**.
- Select a lower-ranked or out-of-budget phone (e.g. OnePlus 12 or Samsung Galaxy S24) in the dropdown.

### Presenter Script:
> *"Now, let's test how the engine behaves under preference perturbation—the 'What-If' test. Suppose our student starts playing competitive mobile games and shifts their performance priority to maximum (1.00) while deprioritizing battery.
> Notice how smoothly the leaderboard re-ranks. Devices with higher AnTuTu benchmark scores and 120Hz/144Hz AMOLED displays surge forward. In our empirical sensitivity study, ranking stability achieves a high mean Kendall's tau of 0.8759.
> Next, let's open Tab 4: 'Why Not This Phone?'. When a consumer asks 'Why wasn't the Samsung Galaxy S24 recommended to me?', standard tools say nothing. SmartPick AI performs a counterfactual gap analysis: it shows that the device exceeded the maximum budget by ₹35,000, and displays the exact dimensional score deltas."*

---

## 🎬 Section 4: Deep Comparison & Pareto Efficiency Frontier (2:45 – 3:45)

### Screen Action:
- Click **Tab 2: "Compare Devices"**.
- Select the #1 and #2 recommended phones.
- Point to the side-by-side spec matrix, then scroll down to the **Plotly Interactive Radar Chart**.
- Click **Tab 3: "Pareto Frontier"**.
- Highlight the non-dominated curve (Price vs. Match Score).

### Presenter Script:
> *"To eliminate buyer's remorse, we provide formal multi-criteria decision tools. 
> In Tab 2, our side-by-side comparison displays our interactive Plotly Radar Chart. The student can immediately see the shape of the trade-off: Device A might have 20% higher processor throughput, but Device B offers 1,000 mAh more battery capacity for ₹2,000 less.
> Moving to Tab 3, we plot the Pareto Efficiency Frontier. In multi-objective optimization, a point is Pareto-optimal if no other device offers higher score for equal or lower price. Points on this upper-left envelope represent the most rational purchases in the entire catalog."*

---

## 🎬 Section 5: Radical Honesty & Limitations (3:45 – 4:30)

### Screen Action:
- Scroll down to the persistent **Caveat Footer** at the bottom of the page.
- Switch the language toggle to **Hinglish** to show bilingual accessibility.
- Point to the **[⚠ Camera Caveat]** chip.

### Presenter Script:
> *"Now, I want to address the limitations of our implementation with total honesty—which is where we believe our project demonstrates the highest engineering maturity.
> First, our camera dimension uses primary sensor megapixels as a proxy. We explicitly note in the UI that 50 megapixels does not equal high camera quality; sensor size, optical stabilization (OIS), and image signal processing matter greatly. We do not claim what our dataset cannot prove.
> Second, our offline catalog represents verified snapshots, not live e-commerce inventory feeds.
> And third, our information retrieval metrics (NDCG@5 = 0.122, Precision@5 = 0.16) are evaluated against a documented synthetic benchmark set of 5 canonical personas. In offline recommender literature, claiming 98% accuracy without real clickstream logs is unscientific. We present verifiable engineering reality."*

---

## 🎬 Section 6: Future Work & Viva Transition (4:30 – 5:00)

### Screen Action:
- Click **Tab 7: "About & Data Dictionary"** to show complete architectural contracts and mathematical formulations.
- Face the judges with confidence.

### Presenter Script:
> *"Our immediate roadmap includes integrating live retailer APIs via webhooks, crowdsourcing India's first open-source smartphone relevance dataset with 500+ student evaluators, and deploying our natural language query parser.
> SmartPick AI has 158 automated tests passing, 92% statement coverage, 100% budget adherence, and zero fabricated claims.
> Thank you, respected judges. I am ready for your questions."*

---

## 🚨 Robust Fallback Protocol (If Murphy's Law Strikes)

| Failure Scenario | Immediate Action & Mitigation | Presenter Spoken Pivot |
| :--- | :--- | :--- |
| **Port 8501 is Busy or Streamlit Fails to Start** | Run on alternate port: `streamlit run app.py --server.port 8502` | *"I am switching to our secondary backup port 8502."* |
| **Browser Fails / Display Freezes** | Open captured high-res screenshots in `assets/screenshots/` (`home.png`, `compare.png`, `what-if.png`). | *"While our browser refreshes, let me guide you through the high-resolution architectural captures from our verified test run."* |
| **Judges Challenge a Calculation** | Open terminal and execute: `pytest tests/test_recommender.py -v` | *"Allow me to run our automated test suite live to verify the mathematical contracts on screen in real time."* |
| **No Internet Connection** | Entire architecture is 100% offline; zero external API or CDN dependencies required. | *"SmartPick AI is intentionally architected as a zero-dependency offline system—no internet is required."* |
| **Judges Ask for Source Code Verification** | Open [src/recommender.py](file:///c:/Users/HP/OneDrive/Desktop/SmartPick-AI/src/recommender.py) and show lines 210–250 (budget filtering & dynamic renormalization). | *"Here is the exact implementation of our deterministic budget filter and weight renormalization formula."* |
