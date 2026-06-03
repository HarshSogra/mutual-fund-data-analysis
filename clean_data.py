import os
import pandas as pd
import numpy as np

def clean_dataset_01(df):
    """01_fund_master.csv: Clean duplicates and standardize date."""
    df = df.drop_duplicates()
    if 'launch_date' in df.columns:
        df['launch_date'] = pd.to_datetime(df['launch_date']).dt.strftime('%Y-%m-%d')
    return df

def clean_dataset_02(df):
    """02_nav_history.csv: Datetime parsing, sort, remove duplicates, validate nav > 0, forward-fill."""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['amfi_code', 'date'])
    df = df.drop_duplicates()
    
    # Validate NAV values are greater than 0
    invalid_nav_count = (df['nav'] <= 0).sum()
    if invalid_nav_count > 0:
        print(f"  * Warning: Found {invalid_nav_count} NAV records with values <= 0. Removing them.")
        df = df[df['nav'] > 0]
        
    # Forward-fill missing NAV values grouped by amfi_code
    df['nav'] = df.groupby('amfi_code')['nav'].ffill()
    
    # Format date back to string YYYY-MM-DD
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    return df

def clean_dataset_03(df):
    """03_aum_by_fund_house.csv: Clean duplicates and standardize date."""
    df = df.drop_duplicates()
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    return df

def clean_dataset_04(df):
    """04_monthly_sip_inflows.csv: Clean duplicates, handle missing values, standardize month."""
    df = df.drop_duplicates().copy()
    if 'month' in df.columns:
        df['month'] = pd.to_datetime(df['month'], format='%Y-%m').dt.strftime('%Y-%m')
    if 'yoy_growth_pct' in df.columns:
        # Fill missing growth rates with 0.0 or leave it as NaN. Let's fill it for clean analysis.
        missing_count = df['yoy_growth_pct'].isnull().sum()
        if missing_count > 0:
            print(f"  * Filling {missing_count} missing values in 'yoy_growth_pct' with 0.0.")
            df['yoy_growth_pct'] = df['yoy_growth_pct'].fillna(0.0)
    return df

def clean_dataset_05(df):
    """05_category_inflows.csv: Clean duplicates and standardize month."""
    df = df.drop_duplicates().copy()
    if 'month' in df.columns:
        df['month'] = pd.to_datetime(df['month'], format='%Y-%m').dt.strftime('%Y-%m')
    return df

def clean_dataset_06(df):
    """06_industry_folio_count.csv: Clean duplicates and standardize month."""
    df = df.drop_duplicates().copy()
    if 'month' in df.columns:
        df['month'] = pd.to_datetime(df['month'], format='%Y-%m').dt.strftime('%Y-%m')
    return df

def clean_dataset_07(df):
    """07_scheme_performance.csv: Ensure return columns are numeric, validate expense ratio."""
    df = df.copy()
    return_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct']
    for col in return_cols:
        if col in df.columns:
            # Check for non-numeric/invalid values
            invalid_mask = pd.to_numeric(df[col], errors='coerce').isna() & df[col].notna()
            if invalid_mask.any():
                print(f"  * Warning: Found non-numeric values in performance '{col}':")
                print(df[invalid_mask][['amfi_code', 'scheme_name', col]])
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Validate expense_ratio_pct is within 0.1 to 2.5
    if 'expense_ratio_pct' in df.columns:
        out_of_bounds = df[(df['expense_ratio_pct'] < 0.1) | (df['expense_ratio_pct'] > 2.5)]
        if not out_of_bounds.empty:
            print(f"  * Warning: Found {len(out_of_bounds)} schemes with expense_ratio_pct outside [0.1, 2.5]:")
            print(out_of_bounds[['amfi_code', 'scheme_name', 'expense_ratio_pct']])
            
    df = df.drop_duplicates()
    return df

def clean_dataset_08(df):
    """08_investor_transactions.csv: Standardize transaction type, fix date formats, validate amount > 0, inspect KYC."""
    df = df.copy()
    
    # 1. Standardize transaction_type
    if 'transaction_type' in df.columns:
        df['transaction_type'] = df['transaction_type'].astype(str).str.strip()
        txn_map = {
            'sip': 'SIP',
            'lumpsum': 'Lumpsum',
            'redemption': 'Redemption'
        }
        df['transaction_type'] = df['transaction_type'].str.lower().map(txn_map).fillna(df['transaction_type'])
        
    # 2. Fix date formats
    if 'transaction_date' in df.columns:
        df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.strftime('%Y-%m-%d')
        
    # 3. Validate amount > 0
    if 'amount_inr' in df.columns:
        invalid_amount_count = (df['amount_inr'] <= 0).sum()
        if invalid_amount_count > 0:
            print(f"  * Warning: Found {invalid_amount_count} transactions with amount_inr <= 0. Removing them.")
            df = df[df['amount_inr'] > 0]
            
    # 4. Check KYC status values and identify unexpected values
    if 'kyc_status' in df.columns:
        unique_kyc = df['kyc_status'].astype(str).str.strip().unique()
        print(f"  * Unique KYC status values found: {list(unique_kyc)}")
        # Check for inconsistent capitalization or unexpected strings
        expected_status = {'Verified', 'Pending'}
        unexpected_kyc = [status for status in unique_kyc if status not in expected_status]
        if unexpected_kyc:
            print(f"  * Warning: Found unexpected KYC status entries: {unexpected_kyc}")
            
    df = df.drop_duplicates()
    return df

def clean_dataset_09(df):
    """09_portfolio_holdings.csv: Clean duplicates and standardize date."""
    df = df.drop_duplicates()
    if 'portfolio_date' in df.columns:
        df['portfolio_date'] = pd.to_datetime(df['portfolio_date']).dt.strftime('%Y-%m-%d')
    return df

def clean_dataset_10(df):
    """10_benchmark_indices.csv: Clean duplicates and standardize date."""
    df = df.drop_duplicates()
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    return df

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(base_dir, 'data', 'raw')
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    
    datasets = {
        "01_fund_master.csv": clean_dataset_01,
        "02_nav_history.csv": clean_dataset_02,
        "03_aum_by_fund_house.csv": clean_dataset_03,
        "04_monthly_sip_inflows.csv": clean_dataset_04,
        "05_category_inflows.csv": clean_dataset_05,
        "06_industry_folio_count.csv": clean_dataset_06,
        "07_scheme_performance.csv": clean_dataset_07,
        "08_investor_transactions.csv": clean_dataset_08,
        "09_portfolio_holdings.csv": clean_dataset_09,
        "10_benchmark_indices.csv": clean_dataset_10
    }
    
    print("=" * 60)
    print(" DAY 2: CLEANING MUTUAL FUND DATASETS")
    print("=" * 60)
    
    for filename, clean_func in datasets.items():
        raw_path = os.path.join(raw_dir, filename)
        processed_path = os.path.join(processed_dir, filename)
        
        if not os.path.exists(raw_path):
            print(f"Error: Raw file {filename} not found at {raw_path}")
            continue
            
        print(f"\nCleaning {filename}...")
        df = pd.read_csv(raw_path)
        initial_shape = df.shape
        
        df_cleaned = clean_func(df)
        final_shape = df_cleaned.shape
        
        # Save to processed directory
        df_cleaned.to_csv(processed_path, index=False)
        print(f"Saved: {filename} (Raw: {initial_shape} -> Cleaned: {final_shape})")
        
    print("\n" + "=" * 60)
    print(" DATA CLEANING PROCESS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
