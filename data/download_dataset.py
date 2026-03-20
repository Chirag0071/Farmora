"""
data/download_dataset.py
========================
Pulls as much historical data as possible from the AGMARKNET API using
pagination, then saves it as data/agmarknet_historical.csv.

Run once:  python data/download_dataset.py

This gives ~2 years of data — enough for decent seasonality.
For full 10-year history, download from Kaggle (see README_DATASET.md).
"""

import requests
import pandas as pd
import os
import time
from datetime import datetime

DATA_API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
DATA_URL     = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
OUT_PATH     = os.path.join(os.path.dirname(__file__), "agmarknet_historical.csv")
MAX_PAGES    = 20          # 20 × 5000 = 100,000 records
PAGE_SIZE    = 5000
SLEEP_SEC    = 0.8         # be polite to the API


def fetch_page(offset: int) -> list:
    params = {
        "api-key": DATA_API_KEY,
        "format":  "json",
        "limit":   PAGE_SIZE,
        "offset":  offset,
    }
    try:
        r = requests.get(DATA_URL, params=params, timeout=30)
        r.raise_for_status()
        return r.json().get("records", [])
    except Exception as e:
        print(f"  ⚠️  Page offset={offset} failed: {e}")
        return []


def main():
    print("=" * 60)
    print("Farmora — AGMARKNET Historical Data Downloader")
    print("=" * 60)

    if os.path.exists(OUT_PATH):
        existing = pd.read_csv(OUT_PATH)
        print(f"ℹ️  Existing file found: {len(existing):,} records")
        ans = input("Re-download and overwrite? [y/N]: ").strip().lower()
        if ans != "y":
            print("Skipping download.")
            return

    all_records = []
    print(f"\nFetching up to {MAX_PAGES * PAGE_SIZE:,} records ({MAX_PAGES} pages × {PAGE_SIZE})…\n")

    for page in range(MAX_PAGES):
        offset = page * PAGE_SIZE
        print(f"  Page {page+1:2d}/{MAX_PAGES}  offset={offset:,}", end="  ")
        records = fetch_page(offset)
        if not records:
            print("→ empty, stopping.")
            break
        all_records.extend(records)
        print(f"→ +{len(records):,}  total={len(all_records):,}")
        time.sleep(SLEEP_SEC)

    if not all_records:
        print("\n❌ No records fetched. Check your API key / internet connection.")
        return

    df = pd.DataFrame(all_records)

    # ── normalise columns ──────────────────────────────────────────────────
    rename_map = {}
    for col in df.columns:
        cl = col.lower()
        if "state"     in cl and "state"     not in rename_map.values(): rename_map[col] = "state"
        if "district"  in cl and "district"  not in rename_map.values(): rename_map[col] = "district"
        if "market"    in cl and "market"    not in rename_map.values(): rename_map[col] = "market"
        if "commodity" in cl and "commodity" not in rename_map.values(): rename_map[col] = "commodity"
        if "arrival"   in cl and "arrival_date" not in rename_map.values(): rename_map[col] = "arrival_date"
        if "min"       in cl and "price" in cl:  rename_map[col] = "min_price"
        if "max"       in cl and "price" in cl:  rename_map[col] = "max_price"
        if "modal"     in cl and "price" in cl:  rename_map[col] = "modal_price"
    df = df.rename(columns=rename_map)

    # ── cast types ─────────────────────────────────────────────────────────
    if "arrival_date" in df.columns:
        df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")
    for col in ["min_price", "max_price", "modal_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["arrival_date", "modal_price"]).sort_values("arrival_date")

    # ── save ───────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print(f"\n✅  Saved {len(df):,} records → {OUT_PATH}")
    print(f"📅  Date range: {df['arrival_date'].min().date()} → {df['arrival_date'].max().date()}")
    print(f"🌾  Unique crops:  {df['commodity'].nunique() if 'commodity' in df.columns else 'N/A'}")
    print(f"🗺️   Unique states: {df['state'].nunique() if 'state' in df.columns else 'N/A'}")


if __name__ == "__main__":
    main()
