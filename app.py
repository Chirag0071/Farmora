# app.py
import streamlit as st

st.set_page_config(
    page_title="Farmora 🌾",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1628 0%, #0d2137 50%, #0a1628 100%);
    border-right: 1px solid rgba(76,175,80,0.2);
}
[data-testid="stSidebar"] * { color: #e8f5e9 !important; }

.nav-brand {
    text-align: center;
    padding: 1.2rem 0 0.5rem;
    font-size: 1.6rem;
    font-weight: 700;
    background: linear-gradient(135deg, #66bb6a, #43a047);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 1px;
}
.nav-tagline {
    text-align: center;
    font-size: 0.72rem;
    color: #81c784 !important;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
}
.nav-user-box {
    background: rgba(76,175,80,0.12);
    border: 1px solid rgba(76,175,80,0.3);
    border-radius: 10px;
    padding: 0.6rem 0.8rem;
    margin: 0 0.5rem 1rem;
    text-align: center;
    font-size: 0.85rem;
}
.nav-section-label {
    font-size: 0.65rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4CAF50 !important;
    padding: 0 0.5rem;
    margin: 0.5rem 0 0.2rem;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 0.55rem 1rem;
    font-size: 0.92rem;
    color: #c8e6c9 !important;
    transition: all 0.2s;
    margin-bottom: 2px;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(76,175,80,0.2) !important;
    color: #fff !important;
    transform: translateX(3px);
}
.nav-active > button {
    background: linear-gradient(90deg,rgba(76,175,80,0.35),rgba(76,175,80,0.1)) !important;
    border-left: 3px solid #4CAF50 !important;
    color: #fff !important;
    font-weight: 600 !important;
}

/* ── Main content ── */
[data-testid="stAppViewContainer"] > .main {
    background: #0e1117;
}
.block-container { padding-top: 1.5rem !important; }

/* ── Cards ── */
.farm-card {
    background: linear-gradient(135deg, #1a2332, #1e2d3d);
    border: 1px solid rgba(76,175,80,0.2);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s, transform 0.2s;
}
.farm-card:hover {
    border-color: rgba(76,175,80,0.5);
    transform: translateY(-2px);
}
.farm-card-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #81c784;
    margin-bottom: 0.4rem;
}
.farm-card-value {
    font-size: 2rem;
    font-weight: 700;
    color: #ffffff;
}
.farm-card-sub {
    font-size: 0.8rem;
    color: #78909c;
    margin-top: 0.15rem;
}

/* ── Metric override ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg,#1a2332,#1e2d3d) !important;
    border: 1px solid rgba(76,175,80,0.25) !important;
    border-radius: 12px !important;
    padding: 0.8rem 1rem !important;
}
[data-testid="stMetricValue"] { color: #fff !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #81c784 !important; }
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

/* ── Buttons ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #43a047, #2e7d32) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.65rem 1.5rem !important;
    box-shadow: 0 4px 15px rgba(76,175,80,0.3) !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(76,175,80,0.45) !important;
}

/* ── Inputs ── */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #1a2332 !important;
    border: 1px solid rgba(76,175,80,0.3) !important;
    border-radius: 8px !important;
    color: #e8f5e9 !important;
}
.stSelectbox > div > div:focus-within,
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #4CAF50 !important;
    box-shadow: 0 0 0 2px rgba(76,175,80,0.15) !important;
}
label { color: #81c784 !important; font-weight: 500 !important; }

/* ── Divider ── */
hr { border-color: rgba(76,175,80,0.15) !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #1a2332 !important;
    border: 1px solid rgba(76,175,80,0.2) !important;
    border-radius: 8px !important;
    color: #81c784 !important;
}

/* ── Info / Success / Error ── */
.stAlert { border-radius: 10px !important; }

/* ── Slider ── */
.stSlider > div > div > div > div { background: #4CAF50 !important; }

/* ── Page title style ── */
.page-title {
    font-size: 2rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(135deg, #66bb6a, #43a047);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.page-subtitle {
    text-align: center;
    color: #78909c;
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── page imports ──────────────────────────────────────────────────────────────
from views import home, about, profile, predict, result, help_page, contact

# ── session defaults ──────────────────────────────────────────────────────────
for key, val in [("current_page","Home"),("user_logged_in",False)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── sidebar ───────────────────────────────────────────────────────────────────
PAGES = [
    ("🏠", "Home",    "Home"),
    ("ℹ️", "About",   "About"),
    ("👤", "Profile", "Profile"),
    ("🌱", "Predict", "Predict"),
    ("📊", "Results", "Result"),
    ("❓", "Help",    "Help"),
    ("📞", "Contact", "Contact"),
]

with st.sidebar:
    st.markdown('<div class="nav-brand">🌾 Farmora</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-tagline">Smart Crop Intelligence</div>', unsafe_allow_html=True)

    if st.session_state.user_logged_in:
        st.markdown(
            f'<div class="nav-user-box">✅ <b>{st.session_state.get("user_name","Farmer")}</b><br>'
            f'<span style="font-size:0.78rem;color:#81c784">'
            f'{st.session_state.get("user_state","")}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="nav-user-box">👤 Not logged in</div>', unsafe_allow_html=True)

    st.markdown('<div class="nav-section-label">Navigation</div>', unsafe_allow_html=True)

    for icon, label, key in PAGES:
        is_active = st.session_state.current_page == key
        css = "nav-active" if is_active else ""
        st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.current_page = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        '<p style="text-align:center;font-size:0.72rem;color:#455a64">'
        'Farmora v2.0<br>Powered by AGMARKNET</p>',
        unsafe_allow_html=True,
    )

# ── router ────────────────────────────────────────────────────────────────────
PAGE_MAP = {
    "Home": home, "About": about, "Profile": profile,
    "Predict": predict, "Result": result, "Help": help_page, "Contact": contact,
}
PAGE_MAP.get(st.session_state.current_page, home).app()
