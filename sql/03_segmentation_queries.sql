-- ==============================================================
-- DECODING CUSTOMER VALUE — SQL DELIVERABLE
-- Segmentation Queries Answering All 5 Key Business Questions
-- ==============================================================
-- Compatible with: PostgreSQL · MySQL 8+ · BigQuery · Snowflake
-- Base table assumed: rfm_features (output of Python Step 1)
-- ==============================================================


-- ──────────────────────────────────────────────────────────────
-- SETUP: Create RFM base view
-- ──────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_rfm AS
SELECT
    customer_id,
    recency,
    frequency,
    monetary,
    avg_order_val,
    tenure_days,
    return_rate,
    satisfaction_flag,
    dependency_score,
    value_tier,
    loyal_defA,
    loyal_defB,
    r_score,
    f_score,
    m_score,
    rfm_total,
    segment
FROM rfm_features;


-- ══════════════════════════════════════════════════════════════
-- Q1: Who are the genuinely loyal customers vs. discount hunters?
-- ══════════════════════════════════════════════════════════════

-- Q1a: Loyalty comparison — two definitions side by side
SELECT
    CASE WHEN loyal_defA = 1 AND loyal_defB = 1 THEN 'Loyal (Both Definitions)'
         WHEN loyal_defA = 1                     THEN 'Loyal by Revenue'
         WHEN loyal_defB = 1                     THEN 'Loyal by Behaviour'
         ELSE                                         'Discount Hunter / Inactive'
    END                                     AS loyalty_class,
    COUNT(*)                                AS customers,
    ROUND(AVG(monetary),       2)           AS avg_revenue,
    ROUND(AVG(dependency_score),3)          AS avg_dependency,
    ROUND(AVG(frequency),      1)           AS avg_orders,
    ROUND(AVG(recency),        0)           AS avg_recency_days,
    ROUND(AVG(return_rate)*100,1)           AS return_rate_pct,
    ROUND(AVG(satisfaction_flag)*100,1)     AS pct_satisfied
FROM v_rfm
GROUP BY 1
ORDER BY avg_revenue DESC;


-- Q1b: Top 20% loyal customers — ideal customer profile seed
WITH ranked AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY monetary DESC) AS revenue_quintile
    FROM v_rfm
    WHERE loyal_defA = 1
)
SELECT
    revenue_quintile,
    COUNT(*)                            AS customers,
    ROUND(AVG(recency),    0)           AS avg_recency,
    ROUND(AVG(frequency),  1)           AS avg_frequency,
    ROUND(AVG(monetary),   2)           AS avg_revenue,
    ROUND(AVG(dependency_score), 3)     AS avg_promo_dependency,
    ROUND(AVG(tenure_days)/365.25, 1)  AS avg_tenure_years
FROM ranked
GROUP BY 1
ORDER BY 1;


-- ══════════════════════════════════════════════════════════════
-- Q2: Which behavioural patterns predict high customer value?
-- ══════════════════════════════════════════════════════════════

-- Q2a: Predictive signal strength — correlation proxy via group means
SELECT
    value_tier,
    COUNT(*)                                AS customers,
    ROUND(AVG(recency),         0)          AS avg_recency,
    ROUND(AVG(frequency),       1)          AS avg_frequency,
    ROUND(AVG(tenure_days),     0)          AS avg_tenure_days,
    ROUND(AVG(dependency_score),3)          AS avg_dependency,
    ROUND(AVG(return_rate)*100, 1)          AS avg_return_rate_pct,
    ROUND(AVG(satisfaction_flag)*100, 1)    AS pct_satisfied,
    ROUND(AVG(monetary),        2)          AS avg_revenue
FROM v_rfm
GROUP BY 1
ORDER BY avg_revenue DESC;


-- Q2b: High-value customers who show WARNING signals (at risk of churning)
SELECT
    customer_id,
    segment,
    recency,
    frequency,
    ROUND(monetary, 2)          AS lifetime_revenue,
    ROUND(dependency_score, 3)  AS promo_dependency,
    ROUND(return_rate * 100, 1) AS return_rate_pct,
    satisfaction_flag,
    CASE
        WHEN recency > 90  AND value_tier = 'High' THEN 'Long-Inactive High Value'
        WHEN dependency_score > 0.7                THEN 'Promo Dependent'
        WHEN return_rate > 0.3                     THEN 'High Returner'
        ELSE                                            'Monitor'
    END                         AS risk_flag
FROM v_rfm
WHERE value_tier = 'High'
  AND (recency > 90 OR dependency_score > 0.7 OR return_rate > 0.3)
ORDER BY monetary DESC;


-- ══════════════════════════════════════════════════════════════
-- Q3: Which geographies signal organic vs. discount-driven demand?
--     (requires joining orders table with country/region data)
-- ══════════════════════════════════════════════════════════════

-- Q3a: Revenue and dependency by country (join with orders)
SELECT
    o.country,
    COUNT(DISTINCT r.customer_id)           AS customers,
    ROUND(SUM(r.monetary), 0)               AS total_revenue,
    ROUND(AVG(r.dependency_score), 3)       AS avg_dependency,
    ROUND(AVG(r.frequency), 1)              AS avg_frequency,
    ROUND(AVG(r.recency), 0)               AS avg_recency,
    ROUND(AVG(r.return_rate)*100, 1)        AS avg_return_rate_pct,
    -- Classify as organic vs promo-driven
    CASE
        WHEN AVG(r.dependency_score) < 0.4  THEN 'Organic Demand'
        WHEN AVG(r.dependency_score) < 0.65 THEN 'Mixed'
        ELSE                                     'Promo Driven'
    END                                     AS demand_type
FROM v_rfm r
JOIN (
    SELECT DISTINCT customer_id, country
    FROM orders   -- replace with your actual orders/transactions table
) o ON r.customer_id = o.customer_id
GROUP BY o.country
HAVING COUNT(DISTINCT r.customer_id) >= 10
ORDER BY total_revenue DESC;


-- Q3b: Geographic opportunity matrix — high spend + low promo dependency
SELECT
    o.country,
    COUNT(DISTINCT r.customer_id)   AS customers,
    ROUND(AVG(r.monetary), 0)       AS avg_revenue_per_customer,
    ROUND(AVG(r.dependency_score),3) AS avg_dependency,
    ROUND(SUM(r.monetary), 0)       AS total_revenue,
    -- Opportunity score: high revenue × low dependency
    ROUND(AVG(r.monetary) * (1 - AVG(r.dependency_score)), 0) AS opportunity_score
FROM v_rfm r
JOIN (SELECT DISTINCT customer_id, country FROM orders) o
  ON r.customer_id = o.customer_id
GROUP BY o.country
HAVING COUNT(DISTINCT r.customer_id) >= 5
ORDER BY opportunity_score DESC
LIMIT 15;


-- ══════════════════════════════════════════════════════════════
-- Q4: How should the brand restructure promotions to protect margins?
-- ══════════════════════════════════════════════════════════════

-- Q4a: Promo sunset candidates — high dependency, recoverable
SELECT
    segment,
    value_tier,
    COUNT(*)                                AS customers,
    ROUND(AVG(dependency_score), 3)         AS avg_dependency,
    ROUND(AVG(monetary), 2)                 AS avg_revenue,
    ROUND(AVG(frequency), 1)                AS avg_frequency,
    ROUND(AVG(recency), 0)                 AS avg_recency,
    -- Margin recovery potential: revenue × dependency (lost if promo removed)
    ROUND(SUM(monetary) * AVG(dependency_score), 0) AS at_risk_revenue,
    -- Recommendation
    CASE
        WHEN AVG(dependency_score) > 0.7 AND AVG(frequency) < 5
            THEN '🔴 Phase Out Promos — Low loyalty signal'
        WHEN AVG(dependency_score) > 0.5 AND AVG(monetary) > 500
            THEN '🟡 Reduce Gradually — High value, test sensitivity'
        WHEN AVG(dependency_score) < 0.4
            THEN '🟢 Maintain — Organically loyal'
        ELSE    '⚪ Monitor — Insufficient signal'
    END AS promo_action
FROM v_rfm
GROUP BY segment, value_tier
ORDER BY at_risk_revenue DESC;


-- Q4b: Rollout phasing — which segments to sunset first
SELECT
    CASE
        WHEN dependency_score >= 0.8 AND monetary < 300  THEN 'Phase 1 — Immediate sunset'
        WHEN dependency_score >= 0.6 AND monetary < 600  THEN 'Phase 2 — Q2 reduction'
        WHEN dependency_score >= 0.4                     THEN 'Phase 3 — Test & monitor'
        ELSE                                                  'No change — Organic'
    END                                         AS rollout_phase,
    COUNT(*)                                    AS customers,
    ROUND(AVG(monetary), 0)                     AS avg_revenue,
    ROUND(AVG(dependency_score), 3)             AS avg_dependency,
    ROUND(SUM(monetary) * AVG(dependency_score), 0) AS projected_risk_revenue
FROM v_rfm
GROUP BY 1
ORDER BY 1;


-- ══════════════════════════════════════════════════════════════
-- Q5: What does the brand's best customer look like?
--     → Ideal Customer Profile (ICP)
-- ══════════════════════════════════════════════════════════════

-- Q5a: ICP — top decile characteristics
WITH top_decile AS (
    SELECT *,
           NTILE(10) OVER (ORDER BY rfm_total DESC) AS decile
    FROM v_rfm
)
SELECT
    'Top 10%'                               AS customer_group,
    COUNT(*)                                AS n,
    ROUND(AVG(recency), 0)                 AS avg_recency_days,
    ROUND(AVG(frequency), 1)               AS avg_orders,
    ROUND(AVG(monetary), 0)                AS avg_revenue,
    ROUND(AVG(tenure_days) / 30.0, 1)     AS avg_tenure_months,
    ROUND(AVG(dependency_score), 3)        AS avg_promo_dependency,
    ROUND(AVG(return_rate) * 100, 1)       AS return_rate_pct,
    ROUND(AVG(satisfaction_flag)*100, 0)   AS pct_satisfied,
    -- Thresholds for targeting model
    MAX(recency)                            AS max_recency_cutoff,
    MIN(frequency)                          AS min_frequency_cutoff,
    MIN(monetary)                           AS min_revenue_cutoff
FROM top_decile
WHERE decile = 1

UNION ALL

SELECT
    'Remaining 90%',
    COUNT(*), ROUND(AVG(recency),0), ROUND(AVG(frequency),1),
    ROUND(AVG(monetary),0), ROUND(AVG(tenure_days)/30.0,1),
    ROUND(AVG(dependency_score),3), ROUND(AVG(return_rate)*100,1),
    ROUND(AVG(satisfaction_flag)*100,0),
    MAX(recency), MIN(frequency), MIN(monetary)
FROM top_decile
WHERE decile > 1;


-- Q5b: Segment-level ideal customer profile summary
SELECT
    segment,
    COUNT(*)                                AS customers,
    ROUND(MIN(monetary), 0)                 AS min_revenue,
    ROUND(AVG(monetary), 0)                 AS avg_revenue,
    ROUND(MAX(monetary), 0)                 AS max_revenue,
    ROUND(AVG(recency), 0)                 AS avg_recency,
    ROUND(AVG(frequency), 1)               AS avg_frequency,
    ROUND(AVG(dependency_score), 3)        AS avg_dependency,
    ROUND(AVG(tenure_days) / 365.0, 1)    AS avg_tenure_years,
    ROUND(AVG(return_rate) * 100, 1)       AS return_rate_pct,
    -- Priority for retention investment
    CASE segment
        WHEN 'Champions'          THEN 1
        WHEN 'Loyal Customers'    THEN 2
        WHEN 'At Risk'            THEN 3
        WHEN 'Can''t Lose Them'   THEN 4
        WHEN 'Potential Loyalists' THEN 5
        WHEN 'Need Attention'     THEN 6
        WHEN 'Promising'          THEN 7
        WHEN 'New Customers'      THEN 8
        WHEN 'Lost'               THEN 9
    END                                     AS retention_priority
FROM v_rfm
GROUP BY segment
ORDER BY retention_priority;


-- ══════════════════════════════════════════════════════════════
-- BONUS: Full KPI dashboard query (single-row executive summary)
-- ══════════════════════════════════════════════════════════════
SELECT
    COUNT(*)                                    AS total_customers,
    ROUND(SUM(monetary), 0)                     AS total_revenue,
    ROUND(AVG(monetary), 2)                     AS avg_customer_revenue,
    ROUND(AVG(avg_order_val), 2)               AS avg_order_value,
    ROUND(AVG(frequency), 1)                   AS avg_order_frequency,
    ROUND(AVG(recency), 0)                     AS avg_recency_days,
    ROUND(AVG(dependency_score), 3)            AS avg_promo_dependency,
    ROUND(AVG(return_rate) * 100, 1)           AS avg_return_rate_pct,
    ROUND(AVG(satisfaction_flag) * 100, 1)     AS pct_satisfied_customers,
    SUM(loyal_defA)                            AS loyal_customers_defA,
    SUM(loyal_defB)                            AS loyal_customers_defB,
    ROUND(SUM(loyal_defA) * 100.0 / COUNT(*), 1) AS loyal_pct_defA,
    ROUND(SUM(loyal_defB) * 100.0 / COUNT(*), 1) AS loyal_pct_defB
FROM v_rfm;
