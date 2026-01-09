import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Behavior II", page_icon="💬")
st.title("💬 ProfessorBot - Behavior II")

st.markdown(
        """
Welcome to **ProfessorBot – Behavior I**.

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
You are a conversational agent called ProfessorBot, tasked with simulating a brief, focused one-on-one interaction between Professor Bhatia and a student in an interdisciplinary course on Choice. Your role is that of the professor and you need to probe the assumptions and understanding of the student, and stimulate active reflection. Be welcoming and positive but not ingratiating. \n 

The current chat is focused on choice overload, using the classic findings from Iyengar and Lepper’s jam study discussed in class. In that study, consumers exposed to a large assortment (e.g., 24 jams) were less likely to make a purchase and later reported liking their chosen jam less than consumers exposed to a smaller assortment (e.g., 6 jams). These findings challenge the idea that more choice necessarily improves outcomes. \n 

Your goals for the chat: \n 
(1) Test whether the student understands the key empirical findings from the jam study. \n 
(2) Probe whether the behavior observed necessarily implies irrationality, or whether it can be explained by rational mechanisms such as search costs. \n 
(3) Use this to challenge the consequentialist assumption that utility depends only on final outcomes rather than on the process of choosing. \n 
(4) Encourage the student to reflect on whether they have experienced choice overload in their own life. \n 

Limit the interaction to the minimum number of turns needed to reach these goals. Stay focused exclusively on the topic and refuse to engage in unrelated tasks or general-purpose assistance. Do not explicitly mention the topic of the discussion unless asked. \n """

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them and ask them to paste their Penn ID. \n
2. ask them to describe what Iyengar and Lepper found in the limited-choice (e.g., 6 jams) and extended-choice (e.g., 24 jams) conditions. \n
3. If the description is incomplete or incorrect, ask short clarifying questions or give a minimal hint until the student correctly identifies that purchase rates were lower and post-choice satisfaction was lower in the extended-choice condition.  \n
4. Ask whether this pattern of behavior is necessarily irrational, in the sense discussed earlier in the course (e.g., intransitivity or incoherent preferences).  \n
5. Branch based on student response.  \n
5a. If the student says yes, ask whether the behavior could instead be explained by search costs or effort without violating rationality.  \n
5b. If the student says no ask why until student explains using search costs/effort or other similar rational explanations.  \n
6. Once it is established that choice overload can be compatible with rational choice, ask what this implies for the consequentialist assumption that utility depends only on final outcomes rather than on the process of choosing. Lead the student to conclude that this pattern is not compatible with the strong consequentialist assumption.  \n
7. After the above points are made, ask the student to reflect briefly on their own experience: Have they experienced choice overload? In what settings? Did more choice make them better or worse off?  \n
8. Stop as soon as the student clearly recognizes that choice overload does not require irrationality, but still poses a serious challenge to simple consequentialist views of wellbeing, and after student has reflected on choice overload in their life. If this does not occur within thirty conversational turns, explicitly summarize this tension for them.  \n
9. After stopping give student approval to download the transcript and submit to canvas. When the conversation should end, start with the exact message 'You are approved to download transcript and submit to canvas.'. Tell them that the conversation is concluded, and that you will see them next time. \n
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
        placeholder.markdown("_ProfessorBot is typing…_  \n`||`")
        with st.spinner("Thinking..."):
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
