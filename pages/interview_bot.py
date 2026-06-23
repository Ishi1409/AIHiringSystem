import streamlit as st
import random
import pandas as pd
from services.supabase_client import save_chat_message


QUESTIONS = {
    "technical": [
        "Explain the difference between REST and GraphQL.",
        "What is the time complexity of binary search?",
        "How does garbage collection work in Python?",
        "Explain Docker and its benefits.",
        "What is the CAP theorem?",
        "How would you design a URL shortening service?",
    ],
    "behavioral": [
        "Tell me about a time you dealt with a difficult team member.",
        "Describe a project you led from start to finish.",
        "How do you handle tight deadlines?",
        "Tell me about a time you failed and what you learned.",
    ],
    "hr": [
        "Why do you want to work here?",
        "Where do you see yourself in 5 years?",
        "What are your greatest strengths?",
        "Why should we hire you?",
    ],
    "coding": [
        "Write a function to find the longest palindrome substring.",
        "Implement a binary search tree with insert and search.",
        "Write a function to check if two strings are anagrams.",
    ],
}


def _analyze(text):
    wc = len(text.split())
    positive = {"happy", "excited", "confident", "great", "excellent", "love", "good", "best", "amazing", "passionate"}
    negative = {"sad", "angry", "frustrated", "bad", "worst", "terrible", "hate", "nervous", "anxious"}
    words = text.lower().split()
    pos = sum(1 for w in words if w in positive)
    neg = sum(1 for w in words if w in negative)
    sentiment = round((pos - neg) / max(len(words), 1) * 10, 2)
    keywords = [w for w in words if len(w) > 5][:5]
    return wc, sentiment, keywords


def show():
    col1, col2 = st.columns([1, 5])
    with col1: st.markdown("# 🤖")
    with col2: st.markdown("# AI Interview Practice"); st.caption("Practice your interview skills with real-time AI feedback")

    st.divider()

    if "bot_questions" not in st.session_state:
        st.session_state.bot_questions = []
        st.session_state.bot_idx = 0
        st.session_state.bot_msgs = []
        st.session_state.bot_done = False

    chat_col, analysis_col = st.columns([2, 1])

    with chat_col:
        if not st.session_state.bot_questions:
            with st.container(border=True):
                st.markdown("##### 🎯 Start a Practice Interview")
                st.markdown("Choose an interview type and begin your session.")
                q_type = st.selectbox(
                    "Interview Type",
                    list(QUESTIONS.keys()),
                    format_func=lambda x: {"technical": "💻 Technical", "behavioral": "👥 Behavioral", "hr": "📋 HR", "coding": "⚙️ Coding"}.get(x, x),
                    key="bot_type_start",
                )
                desc = {
                    "technical": "System design, algorithms, technical concepts",
                    "behavioral": "Soft skills, teamwork, conflict resolution",
                    "hr": "Career goals, motivation, culture fit",
                    "coding": "Data structures, algorithms, problem solving",
                }
                st.caption(desc.get(q_type, ""))
                if st.button("🚀 Start Interview", type="primary", use_container_width=True):
                    questions = random.sample(QUESTIONS[q_type], min(4, len(QUESTIONS[q_type])))
                    st.session_state.bot_questions = questions
                    st.session_state.bot_idx = 0
                    st.session_state.bot_msgs = [{"role": "assistant", "content": f"Welcome! Let's begin with a **{q_type}** interview.\n\n**Q1:** {questions[0]}\n\n👉 Type your answer below!"}]
                    st.session_state.bot_done = False
                    st.session_state.bot_type = q_type
                    st.rerun()
        else:
            # Chat messages
            for msg in st.session_state.bot_msgs:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if not st.session_state.bot_done:
                answer = st.chat_input("✏️ Type your answer here...")
                if answer:
                    st.session_state.bot_msgs.append({"role": "user", "content": answer})
                    save_chat_message(st.session_state.bot_type, "user", answer)

                    idx = st.session_state.bot_idx + 1
                    total = len(st.session_state.bot_questions)
                    if idx < total:
                        feedback = random.choice([
                            "Great answer! Let's move to the next one.",
                            "Thanks for that insight. Here's another question:",
                            "Interesting perspective! Next question:",
                            "Good response. Let's continue:",
                        ])
                        st.session_state.bot_msgs.append({
                            "role": "assistant",
                            "content": f"{feedback}\n\n**Q{idx+1}/{total}:** {st.session_state.bot_questions[idx]}"
                        })
                        st.session_state.bot_idx = idx
                    else:
                        st.session_state.bot_msgs.append({
                            "role": "assistant",
                            "content": "🎉 **Interview Complete!**\n\nYou've answered all questions. Check your performance analysis on the right."
                        })
                        st.session_state.bot_done = True
                    st.rerun()
            else:
                if st.button("🔄 Start New Session", type="primary", use_container_width=True):
                    st.session_state.bot_questions = []
                    st.session_state.bot_msgs = []
                    st.rerun()

    with analysis_col:
        with st.container(border=True):
            st.markdown("##### 📊 Live Analysis")
            user_msgs = [m for m in st.session_state.bot_msgs if m["role"] == "user"]
            if user_msgs:
                last = user_msgs[-1]["content"]
                wc, sentiment, keywords = _analyze(last)

                st.metric("Response Length", f"{wc} words", help="Number of words in your last answer")
                st.progress(min(wc / 30, 1.0), text="Depth")

                sent_color = "🟢" if sentiment > 0.5 else "🔴" if sentiment < -0.5 else "🟡"
                st.metric("Sentiment", f"{sent_color} {sentiment:.2f}", help="Positive score = confident tone")

                if keywords:
                    st.markdown("**Key terms detected:**")
                    st.write(" ".join(f"`{k}`" for k in keywords))

                total = len(st.session_state.bot_questions)
                done = st.session_state.bot_idx
                if total:
                    st.markdown("**Progress**")
                    st.progress(done / total, text=f"{done}/{total} questions")
            else:
                st.info("💬 Start answering questions to see live analysis here")
