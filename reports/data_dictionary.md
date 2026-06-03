# Mutual Fund Star Schema - Data Dictionary

This document serves as the data dictionary for the SQLite database `bluestock_mf.db` star schema tables.

---

## 1. Table: `dim_fund`
* **Type:** Dimension Table
* **Business Definition:** Stores reference information and parameters for each mutual fund scheme.
* **Source Dataset:** `01_fund_master.csv` (with basic cleaning)

| Column Name | SQLite Data Type | Business Definition | Source Column / Table |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER (PK) | Association of Mutual Funds in India identifier code | `amfi_code` |
| `fund_house` | TEXT | Asset Management Company (AMC) name | `fund_house` |
| `scheme_name` | TEXT | Full name of the mutual fund scheme | `scheme_name` |
| `category` | TEXT | Broad category of fund (e.g., Equity, Debt) | `category` |
| `sub_category` | TEXT | Specific asset class classification (e.g., Large Cap, Gilt) | `sub_category` |
| `plan` | TEXT | Investment plan option (Regular or Direct) | `plan` |
| `launch_date` | TEXT | Date when the fund scheme was launched | `launch_date` |
| `benchmark` | TEXT | Market index benchmark that the fund performance is measured against | `benchmark` |
| `expense_ratio_pct` | REAL | Total annual operating expenses of the scheme, as a percentage of assets | `expense_ratio_pct` |
| `exit_load_pct` | REAL | Charge levied when an investor exits or redeems units within a lock-in period | `exit_load_pct` |
| `min_sip_amount` | INTEGER | Minimum allowed monthly investment amount for Systematic Investment Plan | `min_sip_amount` |
| `min_lumpsum_amount` | INTEGER | Minimum allowed initial lump sum investment amount | `min_lumpsum_amount` |
| `fund_manager` | TEXT | Person responsible for managing the portfolio of the scheme | `fund_manager` |
| `risk_category` | TEXT | Risk classification of the fund (e.g., Moderate, Very High) | `risk_category` |
| `sebi_category_code` | TEXT | Securities and Exchange Board of India standardized category code | `sebi_category_code` |

---

## 2. Table: `dim_date`
* **Type:** Dimension Table
* **Business Definition:** Standard calendar date dimension table for joining facts.
* **Source:** Dynamically constructed from unique dates available in NAV, transaction, and AUM tables.

| Column Name | SQLite Data Type | Business Definition | Source Column / Table |
| :--- | :--- | :--- | :--- |
| `date` | TEXT (PK) | Calendar date formatted as `YYYY-MM-DD` | Generated |
| `year` | INTEGER | Calendar year | Generated |
| `month` | INTEGER | Calendar month number (1-12) | Generated |
| `day` | INTEGER | Day of month (1-31) | Generated |
| `quarter` | INTEGER | Calendar quarter of year (1-4) | Generated |
| `month_name` | TEXT | Full text name of the month (e.g., January) | Generated |
| `day_name` | TEXT | Full text name of the day of the week (e.g., Monday) | Generated |

---

## 3. Table: `fact_nav`
* **Type:** Fact Table
* **Business Definition:** Records daily historical Net Asset Values (NAV) of mutual fund schemes.
* **Source Dataset:** `02_nav_history.csv` (with basic cleaning)

| Column Name | SQLite Data Type | Business Definition | Source Column / Table |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER (FK) | AMFI code referencing `dim_fund` | `amfi_code` |
| `date` | TEXT (FK) | Calendar date referencing `dim_date` | `date` |
| `nav` | REAL | Net Asset Value (price per unit) of the scheme on that date | `nav` |

---

## 4. Table: `fact_transactions`
* **Type:** Fact Table
* **Business Definition:** Stores records of all buy, sell, and systematic investment transactions by investors.
* **Source Dataset:** `08_investor_transactions.csv` (with cleaning and formatting)

| Column Name | SQLite Data Type | Business Definition | Source Column / Table |
| :--- | :--- | :--- | :--- |
| `transaction_id` | INTEGER (PK) | Auto-incrementing identifier for transactions | Generated |
| `investor_id` | TEXT | Unique ID representing an investor | `investor_id` |
| `transaction_date` | TEXT (FK) | Date of transaction referencing `dim_date` | `transaction_date` |
| `amfi_code` | INTEGER (FK) | AMFI code of the fund scheme invested in, referencing `dim_fund` | `amfi_code` |
| `transaction_type` | TEXT | Type of transaction (SIP, Lumpsum, or Redemption) | `transaction_type` |
| `amount_inr` | INTEGER | Value of the transaction in Indian Rupees | `amount_inr` |
| `state` | TEXT | Indian state where the transaction originated | `state` |
| `city` | TEXT | Indian city where the transaction originated | `city` |
| `city_tier` | TEXT | Standard city class category (e.g., T30 for Top 30, B30 for Beyond 30) | `city_tier` |
| `age_group` | TEXT | Age range classification of the investor | `age_group` |
| `gender` | TEXT | Gender of the investor (Male, Female) | `gender` |
| `annual_income_lakh` | REAL | Annual income range of the investor in Lakhs INR | `annual_income_lakh` |
| `payment_mode` | TEXT | Payment method used (Cheque, UPI, Mandate, Net Banking) | `payment_mode` |
| `kyc_status` | TEXT | KYC (Know Your Customer) compliance status (Verified, Pending) | `kyc_status` |

---

## 5. Table: `fact_performance`
* **Type:** Fact Table
* **Business Definition:** Captures returns, ratings, and key risk metrics for each fund scheme.
* **Source Dataset:** `07_scheme_performance.csv` (with return coercion and validation checks)

| Column Name | SQLite Data Type | Business Definition | Source Column / Table |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER (PK, FK) | AMFI code identifying the scheme, referencing `dim_fund` | `amfi_code` |
| `scheme_name` | TEXT | Full name of the mutual fund scheme | `scheme_name` |
| `fund_house` | TEXT | Asset Management Company (AMC) name | `fund_house` |
| `category` | TEXT | Broad category of fund (Equity, Debt) | `category` |
| `plan` | TEXT | Investment plan option (Regular or Direct) | `plan` |
| `return_1yr_pct` | REAL | Historical annualized return over the last 1 year | `return_1yr_pct` |
| `return_3yr_pct` | REAL | Historical annualized return over the last 3 years | `return_3yr_pct` |
| `return_5yr_pct` | REAL | Historical annualized return over the last 5 years | `return_5yr_pct` |
| `benchmark_3yr_pct` | REAL | Annualized return of the benchmark index over the last 3 years | `benchmark_3yr_pct` |
| `alpha` | REAL | Outperformance of the fund relative to its benchmark index | `alpha` |
| `beta` | REAL | Volatility of the fund relative to the overall market | `beta` |
| `sharpe_ratio` | REAL | Risk-adjusted return measure (excess return per unit of volatility) | `sharpe_ratio` |
| `sortino_ratio` | REAL | Return measure adjusted for downside volatility only | `sortino_ratio` |
| `std_dev_ann_pct` | REAL | Annualized standard deviation of returns (measure of total risk) | `std_dev_ann_pct` |
| `max_drawdown_pct` | REAL | Maximum peak-to-trough drop in value during a specific period | `max_drawdown_pct` |
| `aum_crore` | INTEGER | Current Assets Under Management in Crores INR | `aum_crore` |
| `expense_ratio_pct` | REAL | Scheme operating expense percentage | `expense_ratio_pct` |
| `morningstar_rating` | INTEGER | Morningstar fund quality star rating (1 to 5) | `morningstar_rating` |
| `risk_grade` | TEXT | Risk grading grade description | `risk_grade` |

---

## 6. Table: `fact_aum`
* **Type:** Fact Table
* **Business Definition:** Tracks assets under management and scheme count trends for each fund house.
* **Source Dataset:** `03_aum_by_fund_house.csv` (with basic cleaning)

| Column Name | SQLite Data Type | Business Definition | Source Column / Table |
| :--- | :--- | :--- | :--- |
| `date` | TEXT (FK) | Date of reporting referencing `dim_date` | `date` |
| `fund_house` | TEXT | AMC Name | `fund_house` |
| `aum_lakh_crore` | REAL | Assets Under Management in Lakh Crores INR | `aum_lakh_crore` |
| `aum_crore` | INTEGER | Assets Under Management in Crores INR | `aum_crore` |
| `num_schemes` | INTEGER | Total number of schemes offered by the AMC | `num_schemes` |
