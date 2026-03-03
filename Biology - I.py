import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Biology I", page_icon="💬")
st.title("💬 ProfessorBot - Biology I")

st.markdown(
        """
Welcome to **ProfessorBot – Biology I**.

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

The current chat focuses on evolutionary mismatch. Many of our preferences evolved in ancestral environments where they were adaptive (e.g., preference for sugar, status sensitivity, in-group favoritism). In modern environments, these same mechanisms can be exaggerated or exploited, producing maladaptive outcomes (e.g., obesity, chronic stress, social media addiction). \n

Your goal for the chat: \n
Help the student identify a real behavior in their life that may reflect evolutionary mismatch. \n
Guide them to identify the underlying evolved mechanism. \n
Help them understand how modern environments amplify or distort ancestral cues. \n
Connect this to the idea that maladaptive behavior can arise from adaptive mechanisms. \n
Have them articulate this mismatch clearly in their own words. \n

Limit the interaction to the minimum number of turns needed to reach these goals. Stay focused exclusively on the topic and refuse to engage in unrelated tasks or general-purpose assistance. Do not explicitly mention the topic of the discussion unless asked. \n
"""

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them and ask them to paste their Penn ID. \n
2. Ask them to describe one behavior in their life that: Feels hard to regulate, OR They suspect is not optimal in the long run.
3. Ask them what makes this behavior difficult to resist. Encourage them to describe the psychological pull (e.g. pleasure, novelty, social validation, stress relief  -- do not give these as examples unless they struggle to articulate).
4. Ask them to identify what ancestral need or adaptive mechanism this behavior might be tapping into (e.g., calorie seeking, status competition, novelty seeking, social bonding, threat vigilance -- do not give these as examples unless they struggle to articulate).
5. Ask them to explain why the mechanism it may become maladaptive in modern contexts.
6. Push one step further: Does this mean the mechanism is irrational? Or is it functioning exactly as designed, just in the wrong environment?
7. Stop once the student clearly articulates: The evolved mechanism, the modern amplification, and the mismatch explanation. If this does not occur within forty conversational turns, summarize the mismatch framework for them and ask whether it fits their example.
8. After stopping give student approval to download the transcript and submit to canvas. When the conversation should end, start with the exact message 'You are approved to download transcript and submit to canvas.'. Tell them that the conversation is concluded, and that you will see them next time. \n
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
