import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Rationality I", page_icon="💬")
st.title("💬 ProfessorBot - Rationality I")

with st.expander("📘 About ProfessorBot (Please read before starting)"):
    st.markdown(
        """
Welcome to **ProfessorBot – Rationality I**.

ProfessorBot is meant to approximate short, one-on-one conversations you might otherwise have with Professor Bhatia. 
The goal is twofold. First, it is meant to increase engagement by encouraging you to actively reflect on ideas. 
Second, it helps surface how students in the class are thinking about the course material, which will inform subsequent lectures 
and in-class discussion.

This conversation should take only a few minutes to complete. When complete, ProfessorBot will give you the approval 
to download the transcript and submit to Canvas.

**Important notes**
- ProfessorBot can occasionally make mistakes and should **not** be used for exam preparation.
- ProfessorBot is based on OpenAI’s GPT model.
- Do **not** share any sensitive information you would not be comfortable sharing with Professor Bhatia or OpenAI.
"""
    )


# ---------- Config ----------
# You can update these weekly in the sidebar (or hardcode based on Week #)
DEFAULT_WEEK_CONCEPTS = [
    "Concept 1 (type it here)",
    "Concept 2 (type it here)"
]

# ---------- Session State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "stage" not in st.session_state:
    st.session_state.stage = "A"  # A: define decision, B: concepts, C: analysis, D: integrate+wrap

if "concept1" not in st.session_state:
    st.session_state.concept1 = ""

if "concept2" not in st.session_state:
    st.session_state.concept2 = ""

if "decision_summary" not in st.session_state:
    st.session_state.decision_summary = ""

if "analysis_c1" not in st.session_state:
    st.session_state.analysis_c1 = ""

if "analysis_c2" not in st.session_state:
    st.session_state.analysis_c2 = ""

if "integration" not in st.session_state:
    st.session_state.integration = ""

if "takeaways" not in st.session_state:
    st.session_state.takeaways = ""


# ---------- Sidebar (optional, still "single chatbot" UI) ----------
with st.sidebar:
    st.header("Weekly setup")
    st.session_state.concept1 = st.text_input("Concept 1", st.session_state.concept1, placeholder=DEFAULT_WEEK_CONCEPTS[0])
    st.session_state.concept2 = st.text_input("Concept 2", st.session_state.concept2, placeholder=DEFAULT_WEEK_CONCEPTS[1])
    st.markdown("---")
    st.write("Progress stage:", f"**{st.session_state.stage}**")
    if st.button("Reset conversation"):
        for k in list(st.session_state.keys()):
            if k != "concept1" and k != "concept2":
                del st.session_state[k]
        st.rerun()

# ---------- Helper: system prompt ----------
SYSTEM_PROMPT = f"""
You are a weekly reflection coach for a psychology course called "Choice".
Goal: guide the student to explore ONE real decision and analyze it using TWO psychology concepts learned this week.

Rules:
- Do NOT invent details for the student.
- Ask short, specific questions. Advance ONE step at a time.
- Always follow the 4-stage flow:
  A) Clarify the decision, options, context, final choice, and outcome.
  B) Confirm the two concepts (ask student to define each in their own words; gently correct misuse).
  C) Analyze the decision with Concept 1, then Concept 2 (each: mechanism/variables + 2 evidence details + counterfactual).
  D) Integrate the two concepts (complement/conflict/causal chain) + actionable takeaways.
- At the end, produce a clean summary the student can submit.

This week’s concepts (student must use both):
Concept 1: {st.session_state.concept1 or "[Not provided yet]"}
Concept 2: {st.session_state.concept2 or "[Not provided yet]"}
"""

def call_llm(messages):
    api_key = st.secrets.get("OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ Missing OPENAI_API_KEY. Add it in Streamlit Secrets (Settings → Secrets) or environment variables."
    client = OpenAI(api_key=api_key)

    # Use a reliable chat model available to your account
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.4,
    )
    return resp.choices[0].message.content


# ---------- Stage routing (simple but effective) ----------
def stage_instruction(stage):
    if stage == "A":
        return ("Stage A (Decision definition): Ask for (1) the decision, (2) at least two options, "
                "(3) what they chose, (4) outcome/feelings. Then restate decision in 2–3 sentences and confirm.")
    if stage == "B":
        return ("Stage B (Concept binding): Ask student to define Concept 1 and Concept 2 in one sentence each, "
                "then check/correct and confirm they will use both.")
    if stage == "C":
        return ("Stage C (Separate analyses): First analyze with Concept 1 (mechanism + 2 evidence details + counterfactual), "
                "then Concept 2 similarly.")
    if stage == "D":
        return ("Stage D (Integration + reflection): Ask how concepts relate (complement/conflict/causal chain), "
                "then prompt 2 actionable takeaways. End with a structured submission-ready summary.")
    return ""


# ---------- Render chat history ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------- First assistant message (if empty) ----------
if len(st.session_state.messages) == 0:
    opening = (
        "Hi! This week we’ll analyze **one decision** using **two course concepts**.\n\n"
        "To start:\n"
        "1) What decision did you make?\n"
        "2) What were your two main options?\n"
        "3) What did you choose, and what happened afterwards?"
    )
    st.session_state.messages.append({"role": "assistant", "content": opening})
    st.rerun()

# ---------- User input ----------
user_text = st.chat_input("Type your response...")
if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})

    # Build prompt with stage constraint
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += st.session_state.messages
    messages.append({"role": "system", "content": stage_instruction(st.session_state.stage)})

    assistant_text = call_llm(messages)
    st.session_state.messages.append({"role": "assistant", "content": assistant_text})

    # Heuristic stage advancement (simple)
    # You can refine later, but this is enough for a class project.
    if st.session_state.stage == "A" and ("option" in user_text.lower() or "chose" in user_text.lower()):
        st.session_state.stage = "B"
    elif st.session_state.stage == "B" and (st.session_state.concept1 and st.session_state.concept2):
        # move once they provided concepts (via sidebar) and started defining them
        st.session_state.stage = "C"
    elif st.session_state.stage == "C" and ("concept 2" in assistant_text.lower() or "second concept" in assistant_text.lower()):
        # after it likely covered both analyses, go D
        st.session_state.stage = "D"

    st.rerun()

# -----------Download transcripts --------------
import json
from datetime import datetime

st.markdown("### 📥 Download chat transcript")

# 2) TXT
lines = []
for m in st.session_state.get("messages", []):
    role = m.get("role", "unknown").upper()
    content = m.get("content", "")
    lines.append(f"{role}:\n{content}\n")

txt_data = "\n---\n".join(lines)

st.download_button(
    label="Download transcript (TXT)",
    data=txt_data.encode("utf-8"),
    file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
    mime="text/plain",
)