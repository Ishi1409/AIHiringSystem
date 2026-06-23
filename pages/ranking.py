import streamlit as st
import pandas as pd
from services.supabase_client import list_jobs, match_candidates_for_job


def show():
    col1, col2 = st.columns([1, 5])
    with col1: st.markdown("# 🏆")
    with col2: st.markdown("# Candidate Ranking"); st.caption("AI-powered candidate-job matching using skill analysis and scoring")

    st.divider()

    jobs = list_jobs()
    if not jobs:
        st.warning("📭 No jobs available. Create a job posting first to rank candidates against it.")
        return

    job_options = {j["id"]: j["title"] for j in jobs}
    selected = st.selectbox(
        "🎯 Select a job to rank candidates against",
        list(job_options.keys()),
        format_func=lambda x: job_options.get(x, x),
    )

    if st.button("🔍 Find & Rank Candidates", use_container_width=True, type="primary"):
        with st.spinner("🤖 AI is analyzing and ranking candidates..."):
            rankings = match_candidates_for_job(selected)
            st.session_state["rankings_result"] = rankings
            st.session_state["ranked_job"] = job_options.get(selected, selected)
        st.rerun()

    rankings = st.session_state.get("rankings_result")

    if rankings is None:
        with st.container(border=True):
            st.markdown("##### How it works")
            st.markdown("""
            1. **Select a job** from the dropdown above
            2. Click **Find & Rank Candidates** to run the AI matching engine
            3. View candidates ranked by **skill match %**, **experience**, and **overall score**
            """)
        return

    if not rankings:
        st.warning("😕 No candidates matched. Upload resumes or register candidates first.")
        return

    st.markdown(f"### Results for: {st.session_state.get('ranked_job', 'Job')}")

    # Show top 3 with highlight
    for i, c in enumerate(rankings[:3]):
        pct = c.get("match_percentage", 0)
        emoji = ["🥇", "🥈", "🥉"][i]
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 3, 1])
            with c1:
                st.markdown(f"# {emoji}")
            with c2:
                st.markdown(f"**{c.get('name', 'Unknown')}**")
                st.caption(f"Score: {c.get('rank_score', 0):.1f}")
            with c3:
                color = "green" if pct >= 70 else "orange" if pct >= 40 else "red"
                st.markdown(f":{color}[**{pct:.1f}%**] match")
            st.progress(pct / 100, text="Skill Match")

    # Full table
    st.divider()
    st.markdown("### Full Rankings")
    df = pd.DataFrame(rankings)
    keep = [c for c in ["rank", "name", "match_percentage", "matched_skills", "rank_score"] if c in df.columns]
    if keep:
        df = df[keep]
        st.dataframe(df, use_container_width=True, hide_index=True, column_config={
            "match_percentage": st.column_config.ProgressColumn("Match %", format="%.1f%%", min_value=0, max_value=100),
            "rank_score": st.column_config.NumberColumn("Rank Score", format="%.1f"),
            "matched_skills": st.column_config.ListColumn("Matched Skills"),
        })
