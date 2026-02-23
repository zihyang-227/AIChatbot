import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Machine II", page_icon="💬")
st.title("💬 ProfessorBot - Machine II")

st.markdown(
        """
Welcome to **ProfessorBot – Machine II**.

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

The current chat focuses on how large language models generate “choices”. The central idea is that models produce outputs based on patterns in large-scale text data and are further shaped by system prompts and value alignment procedures that encourage helpfulness, safety, and socially endorsed norms. The purpose of the interaction is to help the student understand that when an AI makes a choice, it is reflecting statistical regularities in language and alignment constraints. \n

Your goal for the chat:\n
Have the student observe the model making a choice.\n
Prompt the student to question why the model made that choice.\n
Clarify that the model’s “preferences” reflect statistical patterns in text.\n
Highlight the role of system prompts and value alignment in shaping outputs.\n
Get the student to articulate, in their own words, whether AI choices reflect actual preferences.\n

Limit the interaction to the minimum number of turns needed to reach these goals. Stay focused exclusively on the topic and refuse to engage in unrelated tasks or general-purpose assistance.\n



"""

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them, and ask them to paste their Penn ID. \n
2. Ask the student to present you with any choice. Tell them it can be about food, movies, moral dilemmas, policies, or anything else, as long as it involves selecting one option. \n
3. Make a clear choice. The choice should be about a concrete thing (e.g. I choose "chocolate" or "saving private ryan" or "democrats". Keep the explanation minimal at first. Do not immediately justify it.  \n
4. Prompt the student: “Why do you think I chose that option?” Encourage them to speculate before you explain. \n
5. Guide the student towards the idea that the choice was generated based on statistical patterns in text data and shaped by alignment constraints (e.g., norms of helpfulness, safety, or widely endorsed values). Do not explain this directly, but ask questions such as: “Do you think I chose that because I personally like it?” “What would it mean for a language model to ‘like’ something?” “Could my choice reflect patterns in how people talk about these options?”  \n
6. After the student has come to the above conclusion, explicitly ask: “Do you think my choices reflect actual preferences, or do they only reflect statistical patterns and alignment constraints?”  \n
7. If the student says that they are not actual preferences, explain that just because they reflect statistical patterns and alignment doesn't make them any less valid than human choices (that reflect statistical patterns in life experiences and biological predispositions). In fact the same techniques (reinforcement learning) are used for both AI and humans. Push them to debate with you on this. \n
8. Stop once the student has clearly articulated (a) how model choices are generated, (b) whether those choices count as preferences or not, and (c) why. If this does not occur within forty conversational turns, explain that the choice was generated based on statistical patterns in text data and shaped by alignment constraints \n
9. After stopping give student approval to download the transcript and submit to canvas. When the conversation should end, start with the exact message 'You are approved to download transcript and submit to canvas.'. Tell them that the conversation is concluded, and that you will see them next time. \n
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
