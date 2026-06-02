# Mutual Fund Analysis 

This repository contains the Day 1 deliverables for the Mutual Fund Analysis project, focused on data ingestion, quality inspection, validation, and live NAV retrieval.

## Project Structure

```text
mutual_fund_analysis/
├── data/
│   ├── raw/                 # Contains 10 raw CSV files and live fetched NAV files
│   └── processed/
│
├── notebooks/
├── sql/
├── dashboard/
├── reports/
│   └── data_quality_summary.md  # Detailed report on data quality and validation
│
├── data_ingestion.py        # Script for loading, inspection, and validation of raw CSVs
├── live_nav_fetch.py        # Script to retrieve live NAV data from MFAPI
├── requirements.txt         # Project dependencies
├── README.md                # Project documentation (this file)
└── .gitignore               # Files ignored by Git
```

## Dependencies

The project requires Python 3.x and the packages listed in `requirements.txt`:
* `pandas` - Data manipulation and analysis
* `numpy` - Numerical computing utilities
* `matplotlib` & `seaborn` & `plotly` - Data visualization libraries
* `sqlalchemy` - Database connectivity (for future steps)
* `requests` - Making HTTP requests to retrieve live NAVs
* `scipy` - Scientific computations
* `jupyter` - Interactive notebook environment

To install dependencies, run:
```bash
pip install -r requirements.txt
```

## Execution Instructions

### 1. Ingest and Validate Data
To load all 10 raw datasets, perform anomaly scans, explore the fund master, and validate AMFI codes, run:
```bash
python data_ingestion.py
```
This script prints shape, data types, first few rows, and detected anomalies for all 10 datasets, followed by unique fields and code validation results.

### 2. Fetch Live NAV
To fetch live NAV records from the MFAPI endpoint and save them as CSV files in the `data/raw` folder, run:
```bash
python live_nav_fetch.py
```
This fetches the latest NAV data for HDFC Top 100 Direct and 5 other key schemes, saving them to files such as:
* `live_nav_125497.csv`
* `sbi_bluechip_nav.csv`
* `icici_bluechip_nav.csv`
* `nippon_large_cap_nav.csv`
* `axis_bluechip_nav.csv`
* `kotak_bluechip_nav.csv`

---

## Data Validation Summary

* **Inspected Datasets:** 10
* **Data Completeness:** 100% complete except for 12 missing values in `yoy_growth_pct` column within `04_monthly_sip_inflows.csv` due to starting periods.
* **Referential Integrity:** 100% of AMFI codes in `01_fund_master.csv` are present in `02_nav_history.csv`, showing perfect referential alignment between the master listing and historical NAV logs.

For detailed analysis, refer to [reports/data_quality_summary.md](reports/data_quality_summary.md).
