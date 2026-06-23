import streamlit as st
import pandas as pd
from services.supabase_client import create_candidate, list_candidates, list_resumes


def show():
    col1, col2 = st.columns([1, 5])
    with col1: st.markdown("# 👤")
    with col2: st.markdown("# Candidate Registry"); st.caption("Register, track, and manage all candidates")

    st.divider()

    reg, browse = st.tabs(["➕ Register New Candidate", "📋 Browse Candidates"])

    with reg:
        with st.container(border=True):
            st.markdown("##### Candidate Details")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *", key="cand_name", placeholder="e.g. John Doe")
                email = st.text_input("Email *", key="cand_email", placeholder="e.g. john@example.com")
            with col2:
                phone = st.text_input("Phone", key="cand_phone", placeholder="e.g. +1 234 567 890")
                skills_input = st.text_input("Skills (comma separated)", key="cand_skills", placeholder="e.g. Python, React, SQL")

            if st.button("✅ Register Candidate", use_container_width=True, type="primary"):
                if name and email:
                    skills = [s.strip() for s in skills_input.split(",") if s.strip()]
                    create_candidate(name, email, phone, skills)
                    st.toast(f"✅ {name} registered successfully!", icon="🎉")
                    st.rerun()
                else:
                    st.error("Name and email are required")

    with browse:
        candidates = list_candidates()
        resumes = list_resumes()
        all_people = candidates + [
            {
                "name": r.get("parsed_name", "Unknown"),
                "email": r.get("parsed_email", ""),
                "skills": ", ".join(r.get("skills", [])[:5]),
                "source": "📄 Resume Upload",
            }
            for r in resumes
        ]

        if not all_people:
            st.info("🌱 No candidates yet — add one in the Register tab or upload a resume.")
        else:
            st.markdown(f"**{len(all_people)}** total candidates")
            df = pd.DataFrame(all_people)
            st.dataframe(df, use_container_width=True, hide_index=True)
