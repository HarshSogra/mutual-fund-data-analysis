"""Inspect raw mutual fund datasets and report basic data quality findings."""

import os

import pandas as pd

def run_data_ingestion():
    """Load raw CSV files, print quality checks, and validate AMFI coverage."""
    # Define directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_data_dir = os.path.join(base_dir, 'data', 'raw')
    
    # 10 raw CSV files in order
    csv_files = [
        "01_fund_master.csv",
        "02_nav_history.csv",
        "03_aum_by_fund_house.csv",
        "04_monthly_sip_inflows.csv",
        "05_category_inflows.csv",
        "06_industry_folio_count.csv",
        "07_scheme_performance.csv",
        "08_investor_transactions.csv",
        "09_portfolio_holdings.csv",
        "10_benchmark_indices.csv"
    ]
    
    loaded_datasets = {}
    
    print("=" * 80)
    print(" TASK 1: DATA INGESTION & QUALITY INSPECTION")
    print("=" * 80)
    
    for file_name in csv_files:
        file_path = os.path.join(raw_data_dir, file_name)
        print(f"\n--- Reading File: {file_name} ---")
        
        if not os.path.exists(file_path):
            print(f"Error: File {file_name} not found at {file_path}")
            continue
            
        try:
            df = pd.read_csv(file_path)
            loaded_datasets[file_name] = df
            
            # Print basic info
            print(f"Shape: {df.shape}")
            print("\nData Types:")
            print(df.dtypes)
            print("\nFirst 5 Rows:")
            print(df.head())
            
            # Anomaly Checks
            print("\n--- Anomaly Scan Summary ---")
            
            # 1. Missing values
            missing_counts = df.isnull().sum()
            missing_cols = missing_counts[missing_counts > 0]
            if not missing_cols.empty:
                print("Missing values detected:")
                for col, val in missing_cols.items():
                    print(f"  * Column '{col}': {val} missing values")
            else:
                print("  * No missing values found.")
                
            # 2. Duplicate rows
            dup_count = df.duplicated().sum()
            if dup_count > 0:
                print(f"  * Total duplicate rows: {dup_count}")
            else:
                print("  * No duplicate rows found.")
                
            # 3. Empty columns
            empty_cols = [col for col in df.columns if df[col].isnull().all()]
            if empty_cols:
                print(f"  * Completely empty columns: {empty_cols}")
            else:
                print("  * No completely empty columns found.")
                
            # 4. Potential datatype issues observed during inspection
            datatype_issues = []
            for col in df.columns:
                col_lower = col.lower()
                # Check date columns stored as object
                if ('date' in col_lower or 'dt' in col_lower) and df[col].dtype == 'object':
                    datatype_issues.append(f"Column '{col}' contains date-like values but has 'object' type.")
                
                # Check ID/Code columns stored as float/object (e.g. should probably be integer or string)
                if 'code' in col_lower and df[col].dtype == 'float64':
                    datatype_issues.append(f"Column '{col}' is a code/ID but is represented as float64.")
                
                # Check numerical values stored as object
                numeric_keywords = ['amount', 'ratio', 'nav', 'inflow', 'count', 'value', 'price', 'pct', 'aum', 'holding', 'units']
                if any(kw in col_lower for kw in numeric_keywords) and df[col].dtype == 'object':
                    datatype_issues.append(f"Column '{col}' might contain numeric values but has 'object' type.")
            
            if datatype_issues:
                print("Potential datatype issues observed during inspection:")
                for issue in datatype_issues:
                    print(f"  * {issue}")
            else:
                print("  * No potential datatype issues observed.")
                
        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")
            
        print("-" * 60)
        
    # Task 3: Explore Fund Master
    print("\n" + "=" * 80)
    print(" TASK 3: EXPLORE FUND MASTER")
    print("=" * 80)
    
    fund_master_name = "01_fund_master.csv"
    if fund_master_name in loaded_datasets:
        fund_master = loaded_datasets[fund_master_name]
        
        # Unique houses, categories, sub-categories, risk categories
        unique_houses = fund_master["fund_house"].unique()
        unique_categories = fund_master["category"].unique()
        unique_sub_categories = fund_master["sub_category"].unique()
        unique_risk_categories = fund_master["risk_category"].unique()
        
        print(f"Unique Fund Houses ({len(unique_houses)}):")
        print(", ".join(sorted(str(x) for x in unique_houses)))
        
        print(f"\nUnique Categories ({len(unique_categories)}):")
        print(", ".join(sorted(str(x) for x in unique_categories)))
        
        print(f"\nUnique Sub-Categories ({len(unique_sub_categories)}):")
        print(", ".join(sorted(str(x) for x in unique_sub_categories)))
        
        print(f"\nUnique Risk Categories ({len(unique_risk_categories)}):")
        print(", ".join(sorted(str(x) for x in unique_risk_categories)))
        
        # Briefly inspect the AMFI code structure using amfi_code, scheme_name, fund_house
        print("\nAMFI Code Structure Inspection (First 10 records):")
        structure_cols = ["amfi_code", "scheme_name", "fund_house"]
        if all(col in fund_master.columns for col in structure_cols):
            print(fund_master[structure_cols].head(10).to_string(index=False))
        else:
            print("Required columns for structure inspection are missing.")
    else:
        print(f"Error: {fund_master_name} was not loaded. Cannot explore fund master.")
        
    # Task 4: Validate AMFI Codes
    print("\n" + "=" * 80)
    print(" TASK 4: VALIDATE AMFI CODES")
    print("=" * 80)
    
    nav_history_name = "02_nav_history.csv"
    if fund_master_name in loaded_datasets and nav_history_name in loaded_datasets:
        fund_master = loaded_datasets[fund_master_name]
        nav_history = loaded_datasets[nav_history_name]
        
        master_codes = set(fund_master["amfi_code"])
        nav_codes = set(nav_history["amfi_code"])
        missing_codes = master_codes - nav_codes
        
        print(f"Total AMFI codes in fund master: {len(master_codes)}")
        print(f"Total AMFI codes in NAV history: {len(nav_codes)}")
        print(f"Number of missing codes: {len(missing_codes)}")
        if missing_codes:
            print("Missing AMFI codes (in fund master but missing in NAV history):")
            print(sorted(list(missing_codes)))
        else:
            print("All AMFI codes in fund master exist in NAV history.")
    else:
        print("Error: Fund master or NAV history not loaded. Cannot validate AMFI codes.")
        
    print("\n" + "=" * 80)
    print(" DATA INGESTION & ANALYSIS COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    run_data_ingestion()
