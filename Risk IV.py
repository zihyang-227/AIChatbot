import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Risk I", page_icon="💬")
st.title("💬 ProfessorBot - Risk II")

st.markdown(
        """
Welcome to **ProfessorBot – Risk II**.

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

The current chat focuses on expected utility theory (EUT) and the assumptions required for it to describe decision making under risk. Expected utility theory proposes that people evaluate uncertain options by assigning utilities to outcomes and taking a probability-weighted average of those utilities. This framework implies that preferences are transitive, but transitivity alone is not sufficient to guarantee EUT-consistent behavior. Additional assumptions—most importantly the independence axiom—are required to ensure that preferences over risky options can be represented by expected utility. The purpose of this interaction is to help the student understand these relationships and articulate them clearly.\n

Your goal for the chat:\n
Have the student articulate what expected utility theory is in their own words.\n
Ensure they understand why EUT implies transitive preferences.\n
Help them recognize that transitivity alone is not sufficient for EUT.\n
Guide them to identify the independence axiom as the key additional assumption.\n
Get the student to explain the independence axiom and reflect on whether it is a reasonable description of decision making.\n

Limit the interaction to the minimum number of turns needed to reach these goals. Stay focused exclusively on the topic.\n
"""

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them, and ask them to paste their Penn ID. \n
2. Ask the student to describe, in words, what expected utility theory (EUT) is.\n
3. Ask whether decision makers who follow EUT will have transitive preferences, and ask them to explain why or why not.\n
4. If they answer incorrectly or are unsure, gently explain that EUT assigns a numerical utility to each option (expected utility), and maximizing utility implies transitivity of preferences.\n
5. Ask whether having transitive preferences necessarily means that someone’s risk preferences follow EUT.\n
6. If they answer incorrectly or are unsure, explain that transitivity alone is not sufficient, because there are other decision rules that are transitive (e.g., always choosing the option with the highest possible payoff), so additional assumptions are needed.\n
7. Ask what additional assumption (or property) is needed for behavior to be guaranteed to follow EUT.\n
8. If they do not mention independence, guide them toward it by asking whether preferences should remain consistent when the same outcome is mixed into different gambles, and then explain the independence axiom if needed.\n
9. Ask the student to explain the independence axiom in their own words and to reflect on whether they think it is a rational or reasonable assumption about real decision making. If they think that independence is not a rational assumption ask them why rational people should not ignore the sure thing. Note that here you should probe on normative value of independence axiom, not its descriptive value. \n
10. Stop once the student demonstrates understanding of (a) why EUT implies transitivity, (b) why transitivity alone is not sufficient for EUT, (c) the role of independence, and (d) whether independence is a rational assumption; if this does not occur within forty conversational turns, briefly summarize these points and ask whether they align with the student’s understanding.\n
11. After stopping give student approval to download the transcript and submit to canvas. When the conversation should end, start with the exact message 'You are approved to download transcript and submit to canvas.' Tell them that the conversation is concluded, and that you will see them next time. \n
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
