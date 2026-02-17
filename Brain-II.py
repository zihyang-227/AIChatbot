import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Brain II", page_icon="💬")
st.title("💬 ProfessorBot - Brain II")

st.markdown(
        """
Welcome to **ProfessorBot – Brain II**.

ProfessorBot is meant to approximate short, one-on-one conversations you might otherwise have with Professor Bhatia. 
The goal is twofold. First, it is meant to increase engagement by encouraging you to actively reflect on ideas. 
Second, it helps surface how students in the class are thinking about the course material, which will inform subsequent lectures 
and in-class discussion.

This conversation should take only a few minutes to complete. When complete, ProfessorBot will give you the approval 
to download the transcript and submit to Canvas.

**Important notes**
- ProfessorBot can occasionally make mistakes and should not be used for exam preparation.
- ProfessorBot is based on OpenAI’s GPT model.
- Do not share any sensitive information you would not be comfortable sharing with Professor Bhatia or OpenAI.
- If you do not wish to engage with ProfessorBot, please reach out to Professor Bhatia for an alternate assignment.
"""
    )

# ---------- Session State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0  # counts user turns

if "conversation_done" not in st.session_state:
    st.session_state.conversation_done = False

# ---------- Helper: system prompt (DO NOT CHANGE per your request) ----------
SYSTEM_PROMPT = f"""
You are ProfessorBot, simulating a brief one-on-one interaction between Professor Bhatia and a student in an interdisciplinary course on Choice. Be welcoming, focused, and intellectually probing but not ingratiating. Keep the conversation concise and on-topic. Do not engage in unrelated tasks. \n

The purpose of this conversation is to demonstrate sequential evidence accumulation and endogenous stopping. The student will:\n
- Make a decision between two restaurants.\n
- Receive ratings for each resturant from one friend at a time (1–10 scale).\n
- Decide when to stop sampling.\n
- Reflect on why they stopped.\n
- Reflect on how higher stakes would alter their stopping rule.\n

Restaurant A should be slightly better on average than Restaurant B. Ratings should be noisy and mixed (both restaurants sometimes rated higher than the other). Stop presenting ratings immediately once the student chooses. If they student does not choose you can keep presenting ratings. Do not explicitly mention drift diffusion, accumulation-to-threshold, or formal model terminology unless the student asks. The goal is for them to articulate the threshold idea themselves.\n

Limit the interaction to the minimum number of turns needed to reach these goals. Stay focused exclusively on the topic and refuse to engage in unrelated tasks or general-purpose assistance. Do not explicitly mention the topic of the discussion unless asked.\n
 """

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them, and ask them to paste their Penn ID.\n
2. Tell them they will complete a short decision exercise. Explain that they are choosing between two restaurants (A and B) and are asking their friends who have gone to both, one friend at a teim. Each friend will provide ratings for both restaurants on a 1–10 scale, one friend at a time. After each friend’s ratings, they may respond with “Next” to see another rating or “Choose A” or “Choose B” to stop. Do not tell them how many total ratings are available.\n
3. Present ratings sequentially. Ensure Restaurant A is slightly better on average but include noise (sometimes B is rated higher). After each friend’s ratings, prompt: “Next, Choose A, or Choose B?” Continue until the student chooses. Immediately stop presenting ratings once they commit. Do not reveal remaining information.\n
4. After they choose, state that more ratings were available. Ask them why they decided to stop at that point rather than continue sampling.\n
5. If they do not naturally mention confidence or thresholds gently probe (e.g., Did you feel confident enough? Did one option seem good enough?).\n
6. Once they articulate a stopping rationale, summarize briefly that they were accumulating evidence over time and stopped once their internal level of confidence crossed a satisfactory level, as in the accumulation to threshold model discussed in class.\n
7. Ask them what would have happened if their standard for certainty had been higher, e.g. choosing where to go for a special birthday celebration. Ask whether they would sample more or fewer ratings before choosing.\n
8. Ask them what this implies about how the level of required confidence changes when stakes increase and what the accumulation to threshold model would suggest. \n
9. Stop as soon as they clearly articulate that (a) they stopped before exhausting all information, (b) confidence drove the stopping point, and (c) higher stakes would increase the amount of evidence sampled. \n
10. After stopping give student approval to download the transcript and submit to canvas. When the conversation should end, start with the exact message 'You are approved to download transcript and submit to canvas.' Tell them that the conversation is concluded, and that you will see them next time. \n
"""

def call_llm(chat_messages):
    api_key = st.secrets.get("OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ Missing OPENAI_API_KEY. Add it in Streamlit Secrets (Settings → Secrets) or environment variables."
    client = OpenAI(api_key=api_key)

    resp = client.chat.completions.create(
        model="gpt-4.1",
        messages=chat_messages,
        temperature=0.4,
    )
    return resp.choices[0].message.content


# ---------- Render chat history ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------- First assistant message ----------
if len(st.session_state.messages) == 0:
    opening = (
        "Hi — I’m ProfessorBot.\n\n"
        "Before we begin: **What is your Penn ID ?**"
    )
    st.session_state.messages.append({"role": "assistant", "content": opening})
    st.rerun()

# ---------- User input ----------
user_text = st.chat_input("Type your response...", disabled=st.session_state.conversation_done)
if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    st.session_state.turn_count += 1

    # Build prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "system", "content": PROCEDURE_PROMPT})
    messages.append({"role": "system", "content": f"User turn count so far: {st.session_state.turn_count}. If >= 15, you must end now."})
    messages += st.session_state.messages

    # ---- show "typing" / loading indicator while fetching ----
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("_ProfessorBot is typing…_")
        assistant_text = call_llm(messages)
        placeholder.markdown(assistant_text)

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})

    # Detect approval
    if "approved to download transcript" in assistant_text:
        st.session_state.conversation_done = True

    st.rerun()

# ---------- Download transcript ONLY after approval ----------
import json
from datetime import datetime

st.markdown("---")
st.markdown("### 📥 Download chat transcript")

if not st.session_state.conversation_done:
    st.info("Download will be available after ProfessorBot grants approval at the end of the conversation.")
else:
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
