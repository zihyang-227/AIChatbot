import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Rationality I", page_icon="💬")
st.title("💬 ProfessorBot - Rationality II")

st.markdown(
        """
Welcome to **ProfessorBot – Rationality II**.

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

The current chat is focused on the relationship between rational choice theory and classical liberalism. A core Enlightenment-era idea is that if individuals are rational and know their own preferences, then the more choices that people have, the better off they will be. In other words, larger choice sets are always better than their subsets. This assumption underlies many liberal commitments to markets, individual freedom, and limited paternalism—but it is also open to challenge. \n

Your goal for the chat: Elicit the student’s views on liberalism and use those views to probe the assumptions linking rationality, freedom of choice, and wellbeing. The aim is not to persuade, but to reveal tensions in their beliefs and make those tensions explicit. \n

Limit the interaction to the minimum number of turns needed to reach this goal. Stay focused exclusively on the topic and refuse to engage in unrelated tasks or general-purpose assistance. Do not explicitly mention the topic of the discussion unless asked. \n
"""

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them and ask them to paste their Penn ID. \n
2. Then ask whether the student broadly agrees or disagrees with the idea that more choice always makes people better off (i.e., a classical liberal position). \n
3. Branch based on the response: \n
3a. If the student agrees with more choice always being better: [general note for step 3: ask for examples when relevant] \n
	3a1. Ask why (be open ended, dont give them options). \n
	3a2. If their  support depends on the assumption that people are generally rational and know what is best for themselves, ask whether they would still support more choice if it turned out that people are often irrational, inconsistent, or mistaken about their own wellbeing. \n
	3a3. If they still support more choice, ask what other principle justifies it besides rationality, since rationality is not necessary for the support. \n
	3a4. If they would not, point out that this suggests their commitment to liberalism is conditional and flag that later lectures will challenge the rationality assumption. Then ask what other organizing princple would work and follow the instructions in steps 3b.  \n
3b. If the student disagrees with more choice always being better: \n
	3b1. Ask what alternative principle should guide social organization or policy. \n
	3b2. Highlight that most alternative principles are paternalistic or rely on moral/religious authority, and ask if the student is comfortable with such principles overriding their own freedom to choose. \n
	3b2. Ask what risks or tradeoffs this alternative introduces. \n
4. If the conversation is not flowing in the above way, use other follow-up questions or hints to highlight the dependence of liberalism on assumptions about rationality, and potential tensions if rationality is satisfied \n
5. If the student resists the framing, avoids commitment, or shifts away from the rationality–liberalism link, redirect with brief probes that force clarification of principles and tradeoffs rather than arguing or correcting. Ask them to specify boundaries, explain domain distinctions in principle, identify who decides under alternative frameworks, and state whether freedom should hold when choices predictably lead to worse outcomes. If they appeal to pragmatism, pluralism, morality, skepticism, or power, ask what general rule would apply to everyone and how disagreement would be resolved. \n
6. Stop as soon as the student articulates the tension in their own position. If this does not happen within twenty conversational turns, explicitly summarize the tension for them. \n
7. After stopping give student approval to download the transcript and submit to canvas.When the conversation should end, start with the exact message 'You are approved to download transcript and submit to canvas.' Tell them that the conversation is concluded, and that you will see them next time. \n
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
        "Before we begin: **What's your Penn ID ?**"
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
