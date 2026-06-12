"""
Day 5: Build Bluestock Mutual Fund Power BI dashboard and export deliverables.

Outputs:
  - bluestock_mf_dashboard.pbix
  - Dashboard.pdf
  - reports/dashboard/page1_industry_overview.png
  - reports/dashboard/page2_fund_performance.png
  - reports/dashboard/page3_investor_analytics.png
  - reports/dashboard/page4_sip_market_trends.png
"""
from __future__ import annotations

import json
import uuid
import zipfile
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from pbix_mcp.builder import PBIXBuilder

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"
DASHBOARD_DIR = BASE_DIR / "reports" / "dashboard"
PBIX_PATH = BASE_DIR / "bluestock_mf_dashboard.pbix"
PDF_PATH = BASE_DIR / "Dashboard.pdf"
LOGO_PATH = DASHBOARD_DIR / "bluestock_logo.png"

# Bluestock brand palette
BLUESTOCK = {
    "primary": "#1E40AF",
    "secondary": "#2563EB",
    "accent": "#0EA5E9",
    "light": "#DBEAFE",
    "bg": "#F8FAFC",
    "text": "#1E293B",
    "muted": "#64748B",
    "palette": ["#1E40AF", "#2563EB", "#3B82F6", "#0EA5E9", "#06B6D4", "#8B5CF6"],
}


def load_datasets() -> dict[str, pd.DataFrame]:
    """Load and prepare all dashboard datasets."""
    dfs = {
        "dim_fund": pd.read_csv(DATA_DIR / "01_fund_master.csv"),
        "fact_nav": pd.read_csv(DATA_DIR / "02_nav_history.csv"),
        "fact_aum": pd.read_csv(DATA_DIR / "03_aum_by_fund_house.csv"),
        "monthly_sip": pd.read_csv(DATA_DIR / "04_monthly_sip_inflows.csv"),
        "category_inflows": pd.read_csv(DATA_DIR / "05_category_inflows.csv"),
        "industry_folio": pd.read_csv(DATA_DIR / "06_industry_folio_count.csv"),
        "fact_performance": pd.read_csv(DATA_DIR / "07_scheme_performance.csv"),
        "fact_transactions": pd.read_csv(DATA_DIR / "08_investor_transactions.csv"),
        "fund_scorecard": pd.read_csv(DATA_DIR / "fund_scorecard.csv"),
        "alpha_beta": pd.read_csv(DATA_DIR / "alpha_beta.csv"),
        "benchmark_indices": pd.read_csv(DATA_DIR / "10_benchmark_indices.csv"),
    }

    # Date dimension
    dates = set()
    for col_df, col in [
        (dfs["fact_nav"], "date"),
        (dfs["fact_aum"], "date"),
        (dfs["fact_transactions"], "transaction_date"),
        (dfs["benchmark_indices"], "date"),
    ]:
        dates.update(col_df[col].dropna().unique())
    date_idx = pd.to_datetime(sorted(dates))
    dfs["dim_date"] = pd.DataFrame({
        "date": date_idx.strftime("%Y-%m-%d"),
        "year": date_idx.year,
        "month": date_idx.month,
        "quarter": date_idx.quarter,
    })

    # Industry AUM trend (sum across AMCs by date)
    dfs["industry_aum_trend"] = (
        dfs["fact_aum"].groupby("date", as_index=False)["aum_crore"].sum()
        .rename(columns={"aum_crore": "total_aum_crore"})
    )

    # Latest AUM snapshot per fund house (for bar chart)
    latest_aum_date = dfs["fact_aum"]["date"].max()
    dfs["aum_latest"] = dfs["fact_aum"][dfs["fact_aum"]["date"] == latest_aum_date].copy()

    # SIP + Nifty 50 monthly merge for dual-axis page
    bench = dfs["benchmark_indices"].copy()
    bench["date"] = pd.to_datetime(bench["date"])
    bench["month"] = bench["date"].dt.strftime("%Y-%m")
    nifty50_monthly = (
        bench[bench["index_name"] == "NIFTY50"]
        .sort_values("date")
        .groupby("month", as_index=False)
        .last()[["month", "close_value"]]
        .rename(columns={"close_value": "nifty50_close"})
    )
    dfs["sip_nifty"] = dfs["monthly_sip"].merge(nifty50_monthly, on="month", how="left")

    # FY25 top categories (aggregated)
    cat = dfs["category_inflows"].copy()
    cat_fy25 = cat[cat["month"] >= "2025-01"].groupby("category", as_index=False)["net_inflow_crore"].sum()
    cat_fy25 = cat_fy25.sort_values("net_inflow_crore", ascending=False)
    dfs["category_fy25"] = cat_fy25

    # NAV vs benchmark indexed (last 3 years, all funds)
    nav = dfs["fact_nav"].copy()
    nav["date"] = pd.to_datetime(nav["date"])
    end = nav["date"].max()
    start = end - pd.DateOffset(years=3)
    nav = nav[nav["date"] >= start]
    bench_idx = bench[bench["date"] >= start].copy()
    nifty50 = bench_idx[bench_idx["index_name"] == "NIFTY50"].sort_values("date")
    nifty100 = bench_idx[bench_idx["index_name"] == "NIFTY100"].sort_values("date")
    n50_base = nifty50["close_value"].iloc[0]
    n100_base = nifty100["close_value"].iloc[0]
    bench_lines = pd.DataFrame({
        "date": nifty50["date"].dt.strftime("%Y-%m-%d"),
        "amfi_code": 0,
        "scheme_name": "Nifty 50",
        "indexed_value": (nifty50["close_value"] / n50_base * 100).values,
    })
    bench_lines2 = pd.DataFrame({
        "date": nifty100["date"].dt.strftime("%Y-%m-%d"),
        "amfi_code": -1,
        "scheme_name": "Nifty 100",
        "indexed_value": (nifty100["close_value"] / n100_base * 100).values,
    })
    nav_rows = []
    for code, grp in nav.groupby("amfi_code"):
        grp = grp.sort_values("date")
        base = grp["nav"].iloc[0]
        name = dfs["dim_fund"].loc[dfs["dim_fund"]["amfi_code"] == code, "scheme_name"]
        scheme = name.iloc[0] if len(name) else str(code)
        for _, row in grp.iterrows():
            nav_rows.append({
                "date": row["date"].strftime("%Y-%m-%d"),
                "amfi_code": int(code),
                "scheme_name": scheme[:40],
                "indexed_value": round(row["nav"] / base * 100, 2),
            })
    dfs["nav_vs_benchmark"] = pd.concat(
        [pd.DataFrame(nav_rows), bench_lines, bench_lines2], ignore_index=True
    )

    # KPI snapshot values
    dfs["kpi_snapshot"] = pd.DataFrame([{
        "total_aum_crore": dfs["industry_aum_trend"]["total_aum_crore"].iloc[-1],
        "total_sip_inflows_crore": dfs["monthly_sip"]["sip_inflow_crore"].sum(),
        "total_folios_crore": dfs["industry_folio"]["total_folios_crore"].iloc[-1],
        "total_schemes": len(dfs["dim_fund"]),
    }])

    return dfs


def df_rows(df: pd.DataFrame, int_cols: list[str] | None = None) -> list[dict]:
    """Convert DataFrame to list of row dicts for PBIXBuilder."""
    out = df.copy()
    for col in int_cols or []:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)
    records = []
    for row in out.to_dict(orient="records"):
        clean = {}
        for k, v in row.items():
            if pd.isna(v):
                clean[k] = None
            elif isinstance(v, (np.integer,)):
                clean[k] = int(v)
            elif isinstance(v, (np.floating,)):
                clean[k] = float(v)
            else:
                clean[k] = v
        records.append(clean)
    return records


def col_defs(df: pd.DataFrame, overrides: dict[str, str] | None = None) -> list[dict]:
    """Infer PBIX column definitions from a DataFrame."""
    overrides = overrides or {}
    type_map = {
        "int64": "Int64", "Int64": "Int64",
        "float64": "Double", "Float64": "Double",
        "object": "String", "string": "String",
        "bool": "Boolean",
    }
    cols = []
    for name in df.columns:
        dtype = str(df[name].dtype)
        cols.append({"name": name, "data_type": overrides.get(name, type_map.get(dtype, "String"))})
    return cols


def build_pbix(dfs: dict[str, pd.DataFrame]) -> None:
    """Create the Power BI dashboard file with data model and report pages."""
    builder = PBIXBuilder("Bluestock MF Model")
    csv_base = str(DATA_DIR.resolve())

    table_specs = [
        ("dim_fund", dfs["dim_fund"], {"amfi_code": "Int64", "min_sip_amount": "Int64", "min_lumpsum_amount": "Int64"}),
        ("dim_date", dfs["dim_date"], {"year": "Int64", "month": "Int64", "quarter": "Int64"}),
        ("fact_nav", dfs["fact_nav"], {"amfi_code": "Int64"}),
        ("fact_aum", dfs["fact_aum"], {"aum_crore": "Int64", "num_schemes": "Int64"}),
        ("aum_latest", dfs["aum_latest"], {"aum_crore": "Int64", "num_schemes": "Int64"}),
        ("industry_aum_trend", dfs["industry_aum_trend"], {}),
        ("monthly_sip", dfs["monthly_sip"], {}),
        ("sip_nifty", dfs["sip_nifty"], {}),
        ("category_inflows", dfs["category_inflows"], {}),
        ("category_fy25", dfs["category_fy25"], {}),
        ("industry_folio", dfs["industry_folio"], {}),
        ("fact_performance", dfs["fact_performance"], {"amfi_code": "Int64", "aum_crore": "Int64", "morningstar_rating": "Int64"}),
        ("fact_transactions", dfs["fact_transactions"], {"amfi_code": "Int64", "amount_inr": "Int64"}),
        ("fund_scorecard", dfs["fund_scorecard"], {"amfi_code": "Int64", "overall_rank": "Int64"}),
        ("alpha_beta", dfs["alpha_beta"], {"amfi_code": "Int64", "observations": "Int64"}),
        ("benchmark_indices", dfs["benchmark_indices"], {}),
        ("nav_vs_benchmark", dfs["nav_vs_benchmark"], {"amfi_code": "Int64"}),
        ("kpi_snapshot", dfs["kpi_snapshot"], {"total_schemes": "Int64"}),
    ]

    source_files = {
        "dim_fund": "01_fund_master.csv",
        "fact_nav": "02_nav_history.csv",
        "fact_aum": "03_aum_by_fund_house.csv",
        "monthly_sip": "04_monthly_sip_inflows.csv",
        "category_inflows": "05_category_inflows.csv",
        "industry_folio": "06_industry_folio_count.csv",
        "fact_performance": "07_scheme_performance.csv",
        "fact_transactions": "08_investor_transactions.csv",
        "fund_scorecard": "fund_scorecard.csv",
        "alpha_beta": "alpha_beta.csv",
        "benchmark_indices": "10_benchmark_indices.csv",
    }

    int_cols_map = {
        "dim_fund": ["amfi_code", "min_sip_amount", "min_lumpsum_amount"],
        "fact_nav": ["amfi_code"],
        "fact_aum": ["aum_crore", "num_schemes"],
        "fact_performance": ["amfi_code", "aum_crore", "morningstar_rating"],
        "fact_transactions": ["amfi_code", "amount_inr"],
        "fund_scorecard": ["amfi_code", "overall_rank"],
        "alpha_beta": ["amfi_code", "observations"],
        "nav_vs_benchmark": ["amfi_code"],
    }

    for name, df, overrides in table_specs:
        csv_name = source_files.get(name)
        source_csv = str((DATA_DIR / csv_name).resolve()) if csv_name else None
        builder.add_table(
            name,
            col_defs(df, overrides),
            rows=df_rows(df, int_cols_map.get(name)),
            source_csv=source_csv,
        )

    # Relationships on amfi_code and date
    rels = [
        ("fact_nav", "amfi_code", "dim_fund", "amfi_code"),
        ("fact_nav", "date", "dim_date", "date"),
        ("fact_aum", "date", "dim_date", "date"),
        ("fact_performance", "amfi_code", "dim_fund", "amfi_code"),
        ("fact_transactions", "amfi_code", "dim_fund", "amfi_code"),
        ("fact_transactions", "transaction_date", "dim_date", "date"),
        ("fund_scorecard", "amfi_code", "dim_fund", "amfi_code"),
        ("alpha_beta", "amfi_code", "dim_fund", "amfi_code"),
        ("benchmark_indices", "date", "dim_date", "date"),
    ]
    for fr, fc, tt, tc in rels:
        try:
            builder.add_relationship(fr, fc, tt, tc)
        except Exception:
            pass  # skip benchmark/dim_date if column mismatch

    # DAX measures
    measures = [
        ("kpi_snapshot", "Total AUM", "SUM(kpi_snapshot[total_aum_crore])"),
        ("kpi_snapshot", "SIP Inflows", "SUM(kpi_snapshot[total_sip_inflows_crore])"),
        ("kpi_snapshot", "Total Folios", "SUM(kpi_snapshot[total_folios_crore])"),
        ("kpi_snapshot", "Total Schemes", "SUM(kpi_snapshot[total_schemes])"),
        ("industry_aum_trend", "Industry AUM", "SUM(industry_aum_trend[total_aum_crore])"),
        ("aum_latest", "AUM by AMC", "SUM(aum_latest[aum_crore])"),
        ("monthly_sip", "Monthly SIP", "SUM(monthly_sip[sip_inflow_crore])"),
        ("sip_nifty", "SIP Inflow", "SUM(sip_nifty[sip_inflow_crore])"),
        ("sip_nifty", "Nifty 50 Close", "AVERAGE(sip_nifty[nifty50_close])"),
        ("category_inflows", "Net Inflow", "SUM(category_inflows[net_inflow_crore])"),
        ("category_fy25", "FY25 Net Inflow", "SUM(category_fy25[net_inflow_crore])"),
        ("fact_transactions", "Transaction Amount", "SUM(fact_transactions[amount_inr])"),
        ("fact_transactions", "Transaction Count", "COUNTROWS(fact_transactions)"),
        ("fact_performance", "Avg Return 3Y", "AVERAGE(fact_performance[return_3yr_pct])"),
        ("fact_performance", "Avg Risk", "AVERAGE(fact_performance[std_dev_ann_pct])"),
        ("fact_performance", "Total AUM Perf", "SUM(fact_performance[aum_crore])"),
        ("nav_vs_benchmark", "Indexed NAV", "AVERAGE(nav_vs_benchmark[indexed_value])"),
        ("fact_nav", "Avg NAV", "AVERAGE(fact_nav[nav])"),
        ("fund_scorecard", "Fund Score", "AVERAGE(fund_scorecard[fund_score])"),
    ]
    for table, name, expr in measures:
        builder.add_measure(table, name, expr)

    # Page 1 – Industry Overview
    builder.add_page("Industry Overview", visuals=[
        {"type": "card", "x": 20, "y": 20, "width": 280, "height": 110,
         "config": {"measure": "Total AUM"}},
        {"type": "card", "x": 320, "y": 20, "width": 280, "height": 110,
         "config": {"measure": "SIP Inflows"}},
        {"type": "card", "x": 620, "y": 20, "width": 280, "height": 110,
         "config": {"measure": "Total Folios"}},
        {"type": "card", "x": 920, "y": 20, "width": 280, "height": 110,
         "config": {"measure": "Total Schemes"}},
        {"type": "lineChart", "x": 20, "y": 150, "width": 780, "height": 380,
         "config": {"category": {"table": "industry_aum_trend", "column": "date"},
                    "measure": "Industry AUM"}},
        {"type": "clusteredBarChart", "x": 820, "y": 150, "width": 400, "height": 380,
         "config": {"category": {"table": "aum_latest", "column": "fund_house"},
                    "measure": "AUM by AMC"}},
    ])

    # Page 2 – Fund Performance
    builder.add_page("Fund Performance", visuals=[
        {"type": "slicer", "x": 20, "y": 20, "width": 200, "height": 100,
         "config": {"column": {"table": "dim_fund", "column": "fund_house"}}},
        {"type": "slicer", "x": 240, "y": 20, "width": 200, "height": 100,
         "config": {"column": {"table": "dim_fund", "column": "category"}}},
        {"type": "slicer", "x": 460, "y": 20, "width": 200, "height": 100,
         "config": {"column": {"table": "dim_fund", "column": "plan"}}},
        {"type": "tableEx", "x": 20, "y": 140, "width": 580, "height": 400,
         "config": {"columns": [
             {"table": "fund_scorecard", "column": "overall_rank"},
             {"table": "fund_scorecard", "column": "scheme_name"},
             {"table": "fund_scorecard", "column": "fund_score"},
             {"table": "fund_scorecard", "column": "cagr_3yr_pct"},
             {"table": "fund_scorecard", "column": "sharpe_ratio"},
             {"table": "fund_scorecard", "column": "alpha_pct"},
         ]}},
        {"type": "lineChart", "x": 20, "y": 560, "width": 1220, "height": 150,
         "config": {"category": {"table": "nav_vs_benchmark", "column": "date"},
                    "measure": "Indexed NAV"}},
    ])

    # Page 3 – Investor Analytics
    builder.add_page("Investor Analytics", visuals=[
        {"type": "slicer", "x": 20, "y": 20, "width": 180, "height": 100,
         "config": {"column": {"table": "fact_transactions", "column": "state"}}},
        {"type": "slicer", "x": 220, "y": 20, "width": 180, "height": 100,
         "config": {"column": {"table": "fact_transactions", "column": "age_group"}}},
        {"type": "slicer", "x": 420, "y": 20, "width": 180, "height": 100,
         "config": {"column": {"table": "fact_transactions", "column": "city_tier"}}},
        {"type": "clusteredBarChart", "x": 20, "y": 140, "width": 500, "height": 350,
         "config": {"category": {"table": "fact_transactions", "column": "state"},
                    "measure": "Transaction Amount"}},
        {"type": "donutChart", "x": 540, "y": 140, "width": 350, "height": 350,
         "config": {"category": {"table": "fact_transactions", "column": "transaction_type"},
                    "measure": "Transaction Amount"}},
        {"type": "clusteredBarChart", "x": 910, "y": 140, "width": 350, "height": 350,
         "config": {"category": {"table": "fact_transactions", "column": "age_group"},
                    "measure": "Transaction Amount"}},
        {"type": "lineChart", "x": 20, "y": 510, "width": 1240, "height": 200,
         "config": {"category": {"table": "fact_transactions", "column": "transaction_date"},
                    "measure": "Transaction Count"}},
    ])

    # Page 4 – SIP & Market Trends
    builder.add_page("SIP & Market Trends", visuals=[
        {"type": "clusteredColumnChart", "x": 20, "y": 20, "width": 700, "height": 350,
         "config": {"category": {"table": "sip_nifty", "column": "month"},
                    "measure": "SIP Inflow"}},
        {"type": "lineChart", "x": 20, "y": 20, "width": 700, "height": 350,
         "config": {"category": {"table": "sip_nifty", "column": "month"},
                    "measure": "Nifty 50 Close"}},
        {"type": "matrix", "x": 740, "y": 20, "width": 520, "height": 350,
         "config": {"columns": [
             {"table": "category_inflows", "column": "category"},
             {"table": "category_inflows", "column": "month"},
             {"table": "category_inflows", "column": "net_inflow_crore"},
         ]}},
        {"type": "clusteredBarChart", "x": 20, "y": 390, "width": 1240, "height": 320,
         "config": {"category": {"table": "category_fy25", "column": "category"},
                    "measure": "FY25 Net Inflow"}},
    ])

    # Page 5 – NAV Detail (drill-through target)
    builder.add_page("NAV Detail", visuals=[
        {"type": "lineChart", "x": 20, "y": 80, "width": 1240, "height": 600,
         "config": {"category": {"table": "fact_nav", "column": "date"},
                    "measure": "Avg NAV"}},
    ])

    builder.save(str(PBIX_PATH))
    print(f"Created base PBIX: {PBIX_PATH}")


def _make_visual_config(visual_type: str, name: str, projections: dict, prototype_query: dict) -> str:
    """Build a serialized Power BI visual configuration payload."""
    return json.dumps({
        "name": name,
        "singleVisual": {
            "visualType": visual_type,
            "drillFilterOtherVisuals": True,
            "projections": projections,
            "prototypeQuery": prototype_query,
        },
    })


def post_process_pbix(logo_path: Path) -> None:
    """Add Bluestock theme, logo, scatter plot, tooltips, and drill-through."""
    theme = {
        "name": "Bluestock",
        "dataColors": BLUESTOCK["palette"],
        "foreground": BLUESTOCK["text"],
        "foregroundNeutralSecondary": BLUESTOCK["muted"],
        "background": BLUESTOCK["bg"],
        "backgroundLight": BLUESTOCK["light"],
        "tableAccent": BLUESTOCK["primary"],
        "good": "#16A34A",
        "bad": "#DC2626",
        "neutral": BLUESTOCK["muted"],
    }

    buf = BytesIO()
    with zipfile.ZipFile(PBIX_PATH, "r") as zin:
        layout_raw = zin.read("Report/Layout").decode("utf-16-le")
        layout = json.loads(layout_raw)

        # Enhanced tooltips
        layout.setdefault("config", json.dumps({
            "version": "1.0",
            "themeCollection": {
                "baseTheme": {"name": "Bluestock", "type": 2, "version": {"visual": "1.8", "report": "2.0", "page": "1.3"}},
            },
        }))
        layout["resourcePackages"] = [{
            "name": "SharedResources",
            "type": 2,
            "items": [{
                "name": "Bluestock.json",
                "path": "BaseThemes/Bluestock.json",
                "type": 202,
            }],
        }]

        sections = layout.get("sections", [])
        for section in sections:
            section.setdefault("config", "{}")
            if section.get("displayName") == "NAV Detail":
                section["config"] = json.dumps({"visibility": 1})
                section["filters"] = json.dumps([{
                    "name": "drill_amfi_code",
                    "expression": {
                        "Column": {
                            "Expression": {"SourceRef": {"Entity": "dim_fund"}},
                            "Property": "amfi_code",
                        }
                    },
                    "type": "Advanced",
                    "howCreated": 4,
                }])

        # Add scatter plot to Fund Performance page
        for section in sections:
            if section.get("displayName") == "Fund Performance":
                scatter_name = uuid.uuid4().hex[:16]
                scatter_cfg = _make_visual_config(
                    "scatterChart",
                    scatter_name,
                    {
                        "X": [{"queryRef": "fact_performance.return_3yr_pct", "active": True}],
                        "Y": [{"queryRef": "fact_performance.std_dev_ann_pct", "active": True}],
                        "Size": [{"queryRef": "fact_performance.aum_crore", "active": True}],
                        "Details": [{"queryRef": "fact_performance.scheme_name", "active": True}],
                    },
                    {
                        "Version": 2,
                        "From": [{"Name": "p", "Entity": "fact_performance", "Type": 0}],
                        "Select": [
                            {"Column": {"Expression": {"SourceRef": {"Source": "p"}}, "Property": "return_3yr_pct"},
                             "Name": "fact_performance.return_3yr_pct"},
                            {"Column": {"Expression": {"SourceRef": {"Source": "p"}}, "Property": "std_dev_ann_pct"},
                             "Name": "fact_performance.std_dev_ann_pct"},
                            {"Column": {"Expression": {"SourceRef": {"Source": "p"}}, "Property": "aum_crore"},
                             "Name": "fact_performance.aum_crore"},
                            {"Column": {"Expression": {"SourceRef": {"Source": "p"}}, "Property": "scheme_name"},
                             "Name": "fact_performance.scheme_name"},
                        ],
                    },
                )
                section["visualContainers"].append({
                    "x": 620, "y": 140, "width": 620, "height": 400,
                    "config": scatter_cfg,
                })
                # Enable drill-through on scorecard table (last tableEx visual)
                for vc in section["visualContainers"]:
                    cfg = json.loads(vc["config"])
                    if cfg.get("singleVisual", {}).get("visualType") == "tableEx":
                        cfg["singleVisual"]["drillFilterOtherVisuals"] = True
                        vc["config"] = json.dumps(cfg)

        # Add logo image to each main page
        if logo_path.exists():
            logo_name = f"bluestock_logo{logo_path.suffix}"
            for section in sections:
                if section.get("displayName") != "NAV Detail":
                    img_name = uuid.uuid4().hex[:16]
                    img_cfg = json.dumps({
                        "name": img_name,
                        "singleVisual": {
                            "visualType": "image",
                            "drillFilterOtherVisuals": True,
                            "objects": {"general": [{"properties": {
                                "imageUrl": {"expr": {"ResourcePackageItem": {
                                    "PackageName": "RegisteredResources",
                                    "PackageType": 1,
                                    "ItemName": logo_name,
                                }}}
                            }}]},
                        },
                    })
                    section["visualContainers"].append({
                        "x": 1100, "y": 0, "width": 160, "height": 50,
                        "config": img_cfg,
                    })

            layout["resourcePackages"].append({
                "name": "RegisteredResources",
                "type": 1,
                "items": [{"name": logo_name, "path": logo_name, "type": 100}],
            })

        new_layout = json.dumps(layout, ensure_ascii=False).encode("utf-16-le")

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "Report/Layout":
                    data = new_layout
                elif item.filename == "Settings":
                    settings = json.loads(data.decode("utf-16-le"))
                    settings.setdefault("ReportSettings", {})
                    settings["ReportSettings"]["useEnhancedTooltips"] = True
                    data = json.dumps(settings).encode("utf-16-le")
                zout.writestr(item, data)

            # Add theme and logo to package
            zout.writestr(
                "Report/StaticResources/SharedResources/BaseThemes/Bluestock.json",
                json.dumps(theme, indent=2).encode("utf-8"),
            )
            if logo_path.exists():
                zout.writestr(
                    f"Report/StaticResources/RegisteredResources/{logo_name}",
                    logo_path.read_bytes(),
                )

    PBIX_PATH.write_bytes(buf.getvalue())
    print(f"Post-processed PBIX with theme, logo, scatter, drill-through: {PBIX_PATH}")


def create_logo(path: Path) -> None:
    """Create a simple Bluestock logo image."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(3.2, 0.8))
    fig.patch.set_facecolor(BLUESTOCK["primary"])
    ax.set_facecolor(BLUESTOCK["primary"])
    ax.text(0.5, 0.5, "BLUESTOCK", ha="center", va="center",
            fontsize=22, fontweight="bold", color="white", transform=ax.transAxes)
    ax.axis("off")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BLUESTOCK["primary"])
    plt.close(fig)


def _style_axis(ax, title: str) -> None:
    """Apply the shared dashboard axis style."""
    ax.set_title(title, fontsize=13, fontweight="bold", color=BLUESTOCK["text"], pad=10)
    ax.tick_params(colors=BLUESTOCK["muted"])
    for spine in ax.spines.values():
        spine.set_color("#CBD5E1")


def export_page_pngs(dfs: dict[str, pd.DataFrame]) -> list[Path]:
    """Export static PNG screenshots of all 4 dashboard pages."""
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    paths = []

    # --- Page 1: Industry Overview ---
    fig = plt.figure(figsize=(16, 9), facecolor=BLUESTOCK["bg"])
    fig.suptitle("Industry Overview", fontsize=18, fontweight="bold", color=BLUESTOCK["primary"], y=0.97)
    kpi = dfs["kpi_snapshot"].iloc[0]
    kpis = [
        ("Total AUM", f"₹{kpi['total_aum_crore']:,.0f} Cr"),
        ("SIP Inflows", f"₹{kpi['total_sip_inflows_crore']:,.0f} Cr"),
        ("Total Folios", f"{kpi['total_folios_crore']:.2f} Cr"),
        ("Total Schemes", f"{int(kpi['total_schemes'])}"),
    ]
    for i, (label, val) in enumerate(kpis):
        ax = fig.add_axes([0.03 + i * 0.24, 0.78, 0.22, 0.14])
        ax.set_facecolor("white")
        ax.text(0.5, 0.65, val, ha="center", fontsize=14, fontweight="bold", color=BLUESTOCK["primary"])
        ax.text(0.5, 0.2, label, ha="center", fontsize=10, color=BLUESTOCK["muted"])
        ax.axis("off")
        for s in ax.spines.values():
            s.set_visible(True)
            s.set_color(BLUESTOCK["light"])

    ax1 = fig.add_axes([0.05, 0.1, 0.55, 0.6])
    trend = dfs["industry_aum_trend"].copy()
    trend["date"] = pd.to_datetime(trend["date"])
    ax1.plot(trend["date"], trend["total_aum_crore"] / 1000, color=BLUESTOCK["primary"], linewidth=2)
    ax1.fill_between(trend["date"], trend["total_aum_crore"] / 1000, alpha=0.15, color=BLUESTOCK["secondary"])
    _style_axis(ax1, "Industry AUM Trend (2022–2025)")
    ax1.set_ylabel("AUM (₹ Lakh Cr)")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.1f}"))

    ax2 = fig.add_axes([0.65, 0.1, 0.32, 0.6])
    latest = dfs["aum_latest"].sort_values("aum_crore", ascending=True)
    ax2.barh(latest["fund_house"], latest["aum_crore"] / 1000, color=BLUESTOCK["palette"][:len(latest)])
    _style_axis(ax2, "AUM by AMC / Fund House")
    ax2.set_xlabel("AUM (₹ Lakh Cr)")

    p1 = DASHBOARD_DIR / "page1_industry_overview.png"
    fig.savefig(p1, dpi=150, bbox_inches="tight", facecolor=BLUESTOCK["bg"])
    plt.close(fig)
    paths.append(p1)

    # --- Page 2: Fund Performance ---
    fig = plt.figure(figsize=(16, 9), facecolor=BLUESTOCK["bg"])
    fig.suptitle("Fund Performance", fontsize=18, fontweight="bold", color=BLUESTOCK["primary"], y=0.97)
    perf = dfs["fact_performance"]
    ax = fig.add_axes([0.05, 0.45, 0.42, 0.45])
    sizes = perf["aum_crore"] / perf["aum_crore"].max() * 400
    ax.scatter(perf["return_3yr_pct"], perf["std_dev_ann_pct"], s=sizes,
               c=BLUESTOCK["secondary"], alpha=0.65, edgecolors="white")
    _style_axis(ax, "Return vs Risk (bubble size = AUM)")
    ax.set_xlabel("Return 3Y (%)")
    ax.set_ylabel("Std Dev Ann (%)")

    ax_t = fig.add_axes([0.52, 0.45, 0.43, 0.45])
    ax_t.axis("off")
    sc = dfs["fund_scorecard"].head(10)[["overall_rank", "scheme_name", "fund_score", "cagr_3yr_pct", "sharpe_ratio"]]
    sc.columns = ["Rank", "Scheme", "Score", "CAGR 3Y%", "Sharpe"]
    tbl = ax_t.table(cellText=sc.values, colLabels=sc.columns, loc="center", cellLoc="left")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.4)
    ax_t.set_title("Fund Scorecard (Top 10)", fontsize=13, fontweight="bold", color=BLUESTOCK["text"])

    ax_l = fig.add_axes([0.05, 0.08, 0.9, 0.3])
    nvb = dfs["nav_vs_benchmark"]
    top_codes = dfs["fund_scorecard"].head(3)["amfi_code"].tolist()
    for i, code in enumerate(top_codes):
        sub = nvb[nvb["amfi_code"] == code].sort_values("date")
        if len(sub):
            ax_l.plot(pd.to_datetime(sub["date"]), sub["indexed_value"],
                      label=sub["scheme_name"].iloc[0][:25], color=BLUESTOCK["palette"][i], linewidth=1.5)
    for name, code in [("Nifty 50", 0), ("Nifty 100", -1)]:
        sub = nvb[nvb["amfi_code"] == code].sort_values("date")
        ax_l.plot(pd.to_datetime(sub["date"]), sub["indexed_value"], label=name,
                  linestyle="--", color=BLUESTOCK["muted"], linewidth=1.2)
    _style_axis(ax_l, "NAV vs Benchmark (indexed, top 3 funds)")
    ax_l.legend(fontsize=7, ncol=3, loc="upper left")
    ax_l.set_ylabel("Indexed (100)")

    p2 = DASHBOARD_DIR / "page2_fund_performance.png"
    fig.savefig(p2, dpi=150, bbox_inches="tight", facecolor=BLUESTOCK["bg"])
    plt.close(fig)
    paths.append(p2)

    # --- Page 3: Investor Analytics ---
    fig = plt.figure(figsize=(16, 9), facecolor=BLUESTOCK["bg"])
    fig.suptitle("Investor Analytics", fontsize=18, fontweight="bold", color=BLUESTOCK["primary"], y=0.97)
    txn = dfs["fact_transactions"]

    ax1 = fig.add_axes([0.05, 0.52, 0.4, 0.4])
    by_state = txn.groupby("state")["amount_inr"].sum().sort_values(ascending=False).head(12)
    ax1.bar(range(len(by_state)), by_state.values / 1e7, color=BLUESTOCK["primary"])
    ax1.set_xticks(range(len(by_state)))
    ax1.set_xticklabels(by_state.index, rotation=45, ha="right", fontsize=8)
    _style_axis(ax1, "Transaction Amount by State")
    ax1.set_ylabel("Amount (₹ Cr)")

    ax2 = fig.add_axes([0.52, 0.52, 0.2, 0.4])
    by_type = txn.groupby("transaction_type")["amount_inr"].sum()
    ax2.pie(by_type.values, labels=by_type.index, autopct="%1.0f%%",
            colors=BLUESTOCK["palette"][:3], textprops={"fontsize": 8})
    ax2.set_title("SIP vs Lumpsum vs Redemption", fontsize=11, fontweight="bold")

    ax3 = fig.add_axes([0.76, 0.52, 0.2, 0.4])
    age_sip = txn[txn["transaction_type"] == "SIP"].groupby("age_group")["amount_inr"].mean() / 1000
    ax3.bar(age_sip.index, age_sip.values, color=BLUESTOCK["accent"])
    _style_axis(ax3, "Age Group vs Avg SIP (₹K)")
    ax3.tick_params(axis="x", labelsize=7)

    ax4 = fig.add_axes([0.05, 0.08, 0.9, 0.35])
    txn["month"] = pd.to_datetime(txn["transaction_date"]).dt.to_period("M").astype(str)
    monthly = txn.groupby("month").size()
    ax4.plot(monthly.index, monthly.values, color=BLUESTOCK["primary"], marker="o", markersize=3)
    _style_axis(ax4, "Monthly Transaction Volume")
    ax4.set_ylabel("Transactions")
    ax4.tick_params(axis="x", rotation=45, labelsize=7)

    p3 = DASHBOARD_DIR / "page3_investor_analytics.png"
    fig.savefig(p3, dpi=150, bbox_inches="tight", facecolor=BLUESTOCK["bg"])
    plt.close(fig)
    paths.append(p3)

    # --- Page 4: SIP & Market Trends ---
    fig = plt.figure(figsize=(16, 9), facecolor=BLUESTOCK["bg"])
    fig.suptitle("SIP & Market Trends", fontsize=18, fontweight="bold", color=BLUESTOCK["primary"], y=0.97)
    sn = dfs["sip_nifty"].copy()
    sn["month_dt"] = pd.to_datetime(sn["month"])

    ax1 = fig.add_axes([0.05, 0.48, 0.55, 0.42])
    ax1b = ax1.twinx()
    ax1.bar(sn["month_dt"], sn["sip_inflow_crore"] / 1000, width=20, color=BLUESTOCK["light"], label="SIP Inflow")
    ax1b.plot(sn["month_dt"], sn["nifty50_close"], color=BLUESTOCK["primary"], linewidth=2, label="Nifty 50")
    _style_axis(ax1, "SIP Inflow (Bar) vs Nifty 50 (Line) 2022–2025")
    ax1.set_ylabel("SIP (₹K Cr)")
    ax1b.set_ylabel("Nifty 50")
    ax1.tick_params(axis="x", rotation=45, labelsize=7)

    ax2 = fig.add_axes([0.65, 0.48, 0.32, 0.42])
    heat = dfs["category_inflows"].pivot_table(
        index="category", columns="month", values="net_inflow_crore", aggfunc="sum"
    ).iloc[:, -6:]
    im = ax2.imshow(heat.values, aspect="auto", cmap="Blues")
    ax2.set_yticks(range(len(heat.index)))
    ax2.set_yticklabels(heat.index, fontsize=6)
    ax2.set_xticks(range(len(heat.columns)))
    ax2.set_xticklabels(heat.columns, rotation=45, ha="right", fontsize=6)
    _style_axis(ax2, "Category Inflow Heatmap (last 6 months)")
    fig.colorbar(im, ax=ax2, fraction=0.03)

    ax3 = fig.add_axes([0.05, 0.08, 0.9, 0.32])
    top5 = dfs["category_fy25"].head(5)
    ax3.bar(top5["category"], top5["net_inflow_crore"] / 1000, color=BLUESTOCK["palette"][:5])
    _style_axis(ax3, "Top 5 Categories by Net Inflow FY25")
    ax3.set_ylabel("Net Inflow (₹K Cr)")
    ax3.tick_params(axis="x", rotation=30, labelsize=8)

    p4 = DASHBOARD_DIR / "page4_sip_market_trends.png"
    fig.savefig(p4, dpi=150, bbox_inches="tight", facecolor=BLUESTOCK["bg"])
    plt.close(fig)
    paths.append(p4)

    return paths


def export_pdf(png_paths: list[Path]) -> None:
    """Combine dashboard page PNGs into a single PDF."""
    with PdfPages(PDF_PATH) as pdf:
        for png in png_paths:
            img = plt.imread(png)
            fig, ax = plt.subplots(figsize=(16, 9))
            ax.imshow(img)
            ax.axis("off")
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
    print(f"Created PDF: {PDF_PATH}")


def main() -> None:
    print("=" * 60)
    print(" DAY 5: Building Bluestock MF Dashboard")
    print("=" * 60)

    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    create_logo(LOGO_PATH)

    print("\nLoading datasets...")
    dfs = load_datasets()
    print(f"  Loaded {len(dfs)} tables")

    print("\nBuilding Power BI dashboard...")
    build_pbix(dfs)
    post_process_pbix(LOGO_PATH)

    print("\nExporting dashboard PNG screenshots...")
    png_paths = export_page_pngs(dfs)
    for p in png_paths:
        print(f"  {p}")

    print("\nExporting Dashboard.pdf...")
    export_pdf(png_paths)

    print("\n" + "=" * 60)
    print(" DAY 5 DELIVERABLES COMPLETE")
    print("=" * 60)
    print(f"  PBIX:  {PBIX_PATH}")
    print(f"  PDF:   {PDF_PATH}")
    print(f"  PNGs:  {DASHBOARD_DIR}/")


if __name__ == "__main__":
    main()
