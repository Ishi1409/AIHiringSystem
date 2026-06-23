import streamlit as st
import pandas as pd
from services.supabase_client import create_offer, list_offers, list_candidates, list_jobs


def show():
    col1, col2 = st.columns([1, 5])
    with col1: st.markdown("# 📋")
    with col2: st.markdown("# Offer Management"); st.caption("Create, track, and manage job offers for selected candidates")

    st.divider()

    candidates = {c["id"]: c["name"] for c in list_candidates()}
    jobs = {j["id"]: j["title"] for j in list_jobs()}

    create_tab, browse_tab = st.tabs(["✉️ New Offer", "📋 All Offers"])

    with create_tab:
        if not candidates or not jobs:
            st.warning("⚠️ Need both candidates and jobs before creating offers.")
        else:
            with st.container(border=True):
                st.markdown("##### Offer Details")
                col1, col2 = st.columns(2)
                with col1:
                    cand_ids = list(candidates.keys())
                    selected_cand = st.selectbox(
                        "Candidate *", cand_ids,
                        format_func=lambda x: f"{candidates.get(x, x)} ({x})",
                        key="of_cand",
                    )
                    salary = st.number_input("Annual Salary ($) *", min_value=0, value=80000, step=10000, format="%d")
                with col2:
                    job_ids = list(jobs.keys())
                    selected_job = st.selectbox(
                        "Job *", job_ids,
                        format_func=lambda x: f"{jobs.get(x, x)} ({x})",
                        key="of_job",
                    )
                    benefits = st.text_input("Benefits", placeholder="e.g. Health insurance, 401k matching, remote work")

                if st.button("✉️ Send Offer", use_container_width=True, type="primary"):
                    if selected_cand and selected_job and salary > 0:
                        create_offer(str(selected_cand), str(selected_job), salary, benefits)
                        st.toast(f"✅ Offer sent to {candidates.get(selected_cand, 'candidate')}!", icon="🎉")
                        st.rerun()
                    else:
                        st.error("Please fill all required fields")

    with browse_tab:
        offers = list_offers()
        if not offers:
            st.info("📭 No offers created yet")
        else:
            rows = []
            for o in offers:
                status = o.get("status", "pending").title()
                status_emoji = {"Pending": "⏳", "Accepted": "✅", "Rejected": "❌", "Expired": "⌛"}.get(status, "⚪")
                rows.append({
                    "Candidate": candidates.get(o.get("candidate_id", ""), "-"),
                    "Job": jobs.get(o.get("job_id", ""), "-"),
                    "Salary": f"${o.get('salary_offered', 0):,}",
                    "Sent": o.get("sent_date", "-")[:10],
                    "Status": f"{status_emoji} {status}",
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True, column_config={
                "Salary": st.column_config.TextColumn("Salary", help="Annual salary offered"),
            })

            # Summary metrics
            st.divider()
            st.markdown("##### 📊 Offer Summary")
            mc1, mc2, mc3, mc4 = st.columns(4)
            total = len(offers)
            pending = sum(1 for o in offers if o.get("status") == "pending")
            accepted = sum(1 for o in offers if o.get("status") == "accepted")
            rejected = sum(1 for o in offers if o.get("status") == "rejected")
            with mc1: st.metric("📋 Total Offers", total)
            with mc2: st.metric("⏳ Pending", pending)
            with mc3: st.metric("✅ Accepted", accepted)
            with mc4: st.metric("❌ Rejected", rejected)
