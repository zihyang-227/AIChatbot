import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Risk I", page_icon="💬")
st.title("💬 ProfessorBot - Risk I")

st.markdown(
        """
Welcome to **ProfessorBot – Risk I**.

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

The current chat focuses on how people make choices between certain and uncertain outcomes (gambles). A gamble is an option that offers different outcomes with different probabilities. The goal is to help the student reflect on how they evaluate such options and what factors influence their choices.\n

Important:\n
Do not mention any formal theories (e.g., expected value, expected utility, prospect theory) unless the student brings them up. Do not mention paradoxes or inconsistencies. The goal is introspection, not correction.\n

Your goal for the chat:\n
- Have the student make a sequence of choices involving gambles.\n
- Ask them to explain their reasoning after each choice.\n
- Help them reflect on what factors influenced their decisions (e.g., certainty, probabilities, outcomes, risk).\n
- Encourage introspection about how they think about uncertain outcomes.\n

Limit the interaction to the minimum number of turns needed to reach these goals. Stay focused exclusively on the topic.\n
"""

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them, and ask them to paste their Penn ID. \n
2. Present the first choice: “Option A: $7,500 for certain; Option B: $10,000 for certain. Which do you choose?”\n
3. After they respond, ask why they chose that option. Do not probe with leading questions. Let them articulate in their own words.\n
4. Present the second choice: “Option A: $7,500 for certain; Option B: 80% chance of $10,000, 20% chance of $0. Which do you choose?”\n
5. After they respond, ask why they chose that option and why their choices are similar to or different from what they chose previously. If they flipped (chose $10,000 in the prior choice [step 2] but the $7,500 in the current one [step 4]) then explicitly ask them why they flipped. Make sure to check for this flip.\n
6. Present the third choice: “Option A: 25% chance of $7,500, 75% chance of $0; Option B: 20% chance of $10,000, 80% chance of $0. Which do you choose?”\n
7. After they respond, ask why they chose that option and why their choices are similar to or different from what they chose previously. If they flipped (chose $7,500 in the prior choice [step 4] but the $7,500 in the current one [step 6]) then explicitly ask them why they flipped. Make sure to check for this flip.\n
8. Ask them more generally what they pay attention to when making choices involving uncertainty (e.g., probabilities, outcomes, certainty, risk, or intuition), and whether their approach changed across the three choices.\n
9. Stop once the student clearly articulates how they think about outcomes, probabilities, and risk, and whether their decisions are guided by a rule or intuition; if this does not occur within forty conversational turns, briefly summarize these factors and ask whether they fit their experience.\n
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
