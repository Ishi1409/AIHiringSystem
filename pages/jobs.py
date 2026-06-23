import streamlit as st
import pandas as pd
from services.supabase_client import list_jobs, create_job, match_candidates_for_job


def show():
    col1, col2 = st.columns([1, 5])
    with col1: st.markdown("# 💼")
    with col2: st.markdown("# Jobs"); st.caption("Create job postings and find the best matching candidates")

    st.divider()

    create_tab, browse_tab = st.tabs(["➕ New Job Posting", "📋 All Job Postings"])

    with create_tab:
        with st.container(border=True):
            st.markdown("##### Job Details")
            title = st.text_input("Job Title *", placeholder="e.g. Senior Frontend Engineer")
            description = st.text_area("Job Description", placeholder="Describe the role, responsibilities, and team...", height=120)

            col1, col2 = st.columns(2)
            with col1:
                skills_input = st.text_input("Required Skills * (comma separated)", placeholder="e.g. Python, React, SQL, AWS")
            with col2:
                exp = st.number_input("Experience Required (years)", min_value=0, value=0)

            if st.button("✅ Create Job Posting", use_container_width=True, type="primary"):
                if title and skills_input:
                    skills = [s.strip() for s in skills_input.split(",") if s.strip()]
                    create_job(title, description, skills, int(exp))
                    st.toast(f"✅ Job '{title}' created!", icon="🎉")
                    st.rerun()
                else:
                    st.error("Title and skills are required")

    with browse_tab:
        jobs = list_jobs()
        if not jobs:
            st.info("📭 No jobs created yet — create one in the other tab.")
        else:
            for job in jobs:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"##### {job.get('title', 'Untitled')}")
                        if job.get("description"):
                            st.caption(job["description"])
                    with c2:
                        btn = st.button(
                            "🎯 Find Matches" if not st.session_state.get(f"match_done_{job['id']}") else "🔄 Re-match",
                            key=f"match_{job['id']}",
                            use_container_width=True,
                            type="primary",
                        )
                        if btn:
                            with st.spinner("🤖 AI matching candidates..."):
                                rankings = match_candidates_for_job(job["id"])
                                st.session_state[f"rankings_{job['id']}"] = rankings
                                st.session_state[f"match_done_{job['id']}"] = True
                            st.rerun()

                    # Skills chips
                    skills = job.get("skills", [])
                    if skills:
                        st.markdown(" ".join(f"`{s}`" for s in skills))
                    st.caption(f"📅 Experience: {job.get('experience_required', 0)} yrs | Status: {job.get('status', 'open')}")

                    # Show rankings inline
                    rankings = st.session_state.get(f"rankings_{job['id']}")
                    if rankings:
                        st.divider()
                        st.markdown("##### 🏆 Candidate Rankings")
                        df = pd.DataFrame(rankings)
                        keep = [c for c in ["rank", "name", "match_percentage", "rank_score"] if c in df.columns]
                        if keep:
                            df = df[keep]
                            st.dataframe(df, use_container_width=True, hide_index=True, column_config={
                                "match_percentage": st.column_config.ProgressColumn("Match %", format="%.1f%%", min_value=0, max_value=100),
                                "rank_score": st.column_config.NumberColumn("Rank Score", format="%.1f"),
                            })
