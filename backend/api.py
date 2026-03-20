# backend/api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import logging

from backend.data_loader import (
    get_hybrid_data, get_all_districts, get_all_crops,
    fetch_live, load_csv
)
from backend.ml_model import (
    train_model, load_model_by_keys, recursive_forecast, prepare_features
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Farmora Hybrid API", version="3.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"], allow_headers=["*"],
)


class CropRequest(BaseModel):
    state:           str
    district:        str = ""
    crop:            str
    n_days:          int = 30
    production_cost: Optional[float] = None


# ── startup: pre-load CSV into memory ─────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("Loading historical CSV dataset…")
    csv = load_csv()
    if csv.empty:
        logger.warning(
            "⚠️  Historical CSV not loaded. "
            "Forecasts will use live API data only (limited history). "
            "See data/README_DATASET.md."
        )
    else:
        logger.info(f"✅  CSV ready: {len(csv):,} records")


# ── health ─────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    csv = load_csv()
    return {
        "status":       "ok",
        "version":      "3.0",
        "csv_records":  len(csv),
        "csv_loaded":   not csv.empty,
        "data_range":   {
            "from": str(csv["arrival_date"].min().date()) if not csv.empty else None,
            "to":   str(csv["arrival_date"].max().date()) if not csv.empty else None,
        },
    }


# ── metadata endpoints ─────────────────────────────────────────────────────────
@app.get("/districts/{state}")
def districts(state: str):
    d = get_all_districts(state)
    return {"districts": d, "count": len(d), "source": "csv+live"}


@app.get("/crops/{state}")
def crops(state: str, district: str = ""):
    c = get_all_crops(state, district)
    return {"crops": c, "source": "csv+live"}


@app.get("/top_crops/{state}")
def top_crops(state: str):
    c = get_all_crops(state)
    return {"top_crops": [[crop, 0] for crop in c[:20]]}


# ── main predict endpoint ──────────────────────────────────────────────────────
@app.post("/predict")
def predict_crop(req: CropRequest):
    """
    1. Merge historical CSV + live API data
    2. Train (or load cached) GradientBoosting model
    3. Forecast n_days ahead
    4. Calculate profit/loss if production_cost provided
    """
    # ── get hybrid data ────────────────────────────────────────────────────
    df = get_hybrid_data(state=req.state, district=req.district, crop=req.crop)

    if df.empty:
        return {
            "records":        [],
            "total_records":  0,
            "forecast":       [],
            "profit_estimate": None,
            "data_source":    "none",
            "message":        (
                f"No data found for '{req.crop}' in '{req.state}'. "
                "Try a different crop name or check your dataset."
            ),
        }

    # figure out data source for transparency
    csv_size = len(load_csv())
    data_source = "csv+live" if csv_size > 0 else "live_only"

    # ── records to return to frontend ──────────────────────────────────────
    records_out = df.copy()
    if "arrival_date" in records_out.columns:
        records_out["arrival_date"] = records_out["arrival_date"].dt.date.astype(str)
    for col in ["min_price", "max_price", "modal_price"]:
        if col in records_out.columns:
            records_out[col] = records_out[col].round(2)
    records_list = records_out.fillna("").to_dict(orient="records")

    response: dict = {
        "records":       records_list,
        "total_records": len(df),
        "data_source":   data_source,
        "year_range": {
            "from": str(df["arrival_date"].min().date()),
            "to":   str(df["arrival_date"].max().date()),
        } if "arrival_date" in df.columns else {},
    }

    # ── ML model ──────────────────────────────────────────────────────────
    model = load_model_by_keys(req.state, req.district, req.crop)
    df_features = None

    if model is None:
        try:
            model, metrics, df_features = train_model(
                df.copy(), state=req.state,
                district=req.district, crop=req.crop,
            )
            if metrics:
                response["model_metrics"] = metrics
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            model = None
    else:
        try:
            df_features = prepare_features(df.copy())
        except Exception:
            df_features = None

    # ── forecast ──────────────────────────────────────────────────────────
    if model is not None and df_features is not None and not df_features.empty:
        try:
            fx = recursive_forecast(model, df_features, n_days=req.n_days)
            if not fx.empty:
                fx["arrival_date"] = pd.to_datetime(fx["arrival_date"]).dt.date.astype(str)
                response["forecast"] = fx.to_dict(orient="records")
            else:
                response["forecast"] = []
        except Exception as e:
            logger.error(f"Forecast failed: {e}")
            response["forecast"] = []
    else:
        response["forecast"] = []
        response["forecast_message"] = (
            "Not enough data to train the ML model. "
            f"Got {len(df)} records, need at least 30."
        )

    # ── profit estimate ────────────────────────────────────────────────────
    if req.production_cost is not None and response.get("forecast"):
        try:
            preds    = [float(x["predicted_modal_price"]) for x in response["forecast"]]
            avg_pred = sum(preds) / len(preds)
            profit   = avg_pred - float(req.production_cost)
            response["profit_estimate"] = {
                "avg_predicted_price": round(avg_pred, 2),
                "production_cost":     round(float(req.production_cost), 2),
                "profit_per_qtl":      round(profit, 2),
            }
        except Exception:
            response["profit_estimate"] = None
    else:
        response["profit_estimate"] = None

    return response
