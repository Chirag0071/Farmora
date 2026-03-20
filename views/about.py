# views/about.py
import streamlit as st

def app():
    st.markdown("<h1 style='text-align:center;'>🌾 About Farmora</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📖 Overview", "✨ Features", "⚙️ How It Works"])

    with tab1:
        st.header("Smart Crop Suggestion System")
        st.write("""
        Farmora is built to help **farmers and agribusinesses** across India make data-driven 
        decisions. By analysing **real market price records** from AGMARKNET (data.gov.in) 
        and combining them with **machine-learning forecasts**, Farmora tells you:

        - Which crops are fetching good prices **right now**
        - How prices have moved **over the past several years**
        - Where prices are **likely heading** in the next 7–90 days
        - Whether your production cost will result in **profit or loss**
        """)
        st.image(
            "https://images.pexels.com/photos/2132227/pexels-photo-2132227.jpeg",
            caption="Data-driven farming decisions",
            use_container_width=True,
        )

    with tab2:
        st.subheader("Key Features")
        features = [
            ("📊 Real-time Market Data",   "Live mandi prices from 7,000+ markets via data.gov.in AGMARKNET API."),
            ("🤖 ML Price Forecasting",    "RandomForest model trained on your district's historical prices with lag, seasonal and rolling features."),
            ("📈 Historical Price Charts", "Interactive Plotly charts showing past prices year-by-year so you can spot trends."),
            ("🔮 Future Price Forecast",   "Recursive autoregressive forecast for up to 90 days ahead with confidence band."),
            ("💰 Profit / Loss Estimator", "Enter your production cost and instantly see expected profit per quintal."),
            ("🌍 Location-Based",          "State → district → crop drill-down for hyper-local predictions."),
            ("📆 Seasonality Analysis",    "Month-by-month average price chart to understand seasonal peaks and troughs."),
            ("🗺️ Market Map",              "PyDeck map showing geocoded mandi locations for your crop."),
        ]
        cols = st.columns(2)
        for i, (title, desc) in enumerate(features):
            with cols[i % 2]:
                st.markdown(f"**{title}**")
                st.caption(desc)
                st.markdown("")

    with tab3:
        st.subheader("How It Works")
        steps = [
            ("1️⃣ Create Profile",    "Enter your name, state and district. This pre-fills the prediction form."),
            ("2️⃣ Select Crop",       "Choose from the top crops available for your state (fetched live from AGMARKNET)."),
            ("3️⃣ Set Parameters",    "Enter your production cost (₹/qtl) and how many days ahead you want to forecast."),
            ("4️⃣ Get Predictions",   "Farmora fetches up to 5,000 historical records, trains an ML model on the fly, and returns a forecast."),
            ("5️⃣ Analyse Results",   "See: historical price trend chart, year-wise bar chart, forecast chart, profit metric, seasonality and market map."),
            ("6️⃣ Decide Smartly",    "Use the insights to decide what to plant, when to harvest, and where to sell."),
        ]
        for icon_title, desc in steps:
            st.markdown(f"**{icon_title}** — {desc}")

        st.success("With Farmora, you reduce price risk and maximise profit by following market data.")
