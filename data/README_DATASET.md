# 📦 Dataset Setup — Read This First!

Farmora uses a **Hybrid Data Strategy**:
- **CSV file** → 10+ years of historical prices (2010–2023) for training the ML model
- **Live API** → Last 90 days of prices (always fresh, appended to CSV data)

---

## Step 1 — Download the CSV Dataset

### Option A: Kaggle (Recommended — 10 years, ~8 lakh records)
1. Go to: https://www.kaggle.com/datasets/sujaynair2000/indian-market-mandi-price-prediction
2. Click **Download** (free Kaggle account required)
3. Extract the zip → you'll get a file like `mandi_prices.csv`
4. Rename it to `agmarknet_historical.csv`
5. Place it in this `data/` folder

### Option B: data.gov.in (Official Source)
1. Go to: https://data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi
2. Download the full dataset as CSV
3. Rename to `agmarknet_historical.csv`
4. Place in this `data/` folder

### Option C: Auto-download script (runs on startup)
If you have no CSV, Farmora will run `python data/download_dataset.py` automatically
to pull as much data as possible from the live API (covers ~2 years).

---

## Step 2 — Expected CSV Format

The CSV must have these columns (case-insensitive):

| Column | Example |
|--------|---------|
| state | Punjab |
| district | Amritsar |
| market | Amritsar Mandi |
| commodity (or crop) | Wheat |
| arrival_date | 2019-03-15 |
| min_price | 1400 |
| max_price | 1600 |
| modal_price | 1500 |

The app auto-normalises column names so minor variations are fine.

---

## Step 3 — Verify

Run this from the project root to verify the dataset loaded correctly:
```bash
python data/verify_dataset.py
```

Expected output:
```
✅ Dataset loaded: 800,000 records
📅 Date range: 2010-01-01 → 2023-12-31
🌾 Unique crops: 247
🗺️  Unique states: 28
```

---

## What happens without the CSV?

The app still works — it falls back to live API only.
But forecasts will only use 3-6 months of data, making them less accurate.
