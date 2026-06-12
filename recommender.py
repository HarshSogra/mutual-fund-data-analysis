"""Simple fund recommender by risk category (Day 6)."""
import pandas as pd

DATA_DIR = "data/processed"

RISK_GROUPS = {
    "Low": ["Low"],
    "Moderate": ["Moderate", "Moderately High"],
    "High": ["High", "Very High"],
}


def get_recommendations(risk_input: str) -> pd.DataFrame:
    """Return top 3 funds for the given risk category, ranked by Sharpe ratio."""
    risk_input = risk_input.strip().title()
    if risk_input not in RISK_GROUPS:
        raise ValueError(f"Invalid risk category. Choose from: {', '.join(RISK_GROUPS)}")

    fund_df = pd.read_csv(f"{DATA_DIR}/01_fund_master.csv")
    perf_df = pd.read_csv(f"{DATA_DIR}/07_scheme_performance.csv")

    merged = fund_df.merge(
        perf_df[["amfi_code", "sharpe_ratio"]], on="amfi_code", how="inner"
    )
    filtered = merged[merged["risk_category"].isin(RISK_GROUPS[risk_input])]
    top3 = filtered.sort_values("sharpe_ratio", ascending=False).head(3)

    return top3[["scheme_name", "fund_house", "risk_category", "sharpe_ratio"]].rename(
        columns={
            "scheme_name": "Scheme Name",
            "fund_house": "Fund House",
            "risk_category": "Risk Category",
            "sharpe_ratio": "Sharpe Ratio",
        }
    )


def main() -> None:
    print("=" * 50)
    print(" Bluestock Fund Recommender")
    print("=" * 50)
    print("Enter risk category: Low | Moderate | High")
    risk = input("Risk category: ").strip()

    try:
        results = get_recommendations(risk)
    except ValueError as e:
        print(f"Error: {e}")
        return

    if results.empty:
        print(f"No funds found for risk category '{risk}'.")
        return

    print(f"\nTop 3 recommended funds for '{risk.title()}' risk:\n")
    print(results.to_string(index=False))
    print()


if __name__ == "__main__":
    main()
