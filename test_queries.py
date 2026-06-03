import sqlite3

db_path = "bluestock_mf.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Test a few analytical queries
queries = [
    ("Top 5 funds by AUM", """
        SELECT scheme_name, aum_crore 
        FROM fact_performance
        ORDER BY aum_crore DESC
        LIMIT 5;
    """),
    ("Average NAV per month (first 5)", """
        SELECT strftime('%Y-%m', date) AS month, ROUND(AVG(nav), 4) AS avg_nav
        FROM fact_nav
        GROUP BY month
        ORDER BY month
        LIMIT 5;
    """),
    ("Transactions by state (top 5)", """
        SELECT state, COUNT(*) AS transaction_count, SUM(amount_inr) AS total_amount_inr
        FROM fact_transactions
        GROUP BY state
        ORDER BY total_amount_inr DESC
        LIMIT 5;
    """)
]

print("=" * 60)
print(" TESTING ANALYTICAL SQL QUERIES")
print("=" * 60)

for title, query in queries:
    print(f"\n{title}:")
    try:
        result = cursor.execute(query).fetchall()
        if result:
            for row in result[:5]:
                print(f"  {row}")
        else:
            print("  (No results)")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "=" * 60)
conn.close()
