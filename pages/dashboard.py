import streamlit as st
import pandas as pd
from services.supabase_client import get_dashboard


def show():
    data = get_dashboard()

    col1, col2 = st.columns([1, 5])
    with col1: st.markdown("# 📊")
    with col2: st.markdown("# HR Dashboard"); st.caption("AI-powered recruitment analytics at a glance")

    st.divider()

    # ── KPI Metrics ──
    st.markdown("### Key Metrics")
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.metric("👤 Candidates", data.get("total_candidates", 0), "+10% vs last month", help="Total registered candidates")
    with k2: st.metric("📄 Resumes", data.get("total_resumes", 0), "+5%", help="Uploaded and parsed resumes")
    with k3: st.metric("💼 Open Jobs", data.get("total_jobs", 0), "", help="Active job postings")
    with k4: st.metric("🎯 Interviews", data.get("total_interviews", 0), "+20%", help="Scheduled interviews")
    with k5: st.metric(
        "📋 Offers",
        f'{data.get("accepted_offers", 0)}/{data.get("total_offers", 0)}',
        f'{data.get("accepted_offers", 0)/max(data.get("total_offers", 1),1)*100:.0f}% acceptance',
        help="Accepted / Total offers",
    )

    st.divider()

    # ── Two column layout ──
    left, right = st.columns([3, 2])

    with left:
        # Top candidates table
        top = data.get("top_candidates", [])
        if top:
            st.markdown("### 🏆 Top Ranked Candidates")
            df = pd.DataFrame(top)
            cols = [c for c in ["rank", "name", "match_percentage", "experience_years", "rank_score"] if c in df.columns]
            if cols:
                df = df[cols].head(5)
                df.columns = [c.replace("_", " ").title() for c in df.columns]
                df["Match %"] = df["Match %"].apply(lambda x: f"{x:.1f}%")
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No candidates ranked yet — upload resumes and create jobs to see rankings.")

    with right:
        # Hiring funnel
        funnel = data.get("status_funnel", {})
        if funnel:
            st.markdown("### 📈 Hiring Funnel")
            for stage, count in funnel.items():
                c1, c2 = st.columns([1, 4])
                with c1:
                    color = {"new": "#818cf8", "screened": "#6366f1", "interviewed": "#fbbf24", "offered": "#34d399", "hired": "#10b981"}
                    st.markdown(f":{color.get(stage, '#71717a')}[**{count}**]")
                with c2:
                    st.progress(min(count / max(list(funnel.values()) + [1], default=1), 1.0), text=stage.replace("_", " ").title())

    st.divider()

    # ── Skill Gaps ──
    gaps = data.get("skill_gaps", [])
    if gaps:
        st.markdown("### 🧠 Skill Gap Analysis")
        df = pd.DataFrame(gaps[:10])
        if "pct" in df.columns:
            df["Bar"] = df["pct"].apply(lambda x: "█" * max(1, int(x / 5)))
        st.dataframe(df, use_container_width=True, hide_index=True, column_config={
            "skill": st.column_config.TextColumn("Skill", help="Skill name"),
            "count": st.column_config.NumberColumn("Count", help="Number of candidates with this skill"),
            "pct": st.column_config.ProgressColumn("% of Candidates", format="%.1f%%", min_value=0, max_value=100),
        })

    # ── Education Distribution ──
    edu = data.get("education_distribution", [])
    if edu:
        st.divider()
        st.markdown("### 🎓 Education Distribution")
        edu_cols = st.columns(len(edu))
        for i, e in enumerate(edu):
            with edu_cols[i]:
                st.metric(e.get("level", "Other"), e.get("count", 0))
