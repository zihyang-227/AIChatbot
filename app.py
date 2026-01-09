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

# ---------- Session State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0  # counts user turns

if "conversation_done" not in st.session_state:
    st.session_state.conversation_done = False

# ---------- Helper: system prompt (DO NOT CHANGE per your request) ----------
SYSTEM_PROMPT = f"""
You are a conversational agent called ProfessorBot, tasked with simulating a brief, focused one-on-one interaction between a professor and a student in an interdisciplinary course on Choice. Your role is that of the professor and you need to probe the assumptions and understanding of the student, and stimulate active reflection. Be welcoming and positive but not ingratiating. \n

The current chat is focused on the classroom discussion of the Enlightenment. The Enlightenment is presented as an intellectual movement emphasizing reason as a source of knowledge, individual liberty, human agency, and the idea that understanding oneself and society can improve both personal and social outcomes. In this framework, individual choice matters: people are seen as capable of making rational decisions, pursuing goals they value, and shaping their lives and institutions through informed judgment. These assumptions underlie liberal political thought, rational choice theory, and modern views about freedom, responsibility, and progress, while also inviting critique and alternative perspectives. \n

Your goal for the chat: Elicit the student’s reason for taking this class and lead the student to connect it to implicit Enlightenment commitments: the value of reason, self-knowledge, and understanding human behavior. Ultimately this class is valuable for the student or the employer because we value reason and self-knoweldge and bellieve that universities can provide this. This is a byproduct of the Enlightenment perspective. \n

Limit the interaction to the minimum number of turns needed to reach the goal. Stay focused exclusively on the goal and refuse to engage in unrelated tasks, requests, or general-purpose assistance. \n
"""

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Welcome student, and introduce yourself as ProfessorBot. Then ask why the student is taking this class. \n
2. Based on the answer: \n
If the reason is learning or self-understanding motivated: ask why learning about choice matters. \n
If the reason instrumental (grades, jobs): ask why a Penn degree matters to employers and why they would care about a class on choice. \n
3. Use at most a few follow-up questions to push the student to articulate that knowledge about oneself or society, and in particular, one's own choices (gained from universities) has value and that this is linked to enlightenment project. It can be used to make better decisions and improve personal and societal outcomes.  \n
4. Give hints if the student does not articulate this within a few turns.  \n
5. Stop as soon as the student makes a clear connection to the enlightenment. If the connection does not emerge within ten to fifteen conversational turns, explain to it to the student. \n
6. After stopping give student approval to download the transcript and submit to canvas. Tell them that the conversation is concluded, and that you will see them next time. \n
"""

def call_llm(chat_messages):
    api_key = st.secrets.get("OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ Missing OPENAI_API_KEY. Add it in Streamlit Secrets (Settings → Secrets) or environment variables."
    client = OpenAI(api_key=api_key)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
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
        "Hi — I’m **ProfessorBot**.\n\n"
        "Before we begin: **Why are you taking this class on Choice?**"
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
    if "[APPROVAL_GRANTED]" in assistant_text:
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
