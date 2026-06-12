# Mutual Fund Analysis & Analytics Platform

## Project Overview

This project analyzes Indian mutual fund data across fund metadata, NAV history, AUM, SIP inflows, category inflows, investor transactions, benchmark indices, and fund performance metrics.

The platform covers the full analytics workflow: data ingestion, cleaning, SQLite database loading, exploratory analysis, performance analytics, advanced risk analytics, and a Power BI dashboard.

## Purpose of the Project

The purpose of this project is to convert raw mutual fund datasets into a structured analytics platform that can support business reporting, fund comparison, investor behavior analysis, and dashboard-based decision making.

## Business Objective

The business objective is to help stakeholders understand mutual fund industry growth, fund performance, investor participation, SIP trends, market relationships, and risk-adjusted fund quality using a clean database and reproducible analytics workflow.

## Features

### Data Ingestion

- Reads 10 raw mutual fund CSV datasets from `data/raw/`.
- Performs basic quality inspection, anomaly checks, missing value checks, duplicate checks, and AMFI code validation.
- Supports optional live NAV fetching from MFAPI through `live_nav_fetch.py`.

### Data Cleaning

- Standardizes dates across datasets.
- Removes duplicate rows.
- Validates NAV and transaction amount values.
- Handles missing year-over-year SIP growth values.
- Writes cleaned datasets to `data/processed/`.

### SQLite Database

- Loads processed CSV files into `bluestock_mf.db`.
- Uses a star schema with fund and date dimensions.
- Includes fact tables for NAV, transactions, performance, and AUM.
- Verifies loaded row counts against source datasets.

### EDA

- Includes exploratory analysis in `notebooks/EDA_Analysis.ipynb`.
- Covers NAV trends, AUM growth, SIP inflows, category performance, investor demographics, geography, folio growth, return correlations, sector allocation, and fund performance summaries.
- Outputs charts to `reports/charts/`.

### Performance Analytics

- Includes performance analysis in `notebooks/Performance_Analytics.ipynb`.
- Calculates and compares CAGR, Sharpe ratio, Sortino ratio, alpha, beta, drawdown, and fund scorecard rankings.
- Writes outputs such as `alpha_beta.csv` and `fund_scorecard.csv` to `data/processed/`.

### Advanced Analytics

- Includes advanced analysis in `notebooks/Advanced_Analytics.ipynb`.
- Covers historical VaR, CVaR, rolling 90-day Sharpe ratio, benchmark comparison, and simple risk-based fund recommendation.
- Writes outputs such as `var_cvar_report.csv` and rolling Sharpe charts.

### Power BI Dashboard

- Dashboard deliverables include `bluestock_mf_dashboard.pbix`, `Dashboard.pdf`, and static dashboard page exports in `reports/dashboard/`.
- Dashboard pages cover industry overview, fund performance, investor analytics, and SIP and market trends.

## Folder Structure

```text
INTERNSHIP/
|-- data/
|   |-- raw/                      Raw mutual fund CSV datasets and live NAV extracts
|   `-- processed/                Cleaned datasets and analytics outputs
|-- notebooks/
|   |-- EDA_Analysis.ipynb
|   |-- Performance_Analytics.ipynb
|   `-- Advanced_Analytics.ipynb
|-- reports/
|   |-- charts/                   EDA and analytics chart outputs
|   |-- dashboard/                Dashboard page images and logo
|   |-- data_dictionary.md
|   `-- data_quality_summary.md
|-- sql/
|   |-- schema.sql                SQLite star schema DDL
|   `-- queries.sql               Analytical SQL queries
|-- ANALYSIS_SUMMARY.md           EDA summary report
|-- bluestock_mf.db               SQLite database
|-- bluestock_mf_dashboard.pbix   Power BI dashboard file
|-- Dashboard.pdf                 Dashboard PDF export
|-- build_day5_dashboard.py       Dashboard generation script
|-- clean_data.py                 Data cleaning script
|-- data_ingestion.py             Data ingestion and quality inspection script
|-- live_nav_fetch.py             Optional live NAV fetch script
|-- load_to_sqlite.py             SQLite loading script
|-- recommender.py                Simple risk-based recommender
|-- run_pipeline.py               Master workflow runner
|-- test_queries.py               SQLite query verification script
|-- requirements.txt
`-- README.md
```

## Setup Instructions

### Clone Repository

```bash
git clone <repository-url>
cd INTERNSHIP
```

### Install Requirements

```bash
pip install -r requirements.txt
```

### Environment Setup

No separate environment file is required for the core project. A Python environment with the packages listed in `requirements.txt` is sufficient.

For notebooks, ensure Jupyter is installed and available:

```bash
jupyter notebook
```

## How to Run

### Data Cleaning

```bash
python clean_data.py
```

This reads raw CSV files from `data/raw/` and writes cleaned files to `data/processed/`.

### Database Loading

```bash
python load_to_sqlite.py
```

This creates or refreshes `bluestock_mf.db` using `sql/schema.sql` and processed CSV files.

### Analytics Notebooks

Run the notebooks in this order:

```bash
jupyter notebook notebooks/EDA_Analysis.ipynb
jupyter notebook notebooks/Performance_Analytics.ipynb
jupyter notebook notebooks/Advanced_Analytics.ipynb
```

### run_pipeline.py

```bash
python run_pipeline.py
```

The master pipeline runs:

- `clean_data.py`
- `load_to_sqlite.py`
- `notebooks/EDA_Analysis.ipynb`
- `notebooks/Performance_Analytics.ipynb`
- `notebooks/Advanced_Analytics.ipynb`
- `test_queries.py`

Missing scripts or notebooks are skipped with clear messages. Notebooks are executed only if Jupyter is available.

### Power BI Dashboard

Open the existing dashboard file:

```text
bluestock_mf_dashboard.pbix
```

The PDF export is available as:

```text
Dashboard.pdf
```

To rebuild dashboard deliverables from the existing script:

```bash
python build_day5_dashboard.py
```

## Database Information

### Star Schema Overview

The SQLite database uses a star schema centered on fund, date, NAV, transaction, performance, and AUM data. Dimension tables provide descriptive attributes, while fact tables store measurable business events and metrics.

### Main Tables

#### dim_fund

Stores fund-level master information such as AMFI code, fund house, scheme name, category, sub-category, plan, launch date, benchmark, expense ratio, minimum investment amounts, fund manager, risk category, and SEBI category code.

#### dim_date

Stores date attributes including date, year, month, day, quarter, month name, and day name.

#### fact_nav

Stores historical NAV values by AMFI code and date.

#### fact_transactions

Stores investor transaction records including investor ID, transaction date, AMFI code, transaction type, amount, geography, demographics, payment mode, and KYC status.

#### fact_performance

Stores scheme-level return and risk metrics such as 1-year, 3-year, and 5-year returns, benchmark return, alpha, beta, Sharpe ratio, Sortino ratio, standard deviation, drawdown, AUM, expense ratio, rating, and risk grade.

#### fact_aum

Stores assets under management by fund house and date.

## Dashboard Information

### Industry Overview

Shows total AUM, SIP inflows, total folios, total schemes, industry AUM trend, and AUM by AMC or fund house.

### Fund Performance

Shows fund ranking, fund scorecard metrics, return versus risk analysis, NAV versus benchmark comparison, and fund-level filtering.

### Investor Analytics

Shows investor transaction amount and count by state, transaction type, age group, city tier, and time.

### SIP & Market Trends

Shows SIP inflows, Nifty 50 movement, category inflow patterns, and top categories by net inflow.

## Results & Insights

### EDA

- The datasets show high completeness, with only expected missing values in early year-over-year SIP growth periods.
- NAV history and fund master data have complete AMFI code alignment.
- AUM and SIP trends show steady industry growth across the available 2022-2025 period.
- Investor transaction data shows broad demographic and geographic participation.
- Category analysis indicates strong inflows into liquid and equity-oriented categories.

### Performance Analytics

- Fund performance varies across categories and schemes.
- Risk-adjusted metrics such as Sharpe and Sortino help compare funds beyond absolute returns.
- Alpha and beta analysis compares fund behavior against benchmark movement.
- The fund scorecard combines return, risk, alpha, expense ratio, and drawdown metrics for ranking.

### Advanced Analytics

- VaR and CVaR identify funds with higher downside and tail-risk exposure.
- Rolling Sharpe analysis shows that risk-adjusted performance changes over time.
- Benchmark comparison supports relative performance evaluation against market indices.
- The simple recommender ranks funds by risk category and Sharpe ratio.

## Technologies Used

- Python
- Pandas
- NumPy
- SQLAlchemy
- SQLite
- Plotly
- Matplotlib
- Power BI
- Git

