import os
import pandas as pd
from sqlalchemy import create_engine, text

def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    db_path = os.path.join(base_dir, 'bluestock_mf.db')
    schema_path = os.path.join(base_dir, 'sql', 'schema.sql')
    
    print("=" * 60)
    print(" DAY 2: LOADING DATA INTO SQLITE")
    print("=" * 60)
    
    # 1. Reset database file if it exists to ensure idempotent fresh load
    if os.path.exists(db_path):
        print(f"Removing existing database file: {db_path}")
        os.remove(db_path)
        
    # 2. Connect to SQLite and apply DDL schema
    engine = create_engine(f"sqlite:///{db_path}")
    
    if not os.path.exists(schema_path):
        print(f"Error: Schema SQL file not found at {schema_path}")
        return
        
    print("Executing schema.sql DDL script...")
    with open(schema_path, 'r') as f:
        schema_ddl = f.read()
        
    statements = [stmt.strip() for stmt in schema_ddl.split(';') if stmt.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
    print("Database tables initialized.")
    
    # 3. Read processed CSV files
    print("\nReading processed CSV datasets...")
    df_fund = pd.read_csv(os.path.join(processed_dir, '01_fund_master.csv'))
    df_nav = pd.read_csv(os.path.join(processed_dir, '02_nav_history.csv'))
    df_aum = pd.read_csv(os.path.join(processed_dir, '03_aum_by_fund_house.csv'))
    df_perf = pd.read_csv(os.path.join(processed_dir, '07_scheme_performance.csv'))
    df_txn = pd.read_csv(os.path.join(processed_dir, '08_investor_transactions.csv'))
    
    # 4. Create and populate dim_date dynamically using unique dates
    print("Building dim_date table from available dates...")
    unique_dates = set()
    unique_dates.update(df_nav['date'].dropna().unique())
    unique_dates.update(df_txn['transaction_date'].dropna().unique())
    unique_dates.update(df_aum['date'].dropna().unique())
    
    sorted_dates = sorted(list(unique_dates))
    date_objects = pd.to_datetime(sorted_dates)
    
    df_date = pd.DataFrame({
        'date': sorted_dates,
        'year': date_objects.year,
        'month': date_objects.month,
        'day': date_objects.day,
        'quarter': date_objects.quarter,
        'month_name': date_objects.strftime('%B'),
        'day_name': date_objects.strftime('%A')
    })
    print(f"  * Generated {len(df_date)} unique dates in dim_date.")
    
    # 5. Load datasets using pandas to_sql
    tables_to_load = [
        (df_fund, 'dim_fund'),
        (df_date, 'dim_date'),
        (df_nav, 'fact_nav'),
        (df_txn, 'fact_transactions'),
        (df_perf, 'fact_performance'),
        (df_aum, 'fact_aum')
    ]
    
    print("\nLoading tables into SQLite...")
    for df, table_name in tables_to_load:
        # Since table was created by DDL, we use if_exists='append'
        # For fact_transactions, we drop transaction_id column from df if it's not present (SQLite handles autoincrement primary key)
        df_to_load = df.copy()
        if table_name == 'fact_transactions' and 'transaction_id' not in df_to_load.columns:
            # Let the database handle the autoincrement PK
            pass
            
        df_to_load.to_sql(table_name, con=engine, if_exists='append', index=False)
        print(f"  * Table '{table_name}' loaded successfully.")
        
    # 6. Verify row counts match
    print("\n" + "=" * 40)
    print(" ROW COUNT VERIFICATION LOGS")
    print("=" * 40)
    
    verification_passed = True
    with engine.connect() as conn:
        for df, table_name in tables_to_load:
            res = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            db_count = res.scalar()
            csv_count = len(df)
            
            status = "PASS" if db_count == csv_count else "FAIL"
            print(f"Table '{table_name}': SQLite Count = {db_count} | Source CSV Count = {csv_count} | Status = {status}")
            if status == "FAIL":
                verification_passed = False
                
    print("=" * 40)
    if verification_passed:
        print("Verification SUCCESS: All SQLite row counts match source datasets.")
    else:
        print("Verification FAILURE: Row counts do not match. Check errors.")
        
    print("=" * 60)

if __name__ == "__main__":
    load_data()
