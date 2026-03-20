"""
backend/ml_model.py
===================
ML model trained on multi-year historical data.

Key additions over the old model:
  • year_over_year_change  — % price change vs same month last year
  • price_vs_5yr_avg       — deviation from 5-year monthly average
  • trend_90d              — 90-day linear trend slope
  • GradientBoosting with more estimators for better seasonal learning
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
import joblib
import os

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)


def _sanitize(s) -> str:
    if s is None: return "na"
    return "".join(c if c.isalnum() else "_" for c in str(s)).lower()


def model_path(state: str, district: str, crop: str) -> str:
    return os.path.join(MODEL_DIR, f"gb_{_sanitize(state)}_{_sanitize(district)}_{_sanitize(crop)}.joblib")


def load_model_by_keys(state: str, district: str, crop: str):
    p = model_path(state, district, crop)
    return joblib.load(p) if os.path.exists(p) else None


# ── feature engineering ────────────────────────────────────────────────────────

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a rich feature matrix from multi-year price data.
    The more years of data, the better the seasonal and YOY features work.
    """
    df = df.copy()

    # ── parse ──────────────────────────────────────────────────────────────
    if "arrival_date" not in df.columns:
        return pd.DataFrame()
    df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")

    # normalise modal_price column name
    if "modal_price" not in df.columns:
        for col in df.columns:
            if "modal" in col.lower() and "price" in col.lower():
                df["modal_price"] = df[col]; break
    if "modal_price" not in df.columns:
        return pd.DataFrame()

    df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")

    # ── aggregate: one row per date (mean across markets) ──────────────────
    # This prevents duplicate-date issues when multiple markets report same day
    df = (df.dropna(subset=["arrival_date","modal_price"])
            .groupby("arrival_date", as_index=False)["modal_price"].mean()
            .sort_values("arrival_date")
            .reset_index(drop=True))

    if df.empty or len(df) < 10:
        return df

    # ── calendar ───────────────────────────────────────────────────────────
    df["day"]        = df["arrival_date"].dt.day
    df["month"]      = df["arrival_date"].dt.month
    df["year"]       = df["arrival_date"].dt.year
    df["dayofyear"]  = df["arrival_date"].dt.dayofyear
    df["weekofyear"] = df["arrival_date"].apply(lambda d: d.timetuple().tm_yday // 7 + 1)
    df["quarter"]    = df["arrival_date"].dt.quarter

    # ── lag features ───────────────────────────────────────────────────────
    df["lag1"]   = df["modal_price"].shift(1)
    df["lag7"]   = df["modal_price"].shift(7)
    df["lag14"]  = df["modal_price"].shift(14)
    df["lag30"]  = df["modal_price"].shift(30)
    df["lag90"]  = df["modal_price"].shift(90)
    df["lag365"] = df["modal_price"].shift(365)   # same day last year

    # ── rolling statistics ─────────────────────────────────────────────────
    df["roll7_mean"]  = df["modal_price"].rolling(7,   min_periods=1).mean()
    df["roll14_mean"] = df["modal_price"].rolling(14,  min_periods=1).mean()
    df["roll30_mean"] = df["modal_price"].rolling(30,  min_periods=1).mean()
    df["roll90_mean"] = df["modal_price"].rolling(90,  min_periods=7).mean()
    df["roll7_std"]   = df["modal_price"].rolling(7,   min_periods=2).std().fillna(0)
    df["roll30_std"]  = df["modal_price"].rolling(30,  min_periods=2).std().fillna(0)

    # ── seasonal features (multi-year average) ─────────────────────────────
    monthly_avg  = df.groupby("month")["modal_price"].mean().to_dict()
    seasonal_avg = df.groupby("dayofyear")["modal_price"].mean().to_dict()
    df["monthly_mean"]  = df["month"].map(monthly_avg)
    df["seasonal_mean"] = df["dayofyear"].map(seasonal_avg)

    # ── year-over-year features (only meaningful with 2+ years of data) ────
    n_years = df["year"].nunique()

    if n_years >= 2:
        # % change vs same month last year
        df["yoy_month_change"] = df.apply(
            lambda r: _yoy_change(df, r["year"]-1, r["month"], r["modal_price"]),
            axis=1
        )

        # how current price compares to the 5-year monthly average
        multi_year_monthly = (
            df.groupby(["year","month"])["modal_price"].mean()
              .reset_index()
              .groupby("month")["modal_price"].mean()
              .to_dict()
        )
        df["price_vs_5yr_avg"] = df.apply(
            lambda r: (r["modal_price"] / multi_year_monthly.get(r["month"], r["modal_price"])) - 1.0,
            axis=1
        )
    else:
        df["yoy_month_change"] = 0.0
        df["price_vs_5yr_avg"] = 0.0

    # ── 90-day trend slope (price momentum) ───────────────────────────────
    df["trend_90d"] = _rolling_slope(df["modal_price"], window=90)

    return df.dropna().reset_index(drop=True)


def _yoy_change(df: pd.DataFrame, prev_year: int, month: int, current_price: float) -> float:
    """% change in price vs same month of previous year."""
    prev = df[(df["year"] == prev_year) & (df["month"] == month)]["modal_price"]
    if prev.empty:
        return 0.0
    prev_avg = prev.mean()
    return (current_price - prev_avg) / prev_avg if prev_avg > 0 else 0.0


def _rolling_slope(series: pd.Series, window: int = 90) -> pd.Series:
    """Compute rolling linear regression slope (price trend)."""
    slopes = []
    arr = series.values
    for i in range(len(arr)):
        if i < window - 1:
            slopes.append(np.nan)
        else:
            y = arr[i-window+1:i+1]
            if np.isnan(y).any():
                slopes.append(np.nan)
            else:
                x = np.arange(window)
                slope = np.polyfit(x, y, 1)[0]
                slopes.append(slope)
    return pd.Series(slopes, index=series.index)


FEATURE_COLS = [
    # calendar
    "day", "month", "year", "dayofyear", "weekofyear", "quarter",
    # lags
    "lag1", "lag7", "lag14", "lag30", "lag90", "lag365",
    # rolling
    "roll7_mean", "roll14_mean", "roll30_mean", "roll90_mean",
    "roll7_std", "roll30_std",
    # seasonal
    "seasonal_mean", "monthly_mean",
    # year-over-year
    "yoy_month_change", "price_vs_5yr_avg",
    # trend
    "trend_90d",
]


# ── training ───────────────────────────────────────────────────────────────────

def train_model(df, model_name=None, state=None, district=None, crop=None):
    """
    Train on multi-year data.
    Uses TimeSeriesSplit cross-validation so the model is evaluated
    the same way it will be used (training on past, testing on future).

    Returns (model, metrics_dict, df_features)
    """
    if state is not None and district is not None and crop is not None and model_name is None:
        model_name = model_path(state, district, crop)

    df_features = prepare_features(df)
    if df_features.empty or len(df_features) < 30:
        return None, None, df_features

    available = [c for c in FEATURE_COLS if c in df_features.columns]
    X = df_features[available]
    y = df_features["modal_price"]

    n_years = df_features["year"].nunique() if "year" in df_features.columns else 1

    # more estimators for more data
    n_est = min(500, 100 + n_years * 50)

    model = GradientBoostingRegressor(
        n_estimators   = n_est,
        learning_rate  = 0.05,
        max_depth      = 4,
        subsample      = 0.8,
        min_samples_leaf = 5,
        random_state   = 42,
    )

    # time-series cross-validation
    tscv = TimeSeriesSplit(n_splits=min(5, max(2, len(X)//50)))
    mae_scores, mape_scores = [], []
    for train_idx, val_idx in tscv.split(X):
        if len(train_idx) < 15 or len(val_idx) < 5:
            continue
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        preds = model.predict(X.iloc[val_idx])
        mae_scores.append(mean_absolute_error(y.iloc[val_idx], preds))
        try:
            mape_scores.append(mean_absolute_percentage_error(y.iloc[val_idx], preds) * 100)
        except Exception:
            pass

    # final fit on all data
    model.fit(X, y)

    metrics = {
        "mae":         round(float(np.mean(mae_scores)), 2)  if mae_scores  else None,
        "mape_pct":    round(float(np.mean(mape_scores)), 1) if mape_scores else None,
        "n_records":   len(df_features),
        "n_years":     n_years,
        "n_estimators": n_est,
    }

    if model_name:
        try:
            joblib.dump(model, model_name)
        except Exception:
            pass

    return model, metrics, df_features


# ── forecasting ────────────────────────────────────────────────────────────────

def recursive_forecast(model, df_features: pd.DataFrame, n_days: int = 90) -> pd.DataFrame:
    """
    Multi-year-aware autoregressive forecast.

    Key improvement: lag365 (same day last year) gives the model a real
    anchor for seasonal prediction — wheat spikes in March because
    lag365 from last March's data tells it so.
    """
    if model is None or df_features is None or df_features.empty:
        return pd.DataFrame()

    df_features = df_features.copy()
    df_features["arrival_date"] = pd.to_datetime(df_features["arrival_date"], errors="coerce")
    df_features = (df_features.dropna(subset=["arrival_date","modal_price"])
                               .sort_values("arrival_date")
                               .reset_index(drop=True))
    if df_features.empty:
        return pd.DataFrame()

    seasonal_map = df_features.groupby("dayofyear")["modal_price"].mean().to_dict()
    monthly_map  = df_features.groupby("month")["modal_price"].mean().to_dict()
    series       = df_features["modal_price"].tolist()
    last_date    = df_features["arrival_date"].iloc[-1]
    available    = [c for c in FEATURE_COLS if c in df_features.columns]
    n_years      = df_features["year"].nunique() if "year" in df_features.columns else 1

    # pre-compute multi-year monthly averages for yoy features
    multi_yr_monthly: dict = {}
    if "year" in df_features.columns and "month" in df_features.columns:
        multi_yr_monthly = (
            df_features.groupby(["year","month"])["modal_price"].mean()
                        .reset_index()
                        .groupby("month")["modal_price"].mean()
                        .to_dict()
        )

    results = []
    for _ in range(int(n_days)):
        next_date = last_date + pd.Timedelta(days=1)
        d   = next_date.day
        m   = next_date.month
        y   = next_date.year
        doy = next_date.timetuple().tm_yday
        woy = doy // 7 + 1
        q   = (m - 1) // 3 + 1

        n = len(series)
        fallback = float(np.mean(series[-30:])) if series else 0.0

        lag1   = series[-1]   if n >= 1   else fallback
        lag7   = series[-7]   if n >= 7   else fallback
        lag14  = series[-14]  if n >= 14  else fallback
        lag30  = series[-30]  if n >= 30  else fallback
        lag90  = series[-90]  if n >= 90  else fallback
        lag365 = series[-365] if n >= 365 else seasonal_map.get(doy, fallback)

        r7m  = float(np.mean(series[-7:]))   if n >= 1  else fallback
        r14m = float(np.mean(series[-14:]))  if n >= 1  else fallback
        r30m = float(np.mean(series[-30:]))  if n >= 1  else fallback
        r90m = float(np.mean(series[-90:]))  if n >= 1  else fallback
        r7s  = float(np.std(series[-7:]))    if n >= 2  else 0.0
        r30s = float(np.std(series[-30:]))   if n >= 2  else 0.0

        seasonal = seasonal_map.get(doy, fallback)
        monthly  = monthly_map.get(m,   fallback)

        # YOY change: compare lag365 (same day last year) vs current
        yoy_chg = ((lag1 - lag365) / lag365) if lag365 > 0 else 0.0
        p_vs_5yr = (lag1 / multi_yr_monthly.get(m, lag1)) - 1.0 if multi_yr_monthly else 0.0

        # trend slope (use last 90 predictions if available)
        trend = 0.0
        if n >= 90:
            recent90 = np.array(series[-90:])
            x = np.arange(90)
            trend = float(np.polyfit(x, recent90, 1)[0])

        feat_dict = {
            "day":d, "month":m, "year":y, "dayofyear":doy, "weekofyear":woy, "quarter":q,
            "lag1":lag1, "lag7":lag7, "lag14":lag14, "lag30":lag30, "lag90":lag90, "lag365":lag365,
            "roll7_mean":r7m, "roll14_mean":r14m, "roll30_mean":r30m, "roll90_mean":r90m,
            "roll7_std":r7s, "roll30_std":r30s,
            "seasonal_mean":seasonal, "monthly_mean":monthly,
            "yoy_month_change":yoy_chg, "price_vs_5yr_avg":p_vs_5yr, "trend_90d":trend,
        }
        feat = pd.DataFrame([{k: feat_dict[k] for k in available}])

        try:
            pred = float(model.predict(feat)[0])
            # clip to realistic range relative to recent prices
            pred = float(np.clip(pred, r90m * 0.35, r90m * 2.8))
        except Exception:
            pred = lag1

        results.append({"arrival_date": next_date, "predicted_modal_price": round(pred, 2)})
        series.append(pred)
        last_date = next_date

    return pd.DataFrame(results)
