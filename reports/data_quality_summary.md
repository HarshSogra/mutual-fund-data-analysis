# Data Quality Summary Report

This report summarizes the data quality inspection, exploration, and validation findings for the 10 raw mutual fund datasets.

## Executive Summary

A comprehensive quality scan was performed across all 10 raw datasets. Overall, the datasets exhibit exceptionally high data quality:
* **Total Datasets Inspected:** 10
* **Data Completeness:** High. Only one minor column in a single dataset was found to have missing values.
* **Uniqueness:** No duplicate rows were detected in any of the datasets.
* **Schema Validation:** Data types are consistent, and there are no completely empty columns.
* **AMFI Code Referential Integrity:** 100% match between the Fund Master and NAV History.

---

## Detailed Data Quality Findings

| Dataset File Name | Shape (Rows x Cols) | Missing Values | Duplicate Rows | Empty Columns | Potential Datatype Issues |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `01_fund_master.csv` | 40 x 15 | None | None | None | None |
| `02_nav_history.csv` | 46,000 x 3 | None | None | None | None |
| `03_aum_by_fund_house.csv` | 90 x 5 | None | None | None | None |
| `04_monthly_sip_inflows.csv` | 48 x 6 | **12** (in `yoy_growth_pct`) | None | None | None |
| `05_category_inflows.csv` | 144 x 3 | None | None | None | None |
| `06_industry_folio_count.csv` | 21 x 6 | None | None | None | None |
| `07_scheme_performance.csv` | 40 x 19 | None | None | None | None |
| `08_investor_transactions.csv` | 32,778 x 13 | None | None | None | None |
| `09_portfolio_holdings.csv` | 322 x 8 | None | None | None | None |
| `10_benchmark_indices.csv` | 8,050 x 3 | None | None | None | None |

### Major Anomalies Found

1. **`04_monthly_sip_inflows.csv`**
   * **Anomaly:** Column `yoy_growth_pct` contains **12 missing values** (representing the first 12 months/rows of data where year-over-year growth cannot be calculated because the previous year's comparative data is not present in the dataset).
   * **Impact:** Low. This is a standard cold-start data property, not a data corruption issue.

No other anomalies (such as duplicate rows, completely empty columns, or potential datatype issues) were observed during inspection.

---

## AMFI Code Validation Findings

Validation was performed by matching the set of `amfi_code` values in `01_fund_master.csv` against those in `02_nav_history.csv`:
* **Total unique AMFI codes in Fund Master:** 40
* **Total unique AMFI codes in NAV History:** 40
* **Number of missing codes:** 0
* **Result:** **All AMFI codes** present in the Fund Master are successfully represented in the NAV History dataset, demonstrating 100% referential integrity.

---

## Conclusion & Recommendations

The ingested datasets are highly reliable. Data cleaning is not urgently needed except for handling the missing values in `yoy_growth_pct` during calculations, which can simply be filled with `0` or left as `NaN` (excluded from averages). We can proceed with analysis, feature engineering, and live NAV matching.
