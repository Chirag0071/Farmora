# views/help_page.py
import streamlit as st

def app():
    st.markdown("<h1 style='text-align:center;'>❓ Help & Instructions</h1>", unsafe_allow_html=True)

    st.success("🌱 Welcome to Farmora — the Smart Crop Price Prediction System")

    st.header("💡 What This App Does")
    st.write(
        "Farmora fetches real mandi (wholesale market) price records from the "
        "Indian government's AGMARKNET database, trains a Machine Learning model "
        "on your district's historical prices, and forecasts where prices are "
        "heading — so you can make smarter planting and selling decisions."
    )

    st.header("📝 Step-by-step Guide")
    steps = [
        ("1️⃣ Create Profile",      "Go to **Profile** in the sidebar. Enter your name and location. This pre-fills the Predict page."),
        ("2️⃣ Select State & District", "On the **Predict** page, choose your state and district from the dropdowns."),
        ("3️⃣ Choose Your Crop",    "Select the crop you want to analyse. The list is fetched live from AGMARKNET for your state."),
        ("4️⃣ Set Forecast Period", "Use the slider to choose 7–90 days ahead."),
        ("5️⃣ Enter Production Cost", "Enter your cost per quintal (₹/qtl). Leave at 0 if you only want price trends."),
        ("6️⃣ Click Predict",       "Hit **Get Price History & Forecast**. The app fetches records, trains the ML model, and shows results."),
        ("7️⃣ Read Results",        "On the Results page you get: historical price chart, year-wise bar chart, future forecast chart, profit/loss estimate, seasonality analysis and market map."),
    ]
    for title, desc in steps:
        st.markdown(f"**{title}** — {desc}")

    st.header("📊 What You Get on the Results Page")
    items = [
        "📈 **Combined chart** — all historical prices (dots), 90-day rolling trend (blue line), and ML forecast (orange dashed) on one chart",
        "📊 **Year-wise bar chart** — average price per year so you can see long-term trends at a glance",
        "🔮 **Forecast chart** — zoomed-in view of predicted prices for the coming days with ±10 % confidence band",
        "💰 **Profit / Loss metric** — instant calculation based on your production cost vs forecast price",
        "📅 **Latest 30 records** — most recent market prices with individual profit/loss per row",
        "📆 **Seasonality analysis** — which months historically have the highest and lowest prices",
        "🗺️ **Market map** — geocoded mandi locations on an interactive PyDeck map",
    ]
    for item in items:
        st.markdown(f"- {item}")

    st.header("📌 Example Scenarios")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Tomato 🍅**")
        st.markdown("- Production cost: ₹800/qtl")
        st.markdown("- Forecast price: ₹600/qtl")
        st.error("→ ❌ Loss of ₹200/qtl — consider delaying harvest")
    with c2:
        st.markdown("**Capsicum 🫑**")
        st.markdown("- Production cost: ₹1200/qtl")
        st.markdown("- Forecast price: ₹2000/qtl")
        st.success("→ ✅ Profit of ₹800/qtl — great time to sell!")

    st.header("🚜 Why Use Farmora?")
    st.markdown("""
    - 🌾 Choose the **right crop at the right time**
    - 📉 Avoid overproduction in low-demand periods
    - 💹 Maximise profit by following market data
    - 🧑‍🌾 Empower yourself with **data-driven decisions**
    """)

    st.info("✅ You're all set! Head to the **Predict** page to start exploring your crop data.")
