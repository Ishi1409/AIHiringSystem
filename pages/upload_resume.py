import streamlit as st
import pandas as pd
from services.supabase_client import upload_resume, list_resumes


def show():
    col1, col2 = st.columns([1, 5])
    with col1: st.markdown("# 📄")
    with col2: st.markdown("# Resume Upload"); st.caption("Upload, parse, and extract skills from resumes using AI")

    st.divider()

    upload_tab, history_tab = st.tabs(["📤 Upload & Parse", "📁 Upload History"])

    with upload_tab:
        col_a, col_b = st.columns([2, 1])

        with col_a:
            uploaded_file = st.file_uploader(
                "Drop your resume here",
                type=["pdf", "docx", "txt"],
                help="Supports PDF, DOCX, and TXT files",
            )

            if uploaded_file:
                file_details = {
                    "Filename": uploaded_file.name,
                    "File size": f"{uploaded_file.size / 1024:.1f} KB",
                    "File type": uploaded_file.type or "Unknown",
                }
                st.code("\n".join(f"{k}: {v}" for k, v in file_details.items()))

                if st.button("🚀 Upload & Parse with AI", use_container_width=True, type="primary"):
                    with st.spinner("🤖 AI is parsing your resume..."):
                        user_id = st.session_state.get("user_id", "local-user")
                        result = upload_resume(user_id, uploaded_file)
                    if result:
                        st.session_state["last_parse"] = result
                        st.balloons()
                        st.rerun()

        with col_b:
            last = st.session_state.get("last_parse")
            if last:
                st.markdown("##### ✅ Parsed Result")
                with st.container(border=True):
                    st.markdown(f"**Name:** {last.get('name', '-')}")
                    st.markdown(f"**Email:** {last.get('email', '-')}")
                    st.markdown(f"**Phone:** {last.get('phone', '—')}")
                    if last.get("skills"):
                        st.markdown("**Skills:** " + " ".join(f"`{s}`" for s in last["skills"]))
                    else:
                        st.markdown("*No skills detected*")
            else:
                st.info("Upload a resume to see parsed results here")

    with history_tab:
        resumes = list_resumes()
        if not resumes:
            st.info("📭 No resumes uploaded yet")
        else:
            df = pd.DataFrame(resumes)
            cols = [c for c in ["parsed_name", "filename", "skills"] if c in df.columns]
            if cols:
                df = df[cols]
                df.columns = ["Name", "File", "Skills"]
                df["Skills"] = df["Skills"].apply(lambda x: ", ".join(x[:4]) if x else "-")
                st.dataframe(df, use_container_width=True, hide_index=True)
