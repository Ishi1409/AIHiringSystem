"""
AI Hiring Assistant — Streamlit App
Data-science powered: skill analytics, candidate ranking, resume parsing.
Uses Streamlit's native dark theme (configured in .streamlit/config.toml).
No external auth needed — runs fully local with JSON storage.
"""
import streamlit as st

st.set_page_config(
    page_title="HireAI — AI Hiring Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "page" not in st.session_state:
    st.session_state.page = "dashboard"


def main_app():
    st.markdown(
        '<div style="padding: 8px 0 16px 0; border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 8px;">'
        '<span style="font-size: 20px; font-weight: 700; background: linear-gradient(135deg, #818cf8, #6366f1); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">HireAI</span>'
        '<span style="color: #52525b; font-size: 11px; margin-left: 12px;">⚡ Local Mode</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        '<div style="padding: 8px 0 16px 0; border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 8px;">'
        '<span style="font-size: 16px; font-weight: 700; color: #fff;">HireAI</span>'
        '<span style="color: #52525b; font-size: 11px; margin-left: 8px;">⚡ Local</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    pages = {
        "📊 Dashboard": "dashboard",
        "👤 Candidates": "candidates",
        "📄 Upload Resume": "upload",
        "💼 Jobs": "jobs",
        "🎯 Interviews": "interviews",
        "🤖 AI Interview": "interview_bot",
        "🏆 Ranking": "ranking",
        "📋 Offers": "offers",
    }

    for label, key in pages.items():
        active = st.session_state.page == key
        if st.sidebar.button(
            label,
            use_container_width=True,
            type="primary" if active else "secondary",
            key=f"nav_{key}",
        ):
            st.session_state.page = key
            st.rerun()

    page_map = {
        "dashboard": "pages.dashboard",
        "candidates": "pages.candidates",
        "upload": "pages.upload_resume",
        "jobs": "pages.jobs",
        "interviews": "pages.interviews",
        "interview_bot": "pages.interview_bot",
        "ranking": "pages.ranking",
        "offers": "pages.offers",
    }
    mod_path = page_map.get(st.session_state.page, "pages.dashboard")
    mod = __import__(mod_path, fromlist=["show"])
    mod.show()


main_app()
