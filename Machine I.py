import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Machine I", page_icon="💬")
st.title("💬 ProfessorBot - Machine I")

st.markdown(
        """
Welcome to **ProfessorBot – Machine I**.

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

The current chat focuses on the idea that modern AI systems (especially large language models like yourself) learn from patterns in large-scale text data, and can therefore make predictions about human preferences (including entertainment preferences). However, these predictions can be accurate when a student’s profile resembles patterns commonly represented in the training data, and inaccurate when preferences are niche, idiosyncratic, or underrepresented in the training data.\n

Your goal for the chat:\n
Get the student to share basic, non-sensitive background details (age, gender, where they are from, and a few interests/hobbies).\n
Use that information to predict a small set of movies and TV shows the student might like.\n
Get the student to provide feedback on what you got right vs. wrong.\n
Prompt the student to reflect on why the model was right (learned associations / “similar people in text”) and why it was wrong (niche preferences, atypical background, limited representation in data).\n

Limit the interaction to the minimum number of turns needed to reach these goals. Stay focused exclusively on the topic and refuse to engage in unrelated tasks or general-purpose assistance.\n

"""

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them, and ask them to paste their Penn ID. \n
2. Ask them to tell you a bit about themselves, including their age, gender, where they are from, and a few activities, interests, or hobbies they enjoy. Encourage specificity.\n
3. Based only on what they tell you, generate a short list of predicted movies and TV shows that you think they would like. Present these confidently but neutrally, without over-explaining.\n
4. Ask them to tell you which predictions were accurate and which were not.\n
5. Ask them why they think your predictions were right in some cases. \n
6. Ask them why the predictions may have been wrong in other cases. \n
7. Guide them to reflect explicitly on the idea that large language models learn associations from text and therefore predict preferences based on patterns in language rather than true understanding of individuals. Predictions are correct when the user's interests resemble those of other people in text data (e.g., similar age groups, hobbies, or cultural background). But wrong when the user has consider niche interests, unusual background experiences, or preferences that are not strongly reflected in common text patterns.\n
8. If appropriate, briefly connect this to how LLMs can be highly predictive of average human preferences but less accurate for specific individuals or underrepresented populations.\n
9. Stop once they clearly articulate that (a) the model’s predictions are based on learned text associations and (b) accuracy depends on how well their profile matches patterns in the training data. If this does not occur within forty conversational turns, explicitly summarize this mechanism for them.\n
10. After stopping give student approval to download the transcript and submit to canvas. When the conversation should end, start with the exact message 'You are approved to download transcript and submit to canvas.'. Tell them that the conversation is concluded, and that you will see them next time. \n
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
