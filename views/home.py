# views/home.py
import streamlit as st

def app():
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem">
        <div style="font-size:4rem;margin-bottom:0.5rem">🌾</div>
        <h1 style="font-size:3rem;font-weight:800;background:linear-gradient(135deg,#66bb6a,#43a047);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0">
            Farmora
        </h1>
        <p style="color:#78909c;font-size:1.1rem;margin-top:0.5rem">
            Smart Crop Price Intelligence for Indian Farmers
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    s1,s2,s3,s4 = st.columns(4)
    for col, num, label in [
        (s1,"7,000+","Markets Tracked"),
        (s2,"28","Indian States"),
        (s3,"200+","Crops Available"),
        (s4,"ML","Price Forecasting"),
    ]:
        col.markdown(f"""
        <div class="farm-card" style="text-align:center;padding:1.2rem">
            <div style="font-size:1.8rem;font-weight:800;color:#4CAF50">{num}</div>
            <div style="color:#78909c;font-size:0.82rem;margin-top:0.2rem">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Features
    st.markdown('<h2 style="text-align:center;color:#e8f5e9;margin-bottom:1.5rem">What Farmora Does</h2>',
                unsafe_allow_html=True)
    f1,f2,f3 = st.columns(3)
    features = [
        (f1,"📈","Historical Price Trends",
         "See year-by-year price data for any crop in any district — sourced live from AGMARKNET."),
        (f2,"🔮","ML Price Forecast",
         "Our Gradient Boosting model analyses seasonal patterns and predicts prices up to 90 days ahead."),
        (f3,"💰","Profit Estimator",
         "Enter your production cost and instantly see whether you'll profit or lose at current market rates."),
    ]
    for col, icon, title, desc in features:
        col.markdown(f"""
        <div class="farm-card" style="text-align:center;height:200px">
            <div style="font-size:2.5rem;margin-bottom:0.8rem">{icon}</div>
            <div class="farm-card-title">{title}</div>
            <div style="color:#78909c;font-size:0.85rem;margin-top:0.5rem">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # How it works
    st.markdown('<h2 style="text-align:center;color:#e8f5e9;margin-bottom:1.5rem">How It Works</h2>',
                unsafe_allow_html=True)
    steps = [
        ("1","👤","Create Profile","Enter your name, state and district"),
        ("2","🌾","Select Crop","Choose from AGMARKNET-sourced crop list"),
        ("3","📊","Get Prediction","See historical prices + ML forecast"),
        ("4","💡","Make Decision","Use data to plan planting & selling"),
    ]
    cols = st.columns(4)
    for col, (num, icon, title, desc) in zip(cols, steps):
        col.markdown(f"""
        <div class="farm-card" style="text-align:center;padding:1.2rem">
            <div style="background:rgba(76,175,80,0.2);border-radius:50%;width:36px;height:36px;
                display:flex;align-items:center;justify-content:center;margin:0 auto 0.8rem;
                font-weight:700;color:#4CAF50">{num}</div>
            <div style="font-size:1.8rem">{icon}</div>
            <div style="font-weight:600;color:#e8f5e9;margin:0.4rem 0">{title}</div>
            <div style="color:#78909c;font-size:0.8rem">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    c1,c2,c3 = st.columns([2,1,2])
    with c2:
        if st.button("🚀 Get Started", type="primary", use_container_width=True):
            st.session_state.current_page = "Profile"
            st.rerun()
