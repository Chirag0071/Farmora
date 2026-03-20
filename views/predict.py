# views/predict.py
import streamlit as st
import pandas as pd
import requests
from views.profile import INDIAN_STATES, FASTAPI_BASE

DEFAULT_CROPS = [
    "Wheat","Rice","Potato","Tomato","Onion","Capsicum","Brinjal",
    "Cauliflower","Cabbage","Carrot","Garlic","Ginger","Peas","Coriander",
    "Bitter Gourd","Bottle Gourd","Lady Finger","Banana","Mango","Apple",
]


@st.cache_data(show_spinner=False, ttl=3600)
def _get_districts(state: str):
    try:
        r = requests.get(f"{FASTAPI_BASE}/districts/{state}", timeout=20)
        if r.status_code == 200:
            data = r.json()
            return data.get("districts", []), data.get("source", "unknown")
    except Exception:
        pass
    return [], "unavailable"


@st.cache_data(show_spinner=False, ttl=3600)
def _get_crops(state: str, district: str = ""):
    try:
        params = {"district": district} if district else {}
        r = requests.get(f"{FASTAPI_BASE}/crops/{state}", params=params, timeout=20)
        if r.status_code == 200:
            c = r.json().get("crops", [])
            return c if c else DEFAULT_CROPS
    except Exception:
        pass
    return DEFAULT_CROPS


@st.cache_data(show_spinner=False, ttl=60)
def _get_health():
    try:
        r = requests.get(f"{FASTAPI_BASE}/health", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _predict(payload: dict):
    try:
        r = requests.post(f"{FASTAPI_BASE}/predict", json=payload, timeout=120)
        if r.status_code == 200:
            return r.json(), None
        return None, f"Server error {r.status_code}: {r.text[:300]}"
    except requests.exceptions.ConnectionError:
        return None, "❌ Cannot reach backend. Run: `uvicorn backend.api:app --reload --port 8000`"
    except Exception as e:
        return None, str(e)


def app():
    st.markdown('<h1 class="page-title">🌱 Price Prediction</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Historical prices + ML forecast from multi-year data</p>',
                unsafe_allow_html=True)

    # ── data source status banner ─────────────────────────────────────────
    health = _get_health()
    if health:
        csv_records = health.get("csv_records", 0)
        dr = health.get("data_range", {})
        if csv_records > 0:
            st.success(
                f"✅ **Hybrid Mode Active** — "
                f"Historical dataset: **{csv_records:,} records** "
                f"({dr.get('from','?')} → {dr.get('to','?')}) "
                f"+ Live API data merged"
            )
        else:
            st.warning(
                "⚠️ **Live API Only** — Historical CSV not loaded. "
                "Forecasts use only recent data (limited accuracy). "
                "See `data/README_DATASET.md` to download the full dataset."
            )
    else:
        st.error("❌ Backend not running. Start it with: `uvicorn backend.api:app --reload --port 8000`")

    if not st.session_state.get("user_logged_in", False):
        st.markdown("""
        <div class="farm-card" style="text-align:center;padding:2rem">
            <div style="font-size:3rem">🔒</div>
            <div class="farm-card-title">Profile Required</div>
            <div style="color:#78909c">Please create a profile first</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👤 Create Profile", type="primary", use_container_width=True):
            st.session_state.current_page = "Profile"
            st.rerun()
        return

    st.markdown(f"""
    <div class="farm-card" style="padding:1rem 1.4rem;display:flex;align-items:center;gap:1rem">
        <div style="font-size:2rem">👋</div>
        <div>
            <div style="font-weight:600;color:#e8f5e9">
                Welcome, {st.session_state.get('user_name','Farmer')}!
            </div>
            <div style="font-size:0.82rem;color:#78909c">
                Select your crop and location to get multi-year price analysis + forecast
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Step 1: Location ──────────────────────────────────────────────────
    st.markdown("#### 📍 Step 1 · Location")
    col1, col2 = st.columns(2)
    with col1:
        sv_state  = st.session_state.get("user_state", INDIAN_STATES[0])
        st_idx    = INDIAN_STATES.index(sv_state) if sv_state in INDIAN_STATES else 0
        state_sel = st.selectbox("🗺️ State", INDIAN_STATES, index=st_idx)
    with col2:
        with st.spinner("Loading districts…"):
            districts, dist_src = _get_districts(state_sel)
        if districts:
            sv_city  = st.session_state.get("user_city","").strip().title()
            d_idx    = districts.index(sv_city) if sv_city in districts else 0
            dist_sel = st.selectbox(
                f"🏙️ District  ({len(districts)} in AGMARKNET)", districts, index=d_idx
            )
        else:
            st.info("⚠️ Backend offline — type district manually")
            dist_sel = st.text_input("🏙️ District", value=st.session_state.get("user_city",""))

    # ── Step 2: Crop ──────────────────────────────────────────────────────
    st.markdown("#### 🌾 Step 2 · Crop")
    with st.spinner("Loading crops…"):
        crops = _get_crops(state_sel, dist_sel if dist_sel else "")
    col3, col4 = st.columns([2,1])
    with col3:
        crop_sel = st.selectbox(f"🌾 Crop  ({len(crops)} available)", crops)
    with col4:
        custom = st.text_input("✏️ Or type custom name", placeholder="e.g. Jowar")
    if custom.strip():
        crop_sel = custom.strip().title()

    # ── Step 3: Parameters ────────────────────────────────────────────────
    st.markdown("#### ⚙️ Step 3 · Parameters")
    p1, p2 = st.columns(2)
    with p1:
        n_days = st.slider("📅 Forecast days ahead", 7, 180, 30, 7,
                           help="Up to 180 days with multi-year data")
    with p2:
        prod_cost = st.number_input("💰 Production cost (₹/qtl)  [0 = skip]",
                                     min_value=0.0, value=0.0, format="%.2f")

    st.markdown(f"""
    <div class="farm-card" style="margin-top:0.5rem">
        <div style="display:flex;gap:2rem;flex-wrap:wrap">
            <div><div class="farm-card-sub">Crop</div>
                 <div style="color:#fff;font-weight:600;font-size:1.1rem">{crop_sel}</div></div>
            <div><div class="farm-card-sub">Location</div>
                 <div style="color:#fff;font-weight:600">{dist_sel or 'All'}, {state_sel}</div></div>
            <div><div class="farm-card-sub">Forecast Period</div>
                 <div style="color:#FF9800;font-weight:600">{n_days} days</div></div>
            <div><div class="farm-card-sub">Production Cost</div>
                 <div style="color:#fff;font-weight:600">
                     {"₹{:,.0f}/qtl".format(prod_cost) if prod_cost > 0 else "Not set"}
                 </div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🔍 Get Price History & Forecast", type="primary", use_container_width=True):
        payload = {
            "state":           state_sel,
            "district":        dist_sel or "",
            "crop":            crop_sel,
            "n_days":          int(n_days),
            "production_cost": float(prod_cost) if prod_cost > 0 else None,
        }

        prog = st.progress(0, text="🔄 Loading historical data…")
        with st.spinner(f"Merging CSV + live data for **{crop_sel}**…"):
            data, err = _predict(payload)
        prog.progress(70, text="🤖 Training ML model on multi-year data…")

        if err:
            prog.empty()
            st.error(err)
            return

        prog.progress(100, text="✅ Done!")
        prog.empty()

        records = data.get("records", []) if data else []
        if not records:
            st.error(
                f"❌ No data found for **{crop_sel}** in **{state_sel}**.\n\n"
                f"{data.get('message','')}\n\n"
                "**Try:** different district, different crop, or check dataset setup."
            )
            return

        df = pd.DataFrame(records)
        if "arrival_date" in df.columns:
            df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")
        if "modal_price" in df.columns:
            df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")

        st.session_state.update({
            "result_data":       df,
            "selected_crop":     crop_sel,
            "production_cost":   prod_cost,
            "district_selected": dist_sel or state_sel,
            "state_selected":    state_sel,
            "forecast":          data.get("forecast", []),
            "profit_estimate":   data.get("profit_estimate", None),
            "model_metrics":     data.get("model_metrics", None),
            "data_source":       data.get("data_source","unknown"),
            "year_range":        data.get("year_range", {}),
        })

        n_fc = len(data.get("forecast", []))
        yr   = data.get("year_range", {})
        yr_str = f" ({yr.get('from','?')} → {yr.get('to','?')})" if yr else ""
        src = "📚 CSV + 🌐 Live API" if data.get("data_source") == "csv+live" else "🌐 Live API only"

        st.success(
            f"✅ **{len(df):,} records{yr_str}** · Source: {src}\n"
            f"**{n_fc}-day forecast** generated!  Redirecting to Results…"
        )
        st.balloons()
        st.session_state.current_page = "Result"
        st.rerun()

    with st.expander("💡 How Hybrid Mode Works"):
        st.markdown("""
        **Hybrid Data Strategy:**

        | Source | What it provides |
        |--------|-----------------|
        | 📚 Historical CSV | 10+ years of prices (2010–2023) — enables seasonal learning |
        | 🌐 Live AGMARKNET API | Last 90 days — keeps the model current |

        Both are merged, deduplicated, and sorted before training.

        **The ML model learns:**
        - Which months have high/low prices (seasonal patterns)
        - Year-over-year price trends
        - Short-term price momentum
        - Price deviation from 5-year average

        **Without the CSV** the model only sees 3-6 months — it cannot learn seasonal patterns.
        [Download instructions →](data/README_DATASET.md)
        """)
