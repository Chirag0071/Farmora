# views/contact.py
import streamlit as st

def app():
    st.markdown("<h1 style='text-align:center;'>📞 Contact Us</h1>", unsafe_allow_html=True)
    st.write("Have questions or feedback? We'd love to hear from you.")

    st.markdown("### 📬 Quick Contact Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**📞 Phone**")
        st.write("+91 7217204***")
    with col2:
        st.markdown("**📨 Email**")
        st.write("SupportFarmora@gmail.com")
    with col3:
        st.markdown("**🏢 Office**")
        st.write("M.G Road, India")

    st.markdown("---")

    st.markdown("### 📝 Send Us a Message")
    with st.form("contact_form"):
        name    = st.text_input("Your Name")
        email   = st.text_input("Your Email")
        subject = st.selectbox("Subject", [
            "General Inquiry",
            "Bug Report",
            "Feature Request",
            "Data Issue",
            "Other",
        ])
        message = st.text_area("Your Message", height=140)
        submitted = st.form_submit_button("Send Message ✉️")
        if submitted:
            if not name.strip() or not email.strip() or not message.strip():
                st.warning("⚠️ Please fill in all fields before submitting.")
            else:
                st.success(
                    f"✅ Thank you **{name}**! Your message has been received. "
                    "We'll get back to you within 2 working days."
                )

    st.caption("We value your feedback to make Farmora better for every farmer.")
