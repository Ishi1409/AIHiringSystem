"""
AI Hiring Assistant — Streamlit App
Supabase Auth + local JSON storage.
Data-science powered: skill analytics, candidate ranking, resume parsing.
"""
import streamlit as st
import importlib
from services.supabase_client import sign_up, sign_in, sign_out, get_user, get_profile, is_supabase_available
from services.ml_models import models_available as ml_available

st.set_page_config(
    page_title="HireAI — AI Hiring Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session state ──────────────────────────────────────────────────
for key in ["access_token", "user_email", "user_id", "user_name", "user_role", "page"]:
    if key not in st.session_state:
        default = None if key != "page" else "dashboard"
        st.session_state[key] = default


# ── Auth Pages ─────────────────────────────────────────────────────

def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<h1 style='text-align:center; font-size:2.5rem; font-weight:700; "
            "background:linear-gradient(135deg,#818cf8,#6366f1); -webkit-background-clip:text; "
            "-webkit-text-fill-color:transparent;'>HireAI</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#71717a; margin-bottom:32px;'>AI Hiring Assistant</p>",
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown("##### Sign In")
            email = st.text_input("Email", key="login_email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")

            if st.button("Sign In", use_container_width=True, type="primary"):
                if email and password:
                    with st.spinner("Authenticating..."):
                        res, err = sign_in(email, password)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.access_token = res["access_token"]
                        st.session_state.user_email = res["user"]["email"]
                        st.session_state.user_id = res["user"]["id"]
                        profile = get_profile(res["user"]["id"])
                        st.session_state.user_role = profile.get("role", "candidate")
                        st.session_state.page = "dashboard"
                        st.rerun()
                else:
                    st.warning("Please enter email and password")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create an account", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()


def show_register():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<h1 style='text-align:center; font-size:2.5rem; font-weight:700; "
            "background:linear-gradient(135deg,#818cf8,#6366f1); -webkit-background-clip:text; "
            "-webkit-text-fill-color:transparent;'>HireAI</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#71717a; margin-bottom:32px;'>Create your account</p>",
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown("##### Register")
            col_a, col_b = st.columns(2)
            with col_a:
                name = st.text_input("Full Name", key="reg_name", placeholder="John Doe")
                email = st.text_input("Email", key="reg_email", placeholder="you@example.com")
            with col_b:
                password = st.text_input("Password", type="password", key="reg_pass", placeholder="Min 6 characters")
                role = st.selectbox("Role", ["hr", "candidate"], key="reg_role")

            if st.button("Register", use_container_width=True, type="primary"):
                if name and email and password:
                    if len(password) < 6:
                        st.warning("Password must be at least 6 characters")
                    else:
                        with st.spinner("Creating account..."):
                            res, err = sign_up(email, password, name, role)
                        if err:
                            st.error(err)
                        else:
                            st.success("✅ Account created! Please sign in.")
                            st.session_state.page = "login"
                            st.rerun()
                else:
                    st.warning("Please fill all fields")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Already have an account? Sign In", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()


# ── Main App (authenticated) ──────────────────────────────────────

def main_app():
    # Hide native Streamlit sidebar nav links (from pages/ folder)
    st.markdown(
        "<style>[data-testid='stSidebarNav'] {display: none;}</style>",
        unsafe_allow_html=True,
    )

    # Top bar
    status_icon = "🔒" if is_supabase_available() else "⚡"
    status_text = "Supabase" if is_supabase_available() else "Local Auth"
    st.markdown(
        f'<div style="padding:8px 0 16px 0;border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:8px;'
        f'display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="font-size:20px;font-weight:700;background:linear-gradient(135deg,#818cf8,#6366f1);'
        f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;">HireAI</span>'
        f'<span style="color:#52525b;font-size:11px;">{status_icon} {status_text} | {st.session_state.user_email} | <span style="color:#818cf8;">{st.session_state.get("user_role", "candidate").upper()}</span></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Sidebar
    st.sidebar.markdown(
        f'<div style="padding:8px 0 16px 0;border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:8px;">'
        f'<span style="font-size:16px;font-weight:700;color:#fff;">HireAI</span><br>'
        f'<span style="color:#52525b;font-size:11px;">{st.session_state.user_email}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    role = st.session_state.get("user_role", "candidate")
    role_label = "HR Dashboard" if role == "hr" else "Candidate Dashboard"

    hr_pages = {
        "📊 Dashboard": "dashboard",
        "👤 Candidates": "candidates",
        "📄 Upload Resume": "upload",
        "💼 Jobs": "jobs",
        "🎯 Interviews": "interviews",
        "🤖 AI Interview": "interview_bot",
        "🏆 Ranking": "ranking",
        "📋 Offers": "offers",
    }

    candidate_pages = {
        f"📊 {role_label}": "dashboard",
        "📄 My Resume": "upload",
        "🤖 AI Interview": "interview_bot",
    }

    pages = hr_pages if role == "hr" else candidate_pages

    for label, key in pages.items():
        active = st.session_state.page == key
        if st.sidebar.button(label, use_container_width=True, type="primary" if active else "secondary", key=f"nav_{key}"):
            st.session_state.page = key
            st.rerun()

    st.sidebar.markdown(
        f'<div style="color:#52525b;font-size:11px;margin:4px 0;">Role: {role.upper()}</div>',
        unsafe_allow_html=True,
    )

    ml_status = ml_available()
    if ml_status:
        st.sidebar.markdown(
            '<div style="color:#22c55e;font-size:11px;margin:4px 0;">\U0001f916 ML Models: Active</div>',
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            '<div style="color:#a1a1aa;font-size:11px;margin:4px 0;">\U0001f916 ML Models: run train_all.py</div>',
            unsafe_allow_html=True,
        )

    st.sidebar.divider()
    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        sign_out(st.session_state.access_token)
        for k in ["access_token", "user_email", "user_id", "user_name", "user_role"]:
            st.session_state[k] = None
        st.session_state.page = "login"
        st.rerun()

    # Route pages — force reload to avoid stale cache
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
    mod = importlib.import_module(mod_path)
    importlib.reload(mod)
    mod.show()


# ── Router ─────────────────────────────────────────────────────────

if not st.session_state.access_token:
    st.markdown(
        "<style>[data-testid='stSidebar'] {display: none;} [data-testid='stSidebarCollapseButton'] {display: none;}</style>",
        unsafe_allow_html=True,
    )
    page = st.session_state.page
    if page == "register":
        show_register()
    else:
        show_login()
else:
    main_app()
