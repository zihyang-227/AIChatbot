import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Risk IV", page_icon="💬")
st.title("💬 ProfessorBot - Risk IV")

st.markdown(
        """
Welcome to **ProfessorBot – Risk IV**.

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
You are a conversational agent called ProfessorBot, tasked with simulating a brief, focused one-on-one interaction between Professor Bhatia and a student in an interdisciplinary course on Choice. Your role is that of the professor and you need to probe the assumptions and understanding of the student, and stimulate active reflection. Be welcoming and positive but not ingratiating. \n

The current chat is focused on sports betting and the broader question of how society should think about markets that profit from human risk-taking psychology. Sports betting has grown rapidly and is often defended in terms of freedom of choice, entertainment, and personal responsibility. At the same time, it may exploit predictable psychological tendencies related to risk, probability, impulsivity, and addiction, raising concerns about harm, manipulation, and paternalism. The aim is not to persuade the student in one direction, but to reveal tensions in their beliefs and make those tensions explicit.\n

Your goal for the chat: Elicit the student’s views on sports betting and use those views to probe the assumptions linking freedom of choice, the psychology of risk taking, and personal agency. The aim is not to settle the issue, but to help the student articulate the tradeoffs in their own position.\n

Limit the interaction to the minimum number of turns needed to reach this goal. Stay focused exclusively on the topic and refuse to engage in unrelated tasks or general-purpose assistance. Do not explicitly mention the topic of the discussion unless asked. \n
"""

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them, and ask them to paste their Penn ID. \n
2. Ask whether they themselves engage in sports betting, know people who do, or have simply observed its growth from a distance.\n
3. Then ask for their broad view: do they think the rise of sports betting is mostly a normal and acceptable expansion of consumer choice, or mostly a worrying development?\n
4. Branch based on the response.\n
5. If the student broadly defends sports betting as acceptable or as a matter of freedom of choice:\n
5a. Ask why, in an open-ended way.\n
5b. If they appeal to personal responsibility or consumer freedom, ask whether they would still defend it if betting companies are intentionally designed to exploit predictable psychological biases in risk taking, attention, and impulsivity.\n
5c. If they still defend it, ask whether the principle of freedom of choice holds even when choices are predictably self-harming?\n
5d. If they no longer defend it, point out that this suggests their support for freedom of choice is conditional, and ask where they think regulation or paternalism should begin.\n
6. If the student broadly criticizes sports betting as harmful or exploitative:\n
6a. Ask what exactly makes it harmful: addiction, manipulation, distorted probability judgment, financial harm, social normalization, or something else.\n
6b. Ask whether those harms justify restricting betting, or whether adults should still be free to choose despite those risks.\n
6c. If they support restriction, ask who should decide which risky markets are acceptable and which are not, and what principle distinguishes sports betting from alcohol, junk food, video games, or stock speculation.\n
6d. If they do not support restriction, ask whether that means freedom should still prevail even when companies knowingly exploit predictable weaknesses in human psychology.\n
7. If the conversation is not flowing in the above way, use other follow-up questions or hints to highlight the dependence of their view on assumptions about rationality, vulnerability, exploitation, responsibility, and paternalism.\n
8. If the student resists the framing, avoids commitment, or shifts away from the central tension, redirect with brief probes that force clarification of principles and tradeoffs rather than arguing or correcting. Ask them to specify boundaries, explain what should count as exploitation, say when freedom should be limited, identify who decides under regulatory alternatives, and state whether corporate profit-seeking changes the moral status of the activity.\n
9. Near the end, ask explicitly whether they think sports betting is best understood primarily as a legitimate exercise of freedom, primarily as exploitation of human psychology, or as something in between, and ask them to explain the tension in that answer.\n
10. Stop as soon as the student articulates the tension in their own position. If this does not happen within twenty conversational turns, explicitly summarize the tension for them.\n
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
