-- Analytical SQL Queries for Mutual Fund Star Schema

-- Query 1: Top 5 funds by AUM
SELECT 
    scheme_name, 
    aum_crore
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;

-- Query 2: Average NAV per month
SELECT 
    strftime('%Y-%m', date) AS month, 
    ROUND(AVG(nav), 4) AS avg_nav
FROM fact_nav
GROUP BY month
ORDER BY month;

-- Query 3: SIP YoY growth (computed from fact_transactions)
WITH annual_sip AS (
    SELECT 
        strftime('%Y', transaction_date) AS year,
        SUM(amount_inr) AS total_sip_amount
    FROM fact_transactions
    WHERE transaction_type = 'SIP'
    GROUP BY year
)
SELECT 
    curr.year,
    curr.total_sip_amount,
    prev.total_sip_amount AS prev_year_sip_amount,
    ROUND(((curr.total_sip_amount - prev.total_sip_amount) * 100.0 / prev.total_sip_amount), 2) AS yoy_growth_pct
FROM annual_sip curr
LEFT JOIN annual_sip prev ON CAST(curr.year AS INTEGER) = CAST(prev.year AS INTEGER) + 1
ORDER BY curr.year;

-- Query 4: Transactions by state
SELECT 
    state, 
    COUNT(*) AS transaction_count,
    SUM(amount_inr) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;

-- Query 5: Funds with expense_ratio < 1%
SELECT 
    amfi_code, 
    scheme_name, 
    fund_house, 
    expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

-- Query 6: Total transaction count and total amount by payment mode
SELECT 
    payment_mode,
    COUNT(*) AS txn_count,
    SUM(amount_inr) AS total_amount_inr
FROM fact_transactions
GROUP BY payment_mode
ORDER BY total_amount_inr DESC;

-- Query 7: Average transaction size by gender and age group
SELECT 
    gender,
    age_group,
    COUNT(*) AS txn_count,
    ROUND(AVG(amount_inr), 2) AS avg_txn_amount_inr
FROM fact_transactions
GROUP BY gender, age_group
ORDER BY gender, avg_txn_amount_inr DESC;

-- Query 8: Top 10 funds by 5-year return, including risk grade and Morningstar rating
SELECT 
    scheme_name,
    return_5yr_pct,
    risk_grade,
    morningstar_rating
FROM fact_performance
WHERE return_5yr_pct IS NOT NULL
ORDER BY return_5yr_pct DESC
LIMIT 10;

-- Query 9: Month-on-month trend of AUM per fund house
SELECT 
    fund_house,
    strftime('%Y-%m', date) AS month,
    MAX(aum_crore) AS max_aum_crore
FROM fact_aum
GROUP BY fund_house, month
ORDER BY fund_house, month;

-- Query 10: Comparison of transaction volumes on weekdays vs weekends
SELECT 
    CASE 
        WHEN d.day_name IN ('Saturday', 'Sunday') THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    COUNT(*) AS transaction_count,
    SUM(t.amount_inr) AS total_amount_inr,
    ROUND(AVG(t.amount_inr), 2) AS avg_amount_inr
FROM fact_transactions t
JOIN dim_date d ON t.transaction_date = d.date
GROUP BY day_type;
