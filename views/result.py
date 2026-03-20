# views/result.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from views import geo_viz
from views.seasonality import seasonality_analysis


def _safe(v, d=0.0):
    try: return float(v)
    except: return d


def _prep(df):
    df = df.copy()
    if "arrival_date" not in df.columns or "modal_price" not in df.columns:
        return pd.DataFrame()
    df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")
    df["modal_price"]  = pd.to_numeric(df["modal_price"],   errors="coerce")
    return df.dropna(subset=["arrival_date","modal_price"]).sort_values("arrival_date").reset_index(drop=True)


# ── CHART 1: Master chart — all years + forecast ───────────────────────────────
def _chart_main(hist, fc_list, crop, year_range=None):
    fig = go.Figure()

    if hist is not None and not hist.empty:
        h = _prep(hist)
        if not h.empty:
            # colour dots by year
            h["year"] = h["arrival_date"].dt.year
            years = sorted(h["year"].unique())
            palette = ["#4CAF50","#81C784","#A5D6A7","#C8E6C9",
                       "#2196F3","#64B5F6","#FFA726","#FFD54F",
                       "#EF5350","#EF9A9A","#AB47BC","#CE93D8"]

            for i, yr in enumerate(years):
                yr_data = h[h["year"] == yr]
                color   = palette[i % len(palette)]
                fig.add_trace(go.Scatter(
                    x=yr_data["arrival_date"], y=yr_data["modal_price"],
                    mode="markers", name=str(yr),
                    marker=dict(size=3, color=color, opacity=0.5),
                    hovertemplate=f"%{{x|%d %b %Y}}<br>₹%{{y:,.0f}}/qtl<extra>{yr}</extra>",
                    legendgroup=str(yr),
                ))

            # 90-day rolling mean
            d2 = h.set_index("arrival_date").resample("D")["modal_price"].mean().reset_index()
            d2["r90"] = d2["modal_price"].rolling(90, min_periods=7).mean()
            fig.add_trace(go.Scatter(
                x=d2["arrival_date"], y=d2["r90"],
                mode="lines", name="90-day Trend",
                line=dict(color="#29b6f6", width=3),
                hovertemplate="%{x|%b %Y}<br>₹%{y:,.0f}/qtl<extra>90-day Trend</extra>",
            ))

    if fc_list:
        fdf = pd.DataFrame(fc_list)
        fdf["arrival_date"]          = pd.to_datetime(fdf["arrival_date"], errors="coerce")
        fdf["predicted_modal_price"] = pd.to_numeric(fdf["predicted_modal_price"], errors="coerce")
        fdf = fdf.dropna().sort_values("arrival_date")
        if not fdf.empty:
            up = fdf["predicted_modal_price"] * 1.10
            lo = fdf["predicted_modal_price"] * 0.90
            fig.add_trace(go.Scatter(
                x=pd.concat([fdf["arrival_date"], fdf["arrival_date"].iloc[::-1]]),
                y=pd.concat([up, lo.iloc[::-1]]),
                fill="toself", fillcolor="rgba(255,152,0,0.13)",
                line=dict(color="rgba(0,0,0,0)"), name="±10% Band", hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter(
                x=fdf["arrival_date"], y=fdf["predicted_modal_price"],
                mode="lines+markers", name="🔮 ML Forecast",
                line=dict(color="#FF9800", width=3, dash="dash"),
                marker=dict(size=7, symbol="diamond", color="#FF9800",
                            line=dict(color="#fff",width=1)),
                hovertemplate="%{x|%d %b %Y}<br><b>Forecast ₹%{y:,.0f}/qtl</b><extra></extra>",
            ))

    yr_title = f" ({year_range['from']} → {year_range['to']})" if year_range else ""
    fig.update_layout(
        title=dict(text=f"Price History{yr_title} + ML Forecast — {crop}",
                   font=dict(size=17, color="#e8f5e9")),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#78909c", gridcolor="rgba(255,255,255,0.05)", showgrid=True),
        yaxis=dict(title="₹/qtl", color="#78909c", gridcolor="rgba(255,255,255,0.05)"),
        legend=dict(orientation="h", y=1.08, bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e8f5e9", size=10)),
        hovermode="x unified", height=520,
        font=dict(color="#e8f5e9"), margin=dict(l=10,r=10,t=70,b=10),
    )
    return fig


# ── CHART 2: Year-wise bar ─────────────────────────────────────────────────────
def _chart_yearly(hist, crop):
    h = _prep(hist)
    if h.empty: return None
    h["year"] = h["arrival_date"].dt.year
    yr = h.groupby("year")["modal_price"].agg(avg="mean",lo="min",hi="max").reset_index().sort_values("year")
    if yr.empty: return None
    avgs   = yr["avg"].tolist()
    colors = ["#4CAF50" if i==0 or v>=avgs[i-1] else "#ef5350" for i,v in enumerate(avgs)]
    fig = go.Figure(go.Bar(
        x=yr["year"].astype(str), y=yr["avg"], marker_color=colors,
        error_y=dict(type="data", symmetric=False,
                     array=(yr["hi"]-yr["avg"]).tolist(),
                     arrayminus=(yr["avg"]-yr["lo"]).tolist(),
                     color="rgba(200,200,200,0.4)"),
        hovertemplate="%{x}<br>Avg ₹%{y:,.0f}<br>Min ₹%{customdata[0]:,.0f}  Max ₹%{customdata[1]:,.0f}<extra></extra>",
        customdata=yr[["lo","hi"]].values,
    ))
    fig.update_layout(
        title=dict(text=f"Year-wise Average Price — {crop}", font=dict(size=15,color="#e8f5e9")),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#78909c"), yaxis=dict(title="₹/qtl", color="#78909c"),
        height=360, font=dict(color="#e8f5e9"), margin=dict(l=10,r=10,t=50,b=10),
    )
    return fig


# ── CHART 3: Forecast only ─────────────────────────────────────────────────────
def _chart_forecast(fc_list, crop):
    if not fc_list: return None
    fdf = pd.DataFrame(fc_list)
    fdf["arrival_date"]          = pd.to_datetime(fdf["arrival_date"], errors="coerce")
    fdf["predicted_modal_price"] = pd.to_numeric(fdf["predicted_modal_price"], errors="coerce")
    fdf = fdf.dropna().sort_values("arrival_date")
    if fdf.empty: return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fdf["arrival_date"], y=fdf["predicted_modal_price"]*1.10,
                             mode="lines", line=dict(color="rgba(0,0,0,0)"),
                             showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=fdf["arrival_date"], y=fdf["predicted_modal_price"]*0.90,
                             fill="tonexty", fillcolor="rgba(255,152,0,0.12)",
                             mode="lines", line=dict(color="rgba(0,0,0,0)"),
                             name="±10% Band", hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=fdf["arrival_date"], y=fdf["predicted_modal_price"],
        mode="lines+markers", name="Forecast",
        line=dict(color="#FF9800", width=2.5),
        marker=dict(size=8, symbol="diamond", color="#FF9800", line=dict(color="#fff",width=1)),
        hovertemplate="%{x|%d %b %Y}<br><b>₹%{y:,.0f}/qtl</b><extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"ML Price Forecast — Next {len(fdf)} Days", font=dict(size=15,color="#e8f5e9")),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#78909c"), yaxis=dict(title="₹/qtl", color="#78909c"),
        height=360, font=dict(color="#e8f5e9"), margin=dict(l=10,r=10,t=50,b=10),
    )
    return fig


# ── main page ──────────────────────────────────────────────────────────────────
def app():
    st.markdown('<h1 class="page-title">📊 Analysis Results</h1>', unsafe_allow_html=True)

    col_b, col_n = st.columns([1,5])
    with col_b:
        if st.button("← Back"):
            st.session_state.current_page = "Predict"
            st.rerun()
    with col_n:
        if st.button("🔄 New Prediction", type="primary"):
            st.session_state.current_page = "Predict"
            st.rerun()

    df = st.session_state.get("result_data")
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        st.markdown("""<div class="farm-card" style="text-align:center;padding:3rem">
            <div style="font-size:3rem">📭</div>
            <div class="farm-card-title">No Results Yet</div>
            <div style="color:#78909c">Go to Predict page to fetch data</div>
        </div>""", unsafe_allow_html=True)
        return

    crop         = st.session_state.get("selected_crop",     "Unknown")
    prod_cost    = st.session_state.get("production_cost",   0.0)
    district     = st.session_state.get("district_selected", "")
    state        = st.session_state.get("state_selected",    "")
    fc_list      = st.session_state.get("forecast",          [])
    profit_block = st.session_state.get("profit_estimate",   None)
    metrics      = st.session_state.get("model_metrics",     None)
    data_src     = st.session_state.get("data_source",       "unknown")
    year_range   = st.session_state.get("year_range",        {})

    # ── data source badge ──────────────────────────────────────────────────
    src_color = "#4CAF50" if data_src == "csv+live" else "#FF9800"
    src_label = "📚 CSV + 🌐 Live API (Hybrid)" if data_src == "csv+live" else "🌐 Live API Only"
    st.markdown(
        f'<div style="display:inline-block;background:{src_color}22;border:1px solid {src_color}55;'
        f'border-radius:20px;padding:0.3rem 0.9rem;font-size:0.82rem;color:{src_color};margin-bottom:1rem">'
        f'Data Source: {src_label}</div>',
        unsafe_allow_html=True
    )

    # ── header card ────────────────────────────────────────────────────────
    yr_str = f"{year_range.get('from','?')} → {year_range.get('to','?')}" if year_range else "—"
    st.markdown(f"""
    <div class="farm-card">
        <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem">
            <div>
                <div style="font-size:1.6rem;font-weight:700;color:#fff">{crop}</div>
                <div style="color:#78909c">📍 {district}, {state}</div>
            </div>
            <div style="display:flex;gap:2rem;flex-wrap:wrap">
                <div><div class="farm-card-sub">Total Records</div>
                     <div style="color:#4CAF50;font-weight:700;font-size:1.3rem">{len(df):,}</div></div>
                <div><div class="farm-card-sub">Data Span</div>
                     <div style="color:#29b6f6;font-weight:700">{yr_str}</div></div>
                <div><div class="farm-card-sub">Forecast Days</div>
                     <div style="color:#FF9800;font-weight:700;font-size:1.3rem">{len(fc_list)}</div></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── clean df ───────────────────────────────────────────────────────────
    df = df.copy()
    df["modal_price"]  = pd.to_numeric(df.get("modal_price"),  errors="coerce").fillna(0)
    df["arrival_date"] = pd.to_datetime(df.get("arrival_date"), errors="coerce")
    try:
        df["arrival_date_display"] = df["arrival_date"].dt.strftime("%d %b %Y")
    except Exception:
        df["arrival_date_display"] = df["arrival_date"].astype(str)

    prices = df["modal_price"].replace(0, pd.NA).dropna()

    # ── KPI row ────────────────────────────────────────────────────────────
    if not prices.empty:
        years = df["arrival_date"].dropna().dt.year
        k1,k2,k3,k4,k5 = st.columns(5)
        k1.metric("📦 Records",      f"{len(df):,}")
        k2.metric("📅 Year Span",    f"{int(years.min())}–{int(years.max())}" if not years.empty else "—")
        k3.metric("📉 Lowest",       f"₹{prices.min():,.0f}")
        k4.metric("📈 Highest",      f"₹{prices.max():,.0f}")
        k5.metric("⚖️ Overall Avg",  f"₹{prices.mean():,.0f}")

    # ── model quality info ─────────────────────────────────────────────────
    if metrics:
        mae  = metrics.get("mae")
        mape = metrics.get("mape_pct")
        nyrs = metrics.get("n_years", 1)
        nrec = metrics.get("n_records", 0)
        st.markdown(
            f"<div style='font-size:0.8rem;color:#78909c;margin-bottom:0.5rem'>"
            f"🤖 Model trained on <b style='color:#81c784'>{nrec:,} records</b> across "
            f"<b style='color:#81c784'>{nyrs} years</b>"
            + (f" · MAE ₹{mae:,.0f}" if mae else "")
            + (f" · MAPE {mape:.1f}%" if mape else "")
            + "</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── TABS ───────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Price Charts", "🔮 Forecast", "💰 Profit/Loss", "📅 Records", "🗺️ More"
    ])

    with tab1:
        st.markdown("#### Historical Prices Across All Years + ML Forecast")
        st.caption(
            "Each coloured dot = one day's price · "
            "Colours = different years · "
            "Blue line = 90-day trend · "
            "Orange = ML forecast"
        )
        st.plotly_chart(_chart_main(df, fc_list, crop, year_range), use_container_width=True)

        yfig = _chart_yearly(df, crop)
        if yfig:
            st.markdown("#### Year-wise Average Prices")
            st.caption("🟢 Green = rose vs prior year · 🔴 Red = fell · Error bars = min/max range")
            st.plotly_chart(yfig, use_container_width=True)

    with tab2:
        if fc_list:
            ffig = _chart_forecast(fc_list, crop)
            if ffig:
                st.plotly_chart(ffig, use_container_width=True)

            fdf = pd.DataFrame(fc_list)
            fdf["arrival_date"]          = pd.to_datetime(fdf["arrival_date"], errors="coerce")
            fdf["predicted_modal_price"] = pd.to_numeric(fdf["predicted_modal_price"], errors="coerce")
            fdf = fdf.dropna().sort_values("arrival_date")
            preds = fdf["predicted_modal_price"]

            if not preds.empty:
                f1,f2,f3 = st.columns(3)
                f1.metric("🔮 Forecast Low",  f"₹{preds.min():,.0f}/qtl")
                f2.metric("🔮 Forecast Avg",  f"₹{preds.mean():,.0f}/qtl")
                f3.metric("🔮 Forecast High", f"₹{preds.max():,.0f}/qtl")

            with st.expander("📋 Full Forecast Table"):
                show = fdf.copy()
                show["Date"]  = show["arrival_date"].dt.strftime("%d %b %Y")
                show["Price (₹/qtl)"] = show["predicted_modal_price"].map(lambda v: f"₹{v:,.0f}")
                st.dataframe(show[["Date","Price (₹/qtl)"]].reset_index(drop=True),
                             use_container_width=True, hide_index=True)
        else:
            st.markdown("""<div class="farm-card" style="text-align:center;padding:2rem">
                <div style="font-size:2.5rem">🤖</div>
                <div class="farm-card-title">Forecast Unavailable</div>
                <div style="color:#78909c">Need ≥30 records. Load the historical CSV for best results.</div>
            </div>""", unsafe_allow_html=True)

    with tab3:
        if profit_block:
            avg_p  = _safe(profit_block.get("avg_predicted_price"))
            cost   = _safe(profit_block.get("production_cost"))
            profit = _safe(profit_block.get("profit_per_qtl"))
            color  = "#4CAF50" if profit >= 0 else "#ef5350"
            label  = "PROFIT" if profit >= 0 else "LOSS"
            st.markdown(f"""
            <div class="farm-card" style="text-align:center;padding:2rem;border-color:{color}55">
                <div style="font-size:3rem">{"✅" if profit>=0 else "❌"}</div>
                <div style="font-size:2.5rem;font-weight:800;color:{color}">₹{abs(profit):,.0f}/qtl</div>
                <div style="color:#78909c;font-size:1rem">Expected {label} per Quintal</div>
            </div>
            """, unsafe_allow_html=True)
            p1,p2,p3 = st.columns(3)
            p1.metric("Avg Forecast Price",   f"₹{avg_p:,.0f}/qtl")
            p2.metric("Your Production Cost", f"₹{cost:,.0f}/qtl")
            p3.metric("Net Profit/Loss",       f"₹{profit:,.0f}/qtl",
                      delta="Profit ✅" if profit>=0 else "Loss ❌",
                      delta_color="normal" if profit>=0 else "inverse")
            if profit > 0:
                st.success(f"✅ Expected to earn **₹{profit:,.0f} per quintal** based on ML forecast.")
            else:
                st.error(f"⚠️ Expected loss of **₹{abs(profit):,.0f}/qtl**. Consider waiting or switching crops.")
        else:
            st.markdown("""<div class="farm-card" style="text-align:center;padding:2rem">
                <div style="font-size:2.5rem">💰</div>
                <div class="farm-card-title">Enter Production Cost</div>
                <div style="color:#78909c">Go to Predict page and enter your production cost (₹/qtl)</div>
            </div>""", unsafe_allow_html=True)

    with tab4:
        st.markdown("#### 📅 Latest 30 Market Records")
        recent = df.sort_values("arrival_date", ascending=False).head(30)
        for _, rec in recent.iterrows():
            modal  = _safe(rec.get("modal_price", 0))
            pl_txt = ""
            if prod_cost and prod_cost > 0:
                pl = modal - _safe(prod_cost)
                pl_txt = f" · {'✅ Profit' if pl>=0 else '❌ Loss'} ₹{abs(pl):,.0f}"
            mkt = rec.get("market") or "—"
            d   = rec.get("district") or district
            s   = rec.get("state")    or state
            dt  = rec.get("arrival_date_display") or str(rec.get("arrival_date",""))
            st.markdown(
                f"**{dt}** · 🏬 {mkt} · {d}, {s} · "
                f"Min ₹{rec.get('min_price','—')} · Max ₹{rec.get('max_price','—')} · "
                f"**Modal ₹{modal:,.0f}**/qtl{pl_txt}"
            )
            st.divider()
        with st.expander("🗂️ Full Raw Data Table"):
            st.dataframe(df, use_container_width=True)

    with tab5:
        with st.expander("📆 Seasonality Analysis", expanded=True):
            try:
                seasonality_analysis(df, crop)
            except Exception as e:
                st.error(f"Seasonality failed: {e}")
        with st.expander("🗺️ Market Locations Map"):
            try:
                geo_viz.map_markets(df, place_col="market", state_col="state", n_points=100)
            except Exception as e:
                st.error(f"Map failed: {e}")
