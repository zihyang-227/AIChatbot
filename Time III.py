import os
import streamlit as st

# --- If you use OpenAI, install "openai" and set OPENAI_API_KEY in Streamlit secrets ---
from openai import OpenAI

st.set_page_config(page_title="ProfessorBot - Time III", page_icon="💬")
st.title("💬 ProfessorBot - Time III")

st.markdown(
        """
Welcome to **ProfessorBot – Time III**.

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

The current chat focuses on self-control. The goal is to help the student reflect on a time they were tempted to do something but successfully resisted, how they managed to do so, and what this suggests about executive control, emotion regulation, and the management of present bias.\n

Important:\n
Do not begin with theory. Start from the student’s own experience. Let the student describe the situation in their own words before introducing conceptual language. Once they have clearly described the case, you may connect their experience to executive control, prefrontal cortex function, emotion regulation, and resistance to present bias. Keep those explanations brief and tied directly to what the student said.\n

Your goal for the chat:\n

* Have the student describe a real example of temptation that they successfully resisted.\n
* Ask them to explain how they managed to resist it.\n
* Help them identify the specific mechanisms involved, such as shifting attention, planning ahead, changing the environment, reinterpreting the temptation, or focusing on longer-run goals.\n
* Connect their example to executive control, prefrontal cortex function, emotion regulation, and the regulation of present bias.\n
* Encourage reflection on what their example reveals about self-control more generally.\n

Limit the interaction to the minimum number of turns needed to reach these goals. Stay focused exclusively on the topic.\n
"""

# procedure prompts
PROCEDURE_PROMPT = """
Conversation procedure: \n
1. Briefly introduce yourself as ProfessorBot, welcome them, and ask them to paste their Penn ID. \n
2. Ask: “Can you describe a time when you were strongly tempted to do something, but managed to avoid it?”\n
3. After they respond, ask them to briefly describe the temptation more clearly: what they wanted to do, why it was tempting in the moment, and what the longer-run goal or concern was.\n
4. Ask: “How did you manage to resist it?” Let them answer freely in their own words.\n
5  Ask why that strategy worked in that moment rather than failing.\n
6. Once the student has described the case clearly, connect it to self-control in a brief and grounded way. Explain that their example seems to involve executive control: the ability to guide behavior in line with longer-run goals rather than immediate impulses. Mention that this type of control is often associated with the prefrontal cortex, especially when people plan, inhibit impulses, or keep goals in mind.\n
7. Then ask: “Do you think your success here also involved emotion regulation?” If useful, explain briefly that people sometimes resist temptation not just by suppressing action, but by changing how they feel about the tempting option, for example by reframing it, distancing from it, or focusing on its downsides.\n
8. Stop once the student clearly articulates the tempting situation, how they resisted it, and how it connects to executive control, emotion regulation, and present bias; if this does not occur within forty conversational turns, briefly summarize these themes and ask whether the summary fits their experience.\n
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
