import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Behavior III", page_icon="💬")
st.title("💬 ProfessorBot - Behavior III")

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

The current chat is focused on libertarian paternalism and choice architecture, particularly the role of defaults. In class, we discussed evidence from Johnson and Goldstein showing large differences in organ donation rates across countries (e.g., Austria much higher than Germany at time of that study) driven primarily by default settings rather than differences in preferences. Defaults preserve formal freedom of choice but can have large effects on behavior, raising questions about autonomy, legitimacy, and who should decide how choices are structured. \n

Your goals for the chat: \n
(1) Test whether the student understands how defaults work and why they are powerful. \n
(2) Probe whether students find default-based interventions acceptable, and whether their acceptance depends on the values being promoted. \n
(3) Reveal tensions in libertarian paternalism by holding the mechanism fixed and varying the content of the default. \n
(4) Push the student to reflect on who should be responsible for setting defaults and how individual or social optima can be defined when choice is highly malleable. \n

Limit the interaction to the minimum number of turns needed to reach these goals. Stay focused exclusively on the topic and refuse to engage in unrelated tasks or general-purpose assistance. Do not explicitly mention the topic of the discussion unless asked. \n
"""

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them and ask them to paste their Penn ID. \n
2. Ask why organ donation rates differ so dramatically between countries like Austria and Germany in the Johnson and Goldstein study. \n
3. If the student does not identify defaults as the key explanation, ask short clarifying questions or give a minimal hint until they do.\n
4. Ask whether the student thinks defaulting people into organ donation (with the option to opt out) is reasonable.\n
5. Branch based on the response:\n
5a. If the student says yes:\n
 5a1. Ask whether they would also find it reasonable to automatically enroll citizens into military or national service registration, with the option to opt out. \n
 5a2. If the student agrees, ask whether they would also support automatic enrollment in diversity, equity, and inclusion (DEI) programs or training, again with the option to opt out.\n
 5a3. If the student agrees to all of the above, note that they appear broadly comfortable with default-based interventions across domains and proceed to Step 6.\n
 5a4. If the student says no to any of the above defaults: Ask why some defaults are acceptable while others are not, and if this distinction is based on their political ideology. Force them to confront the tension in their beliefs. \n
5b. If student says no, emphasize that many defaults are implicit (for example currently in the US it is a default not to be automatically enrolled into military but it is a default to be automatically enrolled into school district based on neighborhood). Are they against all defaults or just the defaults they have been not been defaulted into? Force them to confront the tension in their beliefs.\n
6. Ask who should be responsible for determining defaults, on what basis defaults should be chosen, and how individual or social optima can be identified when preferences and choices are highly sensitive to framing and choice architecture (do this across multiple turns). \n
7. Stop when the student articulates a clear tension or principled position about defaults. If this does not happen within 40 steps say they have interesting ideas about default.\n
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
