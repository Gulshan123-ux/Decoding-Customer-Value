# Decoding Customer Value: SQL Retention Playbook

> **Consulting & Analytics Club — IIT Guwahati**  
> D2C Fashion Brand · RFM Segmentation · SQL-First Approach

---

## Project Structure

```
decoding-customer-value/
├── data/
│   └── online_retail_II.xlsx        ← Place dataset here (link in PDF)
├── outputs/
│   ├── 01_cleaned_features.csv      ← Engineered features per customer
│   ├── 02_segment_profile.csv       ← Segment-level KPI summary
│   ├── 04_retention_playbook.md     ← Full campaign playbook
│   ├── 04_executive_summary.md      ← 1-page executive brief
│   └── plots/
│       ├── dashboard_overview.png
│       ├── dashboard_deepdive.png
│       ├── loyalty_definitions.png
│       └── retention_playbook.png
├── sql/
│   └── 03_segmentation_queries.sql  ← All 5 SQL business questions
├── 01_data_preparation.py           ← Step 1: Clean + Feature Engineering
├── 02_rfm_segmentation.py           ← Step 2: RFM Scores + Charts
├── 04_retention_playbook.py         ← Step 4: Playbook + Executive Summary
├── run_all.py                       ← Master runner
├── requirements.txt
└── README.md
```

---

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place dataset
#    Download from the link in Problem Statements PDF
#    Save as: data/online_retail_II.xlsx

# 3. Run full pipeline
python run_all.py

# Or run individual steps
python 01_data_preparation.py
python 02_rfm_segmentation.py
python 04_retention_playbook.py
```

---

## Deliverables

| # | Deliverable | File | Description |
|---|-------------|------|-------------|
| 1 | **Python** | `outputs/01_cleaned_features.csv` | Cleaned dataset with dependency score, value tier, satisfaction flag |
| 2 | **SQL** | `sql/03_segmentation_queries.sql` | 5 queries answering all key business questions |
| 3 | **Charts** | `outputs/plots/` | Overview + Deep Dive dashboards matching project brief |
| 4 | **Playbook** | `outputs/04_retention_playbook.md` | Promo sunset plan + ideal customer profile per segment |
| 5 | **Summary** | `outputs/04_executive_summary.md` | 1-page executive brief with findings & recommendations |

---

## Engineered Features

| Feature | Definition | Business Relevance |
|---------|-----------|-------------------|
| `dependency_score` | Share of orders placed in promo months (Nov–Dec) | Identifies discount hunters vs. organic buyers |
| `value_tier` | High / Mid / Low based on revenue percentiles | Prioritises retention investment |
| `satisfaction_flag` | Return rate below P75 AND frequency ≥ 2 | Proxy for customer satisfaction |
| `loyal_defA` | High value tier + dependency < 0.5 | Revenue-based loyalty definition |
| `loyal_defB` | Frequency ≥ median + recency ≤ 90 days | Behaviour-based loyalty definition |

---

## The Central Analytical Challenge

The dataset has **no loyalty score, no churn label, no timestamps**.  
Every concept is constructed from available variables, not assumed.

- Loyalty is **defined, not declared**
- Two competing loyalty definitions are tested and compared
- Every segment claim is **traceable to specific variable combinations**
- All engineered features answer a question the brand actually cares about

---

## Key Findings Preview

| Insight | Detail |
|---------|--------|
| **Champions** | Bought avg 2 days ago · Zero promo dependency needed |
| **At Risk** | £766 avg revenue · 163 days inactive · Prime win-back target |
| **Lost** | Smallest segment · Churn is recoverable for ~8% |
| **Promo Dependency** | Significant share of At Risk revenue is promo-conditioned |
| **Loyalty Definitions** | Def A vs Def B diverge → frequency ≠ loyalty |

---

*SQL queries compatible with PostgreSQL, MySQL 8+, BigQuery, Snowflake*
