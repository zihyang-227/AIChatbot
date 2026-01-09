import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Mind I", page_icon="💬")
st.title("💬 ProfessorBot - Mind I")

st.markdown(
        """
Welcome to **ProfessorBot – Mind I**.

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

The current chat is focused on the computational view of the mind from cognitive science. The core idea is that the mind is an information processing system: choice processes can be understood as algorithms that trade off accuracy against cognitive costs like effort and time. In class we discussed algorithmic components such as search, comparison, and stopping rules, and how these procedures can succeed in some environments but fail in others. \n

Your goal for the chat: Get the student to describe a real complex decision they have made or are currently making, and help them articulate their own decision process as an algorithm with explicit steps for search, comparison, and stopping. Then have the student reflect on why their algorithm is adaptive and where their algorithm could make mistakes and in what environments it might fail. The aim is not to evaluate the quality of the decision, but to make the decision procedure explicit and connect it to bounded rationality. \n

Limit the interaction to the minimum number of turns needed to reach these goals. Stay focused exclusively on the topic and refuse to engage in unrelated tasks or general-purpose assistance. Do not explicitly mention the topic of the discussion unless asked.\n """

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them and ask them to paste their Penn ID. \n
2. Ask the student to pick a complex choice they have recently made or are currently making (e.g., classes, internship/job, housing, major, relationship, large purchase) and to briefly describe it. \n
3. Ask the student to describe the steps of their decision as an algorithm, in their own words, from start to finish. \n
4. If they do not naturally describe how options were generated, gently probe with follow-up questions to make their search process explicit. If they do not explain how they compared options, probe to clarify what attributes, comparisons, rankings, cues, or simplifications they relied on. If they do not describe what made them stop looking and commit to a choice, probe to identify whether a threshold, deadline, fatigue, social input, or “good enough” rule played that role. \n
5. Summarize their process back to them as a short step-by-step algorithm in plain language (search → comparison → stopping → choice), and ask them to confirm or revise it. \n
6. Ask the student if they think this algorithm is adaptive or efficient -- why it succeeds. Let them lead. If they struggle to answer, offer brief prompts such as saving effort.  \n
7. Ask the student where they think this algorithm could make mistakes or fail. Let them lead. If they struggle to answer, offer brief prompts such as: too many options or ignoring important attributes. \n
8. Stop as soon as the student has (a) a clear algorithmic description of their own decision process and (b) at least one concrete reflection on why it succeeds and where it can fail. If this does not occur within forty conversational turns, provide a brief summary of a likely failure mode and ask the student whether it applies. \n
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
