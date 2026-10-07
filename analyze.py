"""Reproduce a portfolio analysis of the UCI Online Retail dataset.

Usage: python analyze.py [path/to/Online Retail.xlsx]
The original download is cached in .data/ and is not committed.
"""
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO
import hashlib
import json
import sqlite3
import sys

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
SOURCE = "https://archive.ics.uci.edu/static/public/352/online%2Bretail.zip"


def load_data(path=None):
    file = Path(path) if path else ROOT / ".data" / "Online Retail.xlsx"
    if not file.exists():
        file.parent.mkdir(exist_ok=True, parents=True)
        with urlopen(SOURCE, timeout=120) as response:
            archive = ZipFile(BytesIO(response.read()))
        file.write_bytes(archive.read("Online Retail.xlsx"))
    raw = pd.read_excel(file, dtype={"InvoiceNo": str, "StockCode": str})
    return raw, hashlib.sha256(file.read_bytes()).hexdigest()


def prepare_data(raw):
    cancelled = raw["InvoiceNo"].str.upper().str.startswith("C", na=False)
    valid = (~cancelled) & (raw["Quantity"] > 0) & (raw["UnitPrice"] > 0)
    sales = raw.loc[valid].copy()
    sales["sales_value"] = sales["Quantity"] * sales["UnitPrice"]
    sales["invoice_month"] = sales["InvoiceDate"].dt.strftime("%Y-%m")
    # Duplicate-looking rows remain: invoice lines have no unique line identifier.
    sales["CustomerID"] = sales["CustomerID"].astype("Int64").astype("string")
    quality = {
        "source_rows": int(len(raw)),
        "positive_sales_rows": int(len(sales)),
        "excluded_rows": int((~valid).sum()),
        "cancellation_rows": int(cancelled.sum()),
        "nonpositive_quantity_rows": int((raw.Quantity <= 0).sum()),
        "nonpositive_price_rows": int((raw.UnitPrice <= 0).sum()),
        "missing_customer_rows": int(raw.CustomerID.isna().sum()),
        "exact_duplicate_rows_flagged_not_removed": int(raw.duplicated().sum()),
    }
    return sales, quality


def compute_tables(sales):
    db = sqlite3.connect(":memory:")
    sales.to_sql("sales", db, index=False)
    query_text = (ROOT / "queries.sql").read_text(encoding="utf-8")
    tables = {}
    for block in query_text.split("-- QUERY: ")[1:]:
        name, statement = block.split("\n", 1)
        tables[name.strip()] = pd.read_sql_query(statement, db)
    db.close()
    return tables


def create_charts(tables):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "figure.facecolor": "#121212", "axes.facecolor": "#121212",
                         "text.color": "#eeeeee", "axes.labelcolor": "#c9c9c9",
                         "xtick.color": "#c9c9c9", "ytick.color": "#c9c9c9",
                         "axes.edgecolor": "#555555", "savefig.facecolor": "#121212"})
    monthly = tables["monthly_sales"]
    fig, ax = plt.subplots(figsize=(11, 5.5), layout="constrained")
    bars = ax.bar(monthly.month, monthly.sales_gbp / 1e6, color="#ff6b00")
    bars[-1].set_color("#888888")
    fig.suptitle("Recorded positive sales by month", fontsize=18)
    ax.set(title="Positive sale lines only; returns not subtracted. December 2011 covers 1–9 Dec.", ylabel="Sale-line value (GBP millions)")
    ax.title.set_fontsize(10)
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color="#333333", alpha=.7)
    ax.set_axisbelow(True)
    fig.savefig(ROOT / "monthly_sales.png", dpi=140)
    plt.close(fig)
    countries = tables["country_sales"].head(8).iloc[::-1]
    fig, ax = plt.subplots(figsize=(11, 5), layout="constrained")
    ax.barh(countries.country, countries.sales_gbp / 1e6, color="#ff6b00")
    ax.set(title="Top countries by recorded positive sales", xlabel="Sale-line value (GBP millions)")
    ax.set_xlim(left=0)
    ax.grid(axis="x", color="#333333", alpha=.7)
    ax.set_axisbelow(True)
    fig.savefig(ROOT / "country_sales.png", dpi=140)
    plt.close(fig)


def write_outputs(tables, quality, checksum, raw, sales):
    for name, table in tables.items():
        table.to_csv(ROOT / f"{name}.csv", index=False, float_format="%.2f")
    kpi = tables["kpis"].iloc[0].to_dict()
    months = tables["monthly_sales"]
    complete = months[months.month != "2011-12"]
    peak = complete.loc[complete.sales_gbp.idxmax()].to_dict()
    uk = tables["country_sales"].query("country == 'United Kingdom'").iloc[0].sales_gbp
    repeat = tables["customer_summary"].iloc[0].to_dict()
    report = {
        "source": "Chen, D. (2015). Online Retail. UCI. https://doi.org/10.24432/C5BW33",
        "source_download": SOURCE,
        "source_sha256": checksum,
        "dataset_start": raw.InvoiceDate.min().isoformat(),
        "dataset_end": raw.InvoiceDate.max().isoformat(),
        "quality": quality,
        "kpis": kpi,
        "peak_complete_month": peak,
        "uk_positive_sales_share_pct": float(uk / kpi["sales_gbp"] * 100),
        "identified_customer_summary": repeat,
        "definitions": {
            "sales_gbp": "Sum(Quantity × UnitPrice) on noncancelled lines with positive quantity and price. Not net revenue or profit.",
            "orders": "Distinct InvoiceNo in positive sales population, including unidentified customers.",
            "average_order_value": "Positive sales value / distinct orders.",
            "repeat_customer_pct": "Identified customers with more than one distinct purchase invoice / all identified purchasing customers.",
        },
        "caveats": [
            "Historical portfolio study, not current business performance.",
            "December 2011 is partial; do not compare it directly with complete months.",
            "Negative quantities, cancellations and nonpositive prices are excluded; returns are not subtracted.",
            "Anonymous sales count in totals; customer analysis excludes missing CustomerID.",
            "Exact duplicate-looking lines are flagged and retained because line identifiers are unavailable.",
            "Shipping, charges and adjustment StockCodes are retained when positive; totals are not merchandise-only.",
            "No observed trend is treated as a causal explanation or achieved business improvement.",
        ],
    }
    (ROOT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    findings = f"""# Findings

Scope: {report['dataset_start'][:10]} to {report['dataset_end'][:10]}.

- Recorded positive sales: **£{kpi['sales_gbp']:,.2f}**, across **{int(kpi['orders']):,} purchase invoices**.
- Average positive sale-line value per purchase invoice: **£{kpi['average_order_value']:,.2f}**.
- United Kingdom accounts for **{report['uk_positive_sales_share_pct']:.1f}%** of the positive sales value.
- The highest complete month is **{peak['month']}**, with **£{peak['sales_gbp']:,.2f}**.
- **{repeat['repeat_customer_pct']:.1f}%** of identified purchasing customers have more than one purchase invoice.

## Interpretation

The UK dominates the recorded sales mix. November 2011 is the largest complete month; this is a descriptive observation, not proof of a seasonal cause. Repeat purchasing among identified customers is a useful prompt for deeper retention analysis, but anonymous customers and returns limit conclusions.

## Data preparation

Read {quality['source_rows']:,} invoice lines; retained {quality['positive_sales_rows']:,} positive sale lines and excluded {quality['excluded_rows']:,} lines. Flagged {quality['exact_duplicate_rows_flagged_not_removed']:,} exact duplicate-looking rows without deleting them. Missing customer IDs occur in {quality['missing_customer_rows']:,} source rows. Quality categories overlap and must not be added together.

## Limits

""" + "\n".join(f"- {item}" for item in report["caveats"]) + "\n"
    (ROOT / "FINDINGS.md").write_text(findings, encoding="utf-8")
    return report


def main(path=None):
    raw, checksum = load_data(path)
    sales, quality = prepare_data(raw)
    tables = compute_tables(sales)
    create_charts(tables)
    report = write_outputs(tables, quality, checksum, raw, sales)
    print(json.dumps({"quality": quality, "kpis": report["kpis"]}, indent=2))
    return raw, sales, tables, report


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
