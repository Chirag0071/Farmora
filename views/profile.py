# views/profile.py
import streamlit as st
import requests

INDIAN_STATES = [
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat",
    "Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh",
    "Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab",
    "Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh",
    "Uttarakhand","West Bengal",
]

FASTAPI_BASE = "http://127.0.0.1:8000"

@st.cache_data(show_spinner=False, ttl=3600)
def get_cities(state_name: str):
    # Primary: AGMARKNET districts via backend
    try:
        r = requests.get(f"{FASTAPI_BASE}/districts/{state_name}", timeout=15)
        if r.status_code == 200:
            d = r.json().get("districts", [])
            if d:
                return d
    except Exception:
        pass
    # Fallback: countriesnow
    try:
        r = requests.post(
            "https://countriesnow.space/api/v0.1/countries/state/cities",
            json={"country": "India", "state": state_name}, timeout=10,
        )
        return r.json().get("data", []) or []
    except Exception:
        return []


def app():
    st.markdown('<h1 class="page-title">👤 Your Profile</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Create or update your farmer profile</p>', unsafe_allow_html=True)

    if st.session_state.get("user_logged_in"):
        st.markdown(f"""
        <div class="farm-card">
            <div class="farm-card-title">✅ Currently logged in</div>
            <div style="color:#e8f5e9;font-size:1.1rem;font-weight:600">
                {st.session_state.get('user_name','—')}
            </div>
            <div style="color:#78909c;font-size:0.85rem;margin-top:0.3rem">
                {st.session_state.get('user_state','—')} · {st.session_state.get('user_city','—')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns([1,3])
        with col1:
            if st.button("✏️ Update Profile", use_container_width=True):
                st.session_state.user_logged_in = False
                st.rerun()
        with col2:
            if st.button("🌱 Go to Predict →", type="primary", use_container_width=True):
                st.session_state.current_page = "Predict"
                st.rerun()
        st.markdown("---")

    st.markdown("#### 📋 Personal Details")
    c1, c2 = st.columns(2)
    with c1:
        name  = st.text_input("Full Name *", value=st.session_state.get("user_name",""),
                               placeholder="e.g. Rajesh Kumar")
        phone = st.text_input("Phone Number", value=st.session_state.get("user_phone",""),
                               placeholder="+91 XXXXX XXXXX")
    with c2:
        email    = st.text_input("Email Address", value=st.session_state.get("user_email",""),
                                  placeholder="you@example.com")
        st.text_input("Password", type="password", placeholder="••••••••")

    st.markdown("#### 📍 Your Location")
    l1, l2 = st.columns(2)
    with l1:
        saved = st.session_state.get("user_state", INDIAN_STATES[0])
        idx   = INDIAN_STATES.index(saved) if saved in INDIAN_STATES else 0
        state = st.selectbox("State", INDIAN_STATES, index=idx)
    with l2:
        with st.spinner("Loading districts…"):
            cities = get_cities(state)
        opts     = cities if cities else ["No districts found"]
        sv_city  = st.session_state.get("user_city","")
        c_idx    = opts.index(sv_city) if sv_city in opts else 0
        city     = st.selectbox("District / City", opts, index=c_idx)

    st.markdown("")
    if st.button("💾 Save Profile & Continue →", type="primary", use_container_width=True):
        if not name.strip():
            st.warning("⚠️ Please enter your name.")
            return
        st.session_state.update({
            "user_logged_in": True, "user_name": name.strip(),
            "user_phone": phone.strip(), "user_email": email.strip(),
            "user_state": state, "user_city": city,
        })
        st.success("✅ Profile saved!")
        st.session_state.current_page = "Predict"
        st.rerun()
