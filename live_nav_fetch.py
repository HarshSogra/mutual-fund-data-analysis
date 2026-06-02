import os
import requests
import pandas as pd

def fetch_scheme_nav(amfi_code, output_filename):
    url = f"https://api.mfapi.in/mf/{amfi_code}"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, 'data', 'raw', output_filename)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        payload = response.json()
        
        meta = payload.get("meta", {})
        data_list = payload.get("data", [])
        
        scheme_name = meta.get("scheme_name", "Unknown Scheme")
        scheme_code = meta.get("scheme_code", amfi_code)
        num_records = len(data_list)
        
        # Save NAV history to CSV
        if num_records > 0:
            df = pd.DataFrame(data_list)
            # Reorder/ensure columns: date, nav
            df = df[['date', 'nav']]
            
            # Format dates from DD-MM-YYYY to YYYY-MM-DD for standard format consistency
            try:
                df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y').dt.strftime('%Y-%m-%d')
            except Exception as e:
                # Fallback to saving raw dates if conversion fails
                pass
                
            df.to_csv(output_path, index=False)
            
            print(f"Scheme Name: {scheme_name}")
            print(f"AMFI Code:   {scheme_code}")
            print(f"Records:     {num_records} fetched and saved to {output_filename}")
        else:
            print(f"Warning: No data found for AMFI code {amfi_code}")
            
        print("-" * 50)
        return True
        
    except requests.exceptions.RequestException as re:
        print(f"Network error fetching AMFI code {amfi_code}: {re}")
        print("-" * 50)
        return False
    except Exception as e:
        print(f"Unexpected error fetching AMFI code {amfi_code}: {e}")
        print("-" * 50)
        return False

def main():
    print("=" * 60)
    print(" FETCHING LIVE NAV DATA FROM MFAPI")
    print("=" * 60)
    
    # 1. Scheme 1
    fetch_scheme_nav(125497, "live_nav_125497.csv")
    
    # 2. Additional 5 key schemes
    schemes = [
        (119551, "sbi_bluechip_nav.csv"),
        (120503, "icici_bluechip_nav.csv"),
        (118632, "nippon_large_cap_nav.csv"),
        (119092, "axis_bluechip_nav.csv"),
        (120841, "kotak_bluechip_nav.csv")
    ]
    
    for code, filename in schemes:
        fetch_scheme_nav(code, filename)
        
    print("LIVE NAV FETCH COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
