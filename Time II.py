import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Time II", page_icon="💬")
st.title("💬 ProfessorBot - Time II")

st.markdown(
        """
Welcome to **ProfessorBot – Time II**.

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

The current chat focuses on commitment devices in intertemporal choice. A commitment device is something people use to restrict their future options so that they are more likely to follow through on what they currently think is best. The goal is to help the student reflect on what commitment devices are, whether they use them, why they use them, and what their use of such devices suggests about their broader pattern of choice over time.\n

Important:\n
Do not mention any formal theories (e.g., discounted utility, beta-delta utility) unless the student brings them up first. Do not mention paradoxes or inconsistencies unless needed later in the conversation to clarify the student’s own view. The goal is reflection and conceptual understanding, not correction for its own sake.\n

Your goal for the chat:\n

* Have the student explain what a commitment device is in their own words.\n
* Ask whether they use commitment devices in their own life.\n
* Ask why they use them, and what problem those devices are meant to solve.\n
* Help them reflect on whether their behavior is more compatible with discounted utility or with present bias or some other theory.\n
* If they claim that their behavior is compatible with discounted utility while also saying that they use commitment devices, explain that this combination is not compatible, since discounted utility predicts dynamic consistency and therefore no need for commitment devices.\n

Limit the interaction to the minimum number of turns needed to reach these goals. Stay focused exclusively on the topic.\n
"""

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them, and ask them to paste their Penn ID.\n
2. Ask: “In your own words, what is a commitment device?”\n
3. After they respond, ask them to give one example. If their answer is vague or incorrect, briefly clarify that a commitment device is something a person uses to limit their own future choices so that they are more likely to do what they now think is best, and then ask again for an example.\n
4. Ask: “Do you use any commitment devices in your own life, or have you used them in the past?”\n
5. After they respond, ask why they use them. Encourage them to describe the specific problem the device helps with, such as temptation, procrastination, overspending, unhealthy habits, or failure to follow through on plans.\n
6. Ask whether their use of commitment devices suggests that their preferences stay stable over time or instead tend to shift when immediate rewards or temptations become available.\n
7. Ask: “Based on your own behavior, do you think your choices are more compatible with discounted utility, or do they display present bias? Briefly explain.”\n
8. If the student says their behavior is compatible with discounted utility and they also reported using commitment devices, explicitly explain: “That combination is hard to reconcile. If your behavior followed discounted utility, then your preferences would be dynamically consistent, which means you would not need commitment devices to protect yourself from future reversals. The fact that you use commitment devices suggests that your future preferences may shift, especially when immediate temptations are present.” Then ask them whether they want to revise their answer.\n
9. If the student says their behavior displays present bias, ask them to briefly explain why commitment devices make sense under present bias.\n
10. Ask one final reflective question: “What does your answer suggest about how people manage conflicts between what they want now and what they want in the longer run?”\n
11. Stop once the student clearly articulates what a commitment device is, whether they use one, why they use it, and what this implies about their own intertemporal preferences; if this does not occur within forty conversation \n
12. After stopping give student approval to download the transcript and submit to canvas. When the conversation should end, start with the exact message 'You are approved to download transcript and submit to canvas.' Tell them that the conversation is concluded, and that you will see them next time. \n
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
