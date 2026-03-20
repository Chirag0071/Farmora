# views/seasonality.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def seasonality_analysis(df: pd.DataFrame, crop_name: str):
    if df is None or df.empty: return
    if "arrival_date" not in df.columns or "modal_price" not in df.columns: return

    w = df.copy()
    w["arrival_date"] = pd.to_datetime(w["arrival_date"], errors="coerce")
    w["modal_price"]  = pd.to_numeric(w["modal_price"],   errors="coerce")
    w = w.dropna(subset=["arrival_date","modal_price"])
    if w.empty: return

    w["month"] = w["arrival_date"].dt.month
    m = (w.groupby("month")["modal_price"]
          .agg(avg="mean", lo="min", hi="max")
          .reindex(range(1,13)).fillna(0).reset_index())
    labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    m["name"] = labels
    peak = int(m["avg"].idxmax())

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m["name"], y=m["hi"], mode="lines",
                             line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=m["name"], y=m["lo"], fill="tonexty",
                             fillcolor="rgba(76,175,80,0.1)", mode="lines",
                             line=dict(color="rgba(0,0,0,0)"), name="Min–Max Range", hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=m["name"], y=m["avg"], mode="lines+markers", name="Monthly Avg",
        line=dict(color="#4CAF50", width=2.5),
        marker=dict(
            size=[16 if i==peak else 8 for i in range(12)],
            color=["#FF9800" if i==peak else "#4CAF50" for i in range(12)],
            symbol=["star" if i==peak else "circle" for i in range(12)],
        ),
        hovertemplate="%{x}<br>Avg ₹%{y:,.0f}/qtl<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"Monthly Price Seasonality — {crop_name}", font=dict(size=15,color="#e8f5e9")),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#78909c"), yaxis=dict(title="₹/qtl", color="#78909c"),
        height=340, font=dict(color="#e8f5e9"), margin=dict(l=10,r=10,t=50,b=10),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"⭐ **Peak month: {labels[peak]}** — avg ₹{m['avg'].iloc[peak]:,.0f}/qtl. "
            "Align your harvest/selling around this window.")
