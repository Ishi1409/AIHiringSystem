import streamlit as st
import pandas as pd
from services.supabase_client import get_dashboard, list_resumes, list_interviews


def show():
    role = st.session_state.get("user_role", "candidate")
    user_id = st.session_state.get("user_id")
    data = get_dashboard()

    col1, col2 = st.columns([1, 5])
    if role == "hr":
        with col1: st.markdown("# 📊")
        with col2: st.markdown("# HR Dashboard"); st.caption("AI-powered recruitment analytics at a glance")
        try:
            _show_hr_dashboard(data)
        except Exception:
            st.warning("⚠️ Dashboard data unavailable. Upload resumes or create jobs to see analytics.")
    else:
        with col1: st.markdown("# 👤")
        with col2: st.markdown("# My Dashboard"); st.caption("Track your applications and interviews")
        _show_candidate_dashboard(user_id)


def _show_hr_dashboard(data):
    st.divider()

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.metric("👤 Candidates", data.get("total_candidates", 0), help="Total registered candidates")
    with k2: st.metric("📄 Resumes", data.get("total_resumes", 0), help="Uploaded and parsed resumes")
    with k3: st.metric("💼 Open Jobs", data.get("total_jobs", 0), help="Active job postings")
    with k4: st.metric("🎯 Interviews", data.get("total_interviews", 0), help="Scheduled interviews")
    with k5: st.metric("📋 Offers", data.get("total_offers", 0), help="Total offers sent")

    st.divider()

    left, right = st.columns([3, 2])

    with left:
        top = data.get("top_candidates", [])
        if top:
            st.markdown("### 🏆 Top Ranked Candidates")
            df = pd.DataFrame(top)
            keep = [c for c in ["rank", "name", "match_percentage", "experience_years", "rank_score"] if c in df.columns]
            if keep:
                df = df[keep].head(5)
                st.dataframe(df, use_container_width=True, hide_index=True, column_config={
                    "match_percentage": st.column_config.ProgressColumn("Match %", format="%.1f%%", min_value=0, max_value=100),
                    "rank_score": st.column_config.NumberColumn("Rank Score", format="%.1f"),
                })
        else:
            st.info("No candidates ranked yet — upload resumes and create jobs to see rankings.")

    with right:
        funnel = data.get("status_funnel", {})
        if funnel:
            st.markdown("### 📈 Hiring Funnel")
            for stage, count in funnel.items():
                c1, c2 = st.columns([1, 4])
                with c1:
                    st.markdown(f":{'#818cf8' if True else ''}[**{count}**]")
                with c2:
                    st.progress(min(count / max(list(funnel.values()) + [1], default=1), 1.0), text=stage.replace("_", " ").title())

    st.divider()

    gaps = data.get("skill_gaps", [])
    if gaps:
        st.markdown("### 🧠 Skill Gap Analysis")
        df = pd.DataFrame(gaps[:10])
        if "pct" in df.columns:
            df["Bar"] = df["pct"].apply(lambda x: "█" * max(1, int(x / 5)))
        st.dataframe(df, use_container_width=True, hide_index=True, column_config={
            "skill": st.column_config.TextColumn("Skill"),
            "count": st.column_config.NumberColumn("Count"),
            "pct": st.column_config.ProgressColumn("% of Candidates", format="%.1f%%", min_value=0, max_value=100),
        })

    edu = data.get("education_distribution", [])
    if edu:
        st.divider()
        st.markdown("### 🎓 Education Distribution")
        edu_cols = st.columns(len(edu))
        for i, e in enumerate(edu):
            with edu_cols[i]:
                st.metric(e.get("level", "Other"), e.get("count", 0))


def _show_candidate_dashboard(user_id):
    resumes = list_resumes(user_id)
    interviews = list_interviews()

    k1, k2, k3 = st.columns(3)
    with k1: st.metric("📄 My Resumes", len(resumes))
    with k2: st.metric("🎯 My Interviews", len([iv for iv in interviews if iv.get("candidate_id") == user_id]))
    with k3: st.metric("📊 Profile Completeness", "80%" if resumes else "0%")

    st.divider()

    st.markdown("### 📄 My Resumes")
    if resumes:
        for r in resumes:
            with st.container(border=True):
                st.markdown(f"**{r.get('parsed_name', 'Resume')}** — {r.get('filename', '')}")
                skills = r.get("skills", [])
                if skills:
                    st.markdown(" ".join(f"`{s}`" for s in skills[:8]))
                st.caption(f"Uploaded: {r.get('created_at', '')[:10]}")
    else:
        st.info("📭 No resume uploaded yet — go to **My Resume** to upload one.")

    my_interviews = [iv for iv in interviews if iv.get("candidate_id") == user_id]
    st.divider()
    st.markdown("### 🎯 My Interviews")
    if my_interviews:
        for iv in my_interviews:
            status = iv.get("status", "scheduled").title()
            with st.container(border=True):
                st.markdown(f"**{iv.get('interview_type', 'interview').title()}** — `{status}`")
                st.caption(f"Scheduled: {iv.get('scheduled_date', '')[:10]}")
                if iv.get("feedback"):
                    st.markdown(f"*Feedback:* {iv['feedback']}")
    else:
        st.info("📭 No interviews scheduled yet.")
