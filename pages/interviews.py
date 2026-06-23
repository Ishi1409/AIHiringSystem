import streamlit as st
import pandas as pd
from services.supabase_client import create_interview, list_interviews, list_candidates, list_jobs


def show():
    col1, col2 = st.columns([1, 5])
    with col1: st.markdown("# 🎯")
    with col2: st.markdown("# Interview Scheduler"); st.caption("Schedule interviews and track candidate progress")

    st.divider()

    candidates = {c["id"]: c["name"] for c in list_candidates()}
    jobs = {j["id"]: j["title"] for j in list_jobs()}

    sched, list_tab = st.tabs(["➕ Schedule Interview", "📋 All Interviews"])

    with sched:
        with st.container(border=True):
            st.markdown("##### Interview Details")
            col1, col2 = st.columns(2)
            with col1:
                cand_ids = list(candidates.keys())
                selected_cand = st.selectbox(
                    "Candidate *", cand_ids,
                    format_func=lambda x: f"{candidates.get(x, x)} ({x})",
                    key="iv_cand",
                )
                iv_type = st.selectbox(
                    "Interview Type",
                    ["technical", "behavioral", "hr", "coding"],
                    format_func=lambda x: x.title(),
                )
            with col2:
                job_ids = list(jobs.keys())
                selected_job = st.selectbox(
                    "Job *", job_ids,
                    format_func=lambda x: f"{jobs.get(x, x)} ({x})",
                    key="iv_job",
                )
                iv_date = st.date_input("Scheduled Date")

            if st.button("✅ Schedule Interview", use_container_width=True, type="primary"):
                if selected_cand and selected_job:
                    create_interview(str(selected_cand), str(selected_job), iv_type, str(iv_date))
                    st.toast("✅ Interview scheduled!", icon="🎯")
                    st.rerun()
                else:
                    st.error("Select both a candidate and a job")

    with list_tab:
        interviews = list_interviews()
        if not interviews:
            st.info("📭 No interviews scheduled yet")
        else:
            rows = []
            for iv in interviews:
                status = iv.get("status", "scheduled").title()
                status_emoji = {"Scheduled": "🔵", "Completed": "🟢", "Cancelled": "🔴", "In Progress": "🟡"}.get(status, "⚪")
                rows.append({
                    "Candidate": candidates.get(iv.get("candidate_id", ""), "-"),
                    "Job": jobs.get(iv.get("job_id", ""), "-"),
                    "Type": iv.get("interview_type", "technical").title(),
                    "Date": iv.get("scheduled_date", "-")[:10],
                    "Status": f"{status_emoji} {status}",
                    "Sentiment": iv.get("sentiment_score", "-"),
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True, column_config={
                "Sentiment": st.column_config.NumberColumn("Sentiment", format="%.2f" if df["Sentiment"].dtype in [float, int] else None),
            })
