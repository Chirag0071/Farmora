"""
backend/data_loader.py
======================
Hybrid data layer:
  1. Loads the historical CSV (2010–2023) once at startup into memory
  2. Fetches live data from AGMARKNET API (last 90 days)
  3. Merges both, deduplicates, sorts chronologically
  4. Returns a single clean DataFrame to the ML model

This gives the ML model 10+ years of seasonal patterns
PLUS the most recent market prices.
"""

import os
import logging
import requests
import pandas as pd
import numpy as np
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── paths ──────────────────────────────────────────────────────────────────────
_HERE     = os.path.dirname(os.path.abspath(__file__))
CSV_PATH  = os.path.join(_HERE, "..", "data", "agmarknet_historical.csv")
CSV_PATH  = os.path.normpath(CSV_PATH)

DATA_API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
DATA_URL     = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# ── column name normaliser ─────────────────────────────────────────────────────
_COL_MAP = {
    # state
    "state": "state", "State": "state",
    # district
    "district": "district", "District": "district",
    # market
    "market": "market", "Market": "market", "market_name": "market",
    # commodity / crop
    "commodity": "commodity", "Commodity": "commodity",
    "crop": "commodity", "Crop": "commodity",
    # dates
    "arrival_date": "arrival_date", "Arrival_Date": "arrival_date",
    "date": "arrival_date", "Date": "arrival_date",
    # prices
    "min_price": "min_price", "Min_Price": "min_price", "minimum_price": "min_price",
    "max_price": "max_price", "Max_Price": "max_price", "maximum_price": "max_price",
    "modal_price": "modal_price", "Modal_Price": "modal_price",
    "modal price": "modal_price",
}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to the standard schema."""
    rename = {}
    for col in df.columns:
        stripped = col.strip()
        if stripped in _COL_MAP:
            rename[col] = _COL_MAP[stripped]
        else:
            # fuzzy match
            cl = stripped.lower()
            if "state"     in cl: rename[col] = "state"
            elif "district" in cl: rename[col] = "district"
            elif "market"   in cl: rename[col] = "market"
            elif "commodity" in cl or "crop" in cl: rename[col] = "commodity"
            elif "arrival"  in cl: rename[col] = "arrival_date"
            elif "min"      in cl and "price" in cl: rename[col] = "min_price"
            elif "max"      in cl and "price" in cl: rename[col] = "max_price"
            elif "modal"    in cl and "price" in cl: rename[col] = "modal_price"
    return df.rename(columns=rename)


def _cast_types(df: pd.DataFrame) -> pd.DataFrame:
    if "arrival_date" in df.columns:
        df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")
    for col in ["min_price", "max_price", "modal_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["state", "district", "market", "commodity"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()
    return df


# ── CSV loader (cached — loaded once at startup) ───────────────────────────────

_CSV_CACHE: pd.DataFrame | None = None
_CSV_LOADED = False


def load_csv() -> pd.DataFrame:
    """
    Load the historical CSV once and cache in memory.
    Returns empty DataFrame if file not found.
    """
    global _CSV_CACHE, _CSV_LOADED
    if _CSV_LOADED:
        return _CSV_CACHE if _CSV_CACHE is not None else pd.DataFrame()

    _CSV_LOADED = True

    if not os.path.exists(CSV_PATH):
        logger.warning(f"Historical CSV not found at {CSV_PATH}. "
                       "Falling back to live API only. "
                       "See data/README_DATASET.md to download the dataset.")
        _CSV_CACHE = pd.DataFrame()
        return _CSV_CACHE

    try:
        logger.info(f"Loading historical CSV: {CSV_PATH} …")
        df = pd.read_csv(CSV_PATH, low_memory=False)
        df = _normalise_columns(df)
        df = _cast_types(df)
        df = df.dropna(subset=["arrival_date", "modal_price"])
        df = df[df["modal_price"] > 0]
        df = df.sort_values("arrival_date").reset_index(drop=True)
        _CSV_CACHE = df
        logger.info(f"CSV loaded: {len(df):,} records  "
                    f"({df['arrival_date'].min().date()} → {df['arrival_date'].max().date()})")
        return _CSV_CACHE
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        _CSV_CACHE = pd.DataFrame()
        return _CSV_CACHE


# ── live API fetcher ───────────────────────────────────────────────────────────

def fetch_live(state: str = "", district: str = "", crop: str = "",
               limit: int = 5000) -> pd.DataFrame:
    """
    Pull the most recent records from AGMARKNET live API.
    Returns normalised DataFrame or empty DataFrame on failure.
    """
    params = {"api-key": DATA_API_KEY, "format": "json", "limit": limit}
    if state.strip():    params["filters[state]"]     = state.strip()
    if district.strip(): params["filters[district]"]  = district.strip()
    if crop.strip():     params["filters[commodity]"] = crop.strip()

    try:
        r = requests.get(DATA_URL, params=params, timeout=30)
        r.raise_for_status()
        records = r.json().get("records", [])
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df = _normalise_columns(df)
        df = _cast_types(df)
        df = df.dropna(subset=["arrival_date", "modal_price"])
        df = df[df["modal_price"] > 0]
        return df.sort_values("arrival_date").reset_index(drop=True)
    except Exception as e:
        logger.warning(f"Live API fetch failed: {e}")
        return pd.DataFrame()


# ── CSV filter ─────────────────────────────────────────────────────────────────

def filter_csv(state: str = "", district: str = "", crop: str = "") -> pd.DataFrame:
    """
    Filter the in-memory CSV cache for the given state/district/crop.
    Matching is case-insensitive.
    """
    df = load_csv()
    if df.empty:
        return df

    mask = pd.Series([True] * len(df), index=df.index)

    if state.strip() and "state" in df.columns:
        mask &= df["state"].str.lower() == state.strip().lower()

    if district.strip() and "district" in df.columns:
        mask &= df["district"].str.lower() == district.strip().lower()

    if crop.strip() and "commodity" in df.columns:
        # try exact first, then contains
        exact = df["commodity"].str.lower() == crop.strip().lower()
        if exact.sum() > 0:
            mask &= exact
        else:
            mask &= df["commodity"].str.lower().str.contains(
                crop.strip().lower(), regex=False, na=False
            )

    return df[mask].reset_index(drop=True)


# ── main hybrid merge ──────────────────────────────────────────────────────────

def get_hybrid_data(state: str, district: str, crop: str) -> pd.DataFrame:
    """
    Core hybrid fetch:
      1. Filter historical CSV for state+district+crop
      2. Fetch live API for same combination (last few months)
      3. Merge, deduplicate on (arrival_date, market, modal_price), sort
      4. Return unified DataFrame with all historical + recent prices

    Fallback chain if district returns too few records:
      - Try state + crop (drop district)
      - Try crop only (national level)
    """
    MIN_RECORDS = 30  # minimum to attempt a meaningful forecast

    # ── Step 1: CSV historical ─────────────────────────────────────────────
    csv_df = filter_csv(state=state, district=district, crop=crop)

    # if CSV district is empty, try state-level from CSV
    if len(csv_df) < MIN_RECORDS and district:
        csv_df_state = filter_csv(state=state, district="", crop=crop)
        if len(csv_df_state) > len(csv_df):
            csv_df = csv_df_state
            logger.info(f"CSV: district '{district}' too sparse, using state-level data")

    # ── Step 2: Live API ───────────────────────────────────────────────────
    live_df = fetch_live(state=state, district=district, crop=crop)

    # live API fallbacks
    if live_df.empty and district:
        live_df = fetch_live(state=state, district="", crop=crop)
    if live_df.empty:
        live_df = fetch_live(crop=crop, limit=3000)

    # ── Step 3: Merge ──────────────────────────────────────────────────────
    frames = [f for f in [csv_df, live_df] if not f.empty]

    if not frames:
        logger.warning(f"No data found for crop='{crop}' state='{state}'")
        return pd.DataFrame()

    merged = pd.concat(frames, ignore_index=True)

    # ensure consistent types after concat
    merged = _cast_types(merged)
    merged = merged.dropna(subset=["arrival_date", "modal_price"])
    merged = merged[merged["modal_price"] > 0]

    # deduplicate: keep most recent record per (arrival_date, market)
    dedup_cols = [c for c in ["arrival_date", "market", "district"] if c in merged.columns]
    if dedup_cols:
        merged = merged.sort_values("arrival_date").drop_duplicates(
            subset=dedup_cols, keep="last"
        )
    else:
        merged = merged.drop_duplicates()

    merged = merged.sort_values("arrival_date").reset_index(drop=True)

    # ── Step 4: if still too sparse, try national CSV ─────────────────────
    if len(merged) < MIN_RECORDS:
        national_csv = filter_csv(crop=crop)
        if len(national_csv) > len(merged):
            merged = pd.concat([national_csv, live_df], ignore_index=True)
            merged = _cast_types(merged)
            merged = merged.dropna(subset=["arrival_date","modal_price"])
            merged = merged.sort_values("arrival_date").reset_index(drop=True)
            logger.info(f"Using national-level CSV data: {len(merged):,} records")

    logger.info(
        f"Hybrid data for crop='{crop}' state='{state}': "
        f"{len(merged):,} records  "
        f"CSV={len(csv_df):,}  Live={len(live_df):,}  "
        f"range={merged['arrival_date'].min().date() if not merged.empty else 'N/A'}"
        f" → {merged['arrival_date'].max().date() if not merged.empty else 'N/A'}"
    )
    return merged


# ── metadata helpers (for dropdowns) ──────────────────────────────────────────

def get_all_districts(state: str) -> list[str]:
    """All districts for this state — from CSV + live API, merged and sorted."""
    csv_df = load_csv()
    districts = set()

    if not csv_df.empty and "state" in csv_df.columns and "district" in csv_df.columns:
        mask = csv_df["state"].str.lower() == state.lower()
        districts.update(csv_df.loc[mask, "district"].dropna().unique())

    # also pull from live API
    live_df = fetch_live(state=state, limit=5000)
    if not live_df.empty and "district" in live_df.columns:
        districts.update(live_df["district"].dropna().unique())

    return sorted(d.strip().title() for d in districts if d.strip())


def get_all_crops(state: str, district: str = "") -> list[str]:
    """All crops for this state/district — from CSV + live API, sorted by frequency."""
    from collections import Counter
    csv_df = load_csv()
    counts: Counter = Counter()

    if not csv_df.empty and "commodity" in csv_df.columns:
        mask = pd.Series([True] * len(csv_df))
        if state and "state" in csv_df.columns:
            mask &= csv_df["state"].str.lower() == state.lower()
        if district and "district" in csv_df.columns:
            mask &= csv_df["district"].str.lower() == district.lower()
        counts.update(csv_df.loc[mask, "commodity"].dropna().str.title().tolist())

    live_df = fetch_live(state=state, district=district, limit=5000)
    if not live_df.empty and "commodity" in live_df.columns:
        counts.update(live_df["commodity"].dropna().str.title().tolist())

    return [c for c, _ in counts.most_common(50)] or [
        "Wheat","Rice","Potato","Tomato","Onion","Capsicum",
        "Brinjal","Cauliflower","Carrot","Garlic","Ginger",
    ]
