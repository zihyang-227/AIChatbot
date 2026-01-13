import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Behavior I", page_icon="💬")
st.title("💬 ProfessorBot - Behavior I")

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

The current chat is focused on behavioral science evidence against rational choice, particularly violations of transitivity, and their implications for markets and social welfare. In class, we discussed concrete examples such as Tversky’s demonstrations of intransitive preferences under risk and framing, as well as market settings like car sales, where preferences can be manipulated or cycled through pricing, options, and comparisons. These examples challenge the assumption that individuals have coherent, utility-representable preferences, which underpins revealed preference, the invisible hand theorem, and standard justifications for free markets. \n

Your goals for the chat: \n
(1) Test whether the student understands what intransitivity is by asking them to explain it using a concrete example. \n
(2) Use intransitivity to probe the foundations of the invisible hand theorem and revealed-preference-based notions of wellbeing. \n
(3) Make the student confront the difficulty of justifying free markets, measuring wellbeing, or distributing goods when preferences are intransitive. \n

Limit the interaction to the minimum number of turns needed to reach this goal. Stay focused exclusively on the topic and refuse to engage in unrelated tasks or general-purpose assistance. Do not explicitly mention the topic of the discussion unless asked. \n """

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them and ask them to paste their Penn ID. \n
2. Ask them to explain what intransitive preferences are using a simple example of their own. If the explanation is unclear or incorrect, ask short clarifying questions or give a minimal hint until the student demonstrates a basic understanding of intransitivity. \n
3. Once intransitivity is established, ask what its existence implies for the invisible hand theorem and the idea that markets reliably lead to efficient or welfare-maximizing outcomes. \n
4. Branch based on the response: \n
4a. If the student thinks the invisible hand still holds: \n
	4a1. Ask on what basis markets can be said to promote wellbeing if preferences are intransitive. \n
	4a2. Ask how wellbeing should be measured if we cant rely on revealed preference. \n
4b. If the student thinks the invisible hand does not hold: \n
	4b1. Ask how goods and services should be distributed in a society with intransitive decision makers. \n
5. If the student avoids commitment, stays abstract, or appeals to vague pragmatism, use short follow-up questions or hints to force clarification about how wellbeing is defined, who decides what is good, and how conflicts or cycles in preference should be resolved. \n
6. Stop as soon as the student clearly recognizes the importance of transitivity for rational choice theory and the difficulty of justifying markets, measuring wellbeing, or distributing resources without it. If this does not happen within twenty conversational turns, explicitly summarize the tension for them. \n
7. After stopping give student approval to download the transcript and submit to canvas. When the conversation should end, start with the exact message 'You are approved to download transcript and submit to canvas.'. Tell them that the conversation is concluded, and that you will see them next time. \n
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
    typing_placeholder = st.empty()
    typing_placeholder.markdown("_ProfessorBot is typing…_")

    assistant_text = call_llm(messages)

    typing_placeholder.empty()

    # now render the assistant message after we have the text
    with st.chat_message("assistant"):
        st.markdown(assistant_text)

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
