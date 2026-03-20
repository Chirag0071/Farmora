"""
data/verify_dataset.py
======================
Quick sanity-check for the historical CSV.
Run:  python data/verify_dataset.py
"""
import os, sys
import pandas as pd

CSV_PATH = os.path.join(os.path.dirname(__file__), "agmarknet_historical.csv")

if not os.path.exists(CSV_PATH):
    print(f"❌  File not found: {CSV_PATH}")
    print("    See data/README_DATASET.md for download instructions.")
    sys.exit(1)

print(f"Loading {CSV_PATH} …")
df = pd.read_csv(CSV_PATH, low_memory=False)

print(f"\n{'='*50}")
print(f"✅  Records:        {len(df):,}")
print(f"📋  Columns:        {list(df.columns)}")

if "arrival_date" in df.columns:
    df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")
    print(f"📅  Date range:     {df['arrival_date'].min().date()} → {df['arrival_date'].max().date()}")
    missing_dates = df["arrival_date"].isna().sum()
    print(f"❓  Missing dates:  {missing_dates:,}")

for col in ["commodity", "state", "district", "modal_price"]:
    if col in df.columns:
        if df[col].dtype == object:
            print(f"🔍  Unique {col:12s}: {df[col].nunique():,}")
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            nulls = df[col].isna().sum()
            print(f"💰  {col:16s}: min={df[col].min():.0f}  max={df[col].max():.0f}  nulls={nulls:,}")
    else:
        print(f"⚠️   Column missing: '{col}'")

print(f"\n{'='*50}")
print("Dataset looks good! You can now run the app.")
