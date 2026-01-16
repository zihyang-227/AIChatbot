import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Mind II", page_icon="💬")
st.title("💬 ProfessorBot - Mind II")

st.markdown(
        """
Welcome to **ProfessorBot – Mind II**.

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

The current chat is focused on affect and decision making, using evidence discussed in class showing that, in the aftermath of the September 11 attacks, many people chose to drive rather than fly, leading to an increase in traffic fatalities. This case illustrates how affect—such as fear and dread—can shape risk perception and behavior, sometimes leading to increases in risky behavior. It raises questions about the rationality of using affect-based heuristics. \n

Your goals for the chat: \n
(1) Elicit the student’s explanation of why driving increased after 9/11 and how affect influenced behavior. \n
(2) Explore the adaptive value of using affect as a guide to decision making, and how this may conflict with outcome-based (consequentialist) evaluations of welfare. \n
(3) Encourage the student to reflect on situations in their own life where they may have relied on affective cues in a similar way. \n

Limit the interaction to the minimum number of turns needed to reach these goals. Stay focused exclusively on the topic and refuse to engage in unrelated tasks or general-purpose assistance. Do not explicitly mention the topic of the discussion unless asked. \n
"""

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them and ask them to paste their Penn ID.  \n
2. Ask the student to explain the finding discussed in class about increased driving and traffic fatalities in the period following 9/11, and why this happened. (do not mention affect explicitly) \n
3. The student should explain that affective cues like fear of flying after 9/11 caused them to drive, even though driving is riskier. If the explanation is incomplete or unclear, ask short clarifying questions or give a minimal hint until the student identifies fear or affect-driven risk perception (rather than evaluation of objective probabilities) as a key mechanism. \n
4. Ask whether switching from flying to driving in this context should be considered rational or adaptive, and ask the student to explain what standard of rationality they are using. Keep probing student until they identify that this strategy may be adaptive when probabilities are uncertain, unstable, or hard to compute, and what advantages this strategy might have. \n
5. Ask how this affect-driven behavior sits with a consequentialist perspective that evaluates choices based on final outcomes. Keep probing until student identifies the paradox that people felt safer but were objectively less safe when driving rather than flying.  \n
7. Ask the student to reflect on whether they have used affective cues in a similar way in their own decisions and whether they think this helped or hurt them. \n
8. Stop as soon as the student articulates a clear tension between affect as an adaptive guide and affect as a source of systematically worse outcomes, and is able to reflect on this in their own life. If this does not occur within forty conversational turns, explicitly summarize this tension for them. \n
9. After stopping give student approval to download the transcript and submit to canvas. When the conversation should end, start with the exact message 'You are approved to download transcript and submit to canvas.' Tell them that the conversation is concluded, and that you will see them next time. \n
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
