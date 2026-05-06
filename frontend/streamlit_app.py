import os
from uuid import uuid4

import requests
import streamlit as st

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")
CHAT_ENDPOINT = f"{BACKEND_BASE_URL}/chat"

LANGUAGE_OPTIONS = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
}

VIRTUAL_KEYBOARDS = {
    "hi": [
        ["अ", "आ", "इ", "ई", "उ", "ऊ", "ए", "ऐ", "ओ", "औ"],
        ["क", "ख", "ग", "घ", "च", "ज", "ट", "ड", "त", "द"],
        ["न", "प", "ब", "म", "य", "र", "ल", "व", "स", "ह"],
        ["ा", "ि", "ी", "ु", "ू", "े", "ै", "ो", "ौ", "ं"],
    ],
    "te": [
        ["అ", "ఆ", "ఇ", "ఈ", "ఉ", "ఊ", "ఎ", "ఏ", "ఐ", "ఓ"],
        ["క", "ఖ", "గ", "ఘ", "చ", "జ", "ట", "డ", "త", "ద"],
        ["న", "ప", "బ", "మ", "య", "ర", "ల", "వ", "స", "హ"],
        ["ా", "ి", "ీ", "ు", "ూ", "ె", "ే", "ై", "ో", "ౌ"],
    ],
    "ta": [
        ["அ", "ஆ", "இ", "ஈ", "உ", "ஊ", "எ", "ஏ", "ஐ", "ஓ"],
        ["க", "ச", "ஜ", "ட", "த", "ந", "ப", "ம", "ய", "ர"],
        ["ல", "வ", "ழ", "ள", "ற", "ன", "ங", "ஞ", "ண", "ஹ"],
        ["ா", "ி", "ீ", "ு", "ூ", "ெ", "ே", "ை", "ொ", "ோ"],
    ],
}

st.set_page_config(
    page_title="AI Multilingual Banking Assistant",
    page_icon="🏦",
    layout="centered",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Manrope', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(5, 150, 105, 0.15), transparent 30%),
                linear-gradient(180deg, #f7fbf8 0%, #eef8f5 45%, #ffffff 100%);
        }

        .hero {
            padding: 1.4rem 1.6rem;
            border-radius: 24px;
            background: linear-gradient(135deg, #065f46, #0f766e);
            color: white;
            box-shadow: 0 18px 48px rgba(15, 23, 42, 0.14);
            margin-bottom: 1rem;
        }

        .hero h1 {
            margin: 0 0 0.3rem 0;
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .hero p {
            margin: 0;
            opacity: 0.96;
        }

        .toolbar {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(15, 118, 110, 0.12);
            border-radius: 20px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        }

        .stChatMessage {
            border-radius: 18px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid4())
    if "draft_message" not in st.session_state:
        st.session_state.draft_message = ""
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "English"


def reset_chat() -> None:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid4())
    st.session_state.draft_message = ""


def append_character(character: str) -> None:
    st.session_state.draft_message += character


def backspace_character() -> None:
    st.session_state.draft_message = st.session_state.draft_message[:-1]


def render_keyboard(language_code: str) -> None:
    if language_code == "en":
        return

    st.caption("Virtual keyboard")
    for row_index, row in enumerate(VIRTUAL_KEYBOARDS.get(language_code, [])):
        columns = st.columns(len(row))
        for index, character in enumerate(row):
            columns[index].button(
                character,
                key=f"vk_{language_code}_{row_index}_{index}_{character}",
                use_container_width=True,
                on_click=append_character,
                args=(character,),
            )

    action_cols = st.columns([1, 1, 3])
    action_cols[0].button("Space", use_container_width=True, on_click=append_character, args=(" ",))
    action_cols[1].button("⌫", use_container_width=True, on_click=backspace_character)


def ask_question() -> None:
    user_input = st.session_state.draft_message.strip()
    if not user_input:
        return

    selected_language = st.session_state.selected_language
    payload = {
        "message": user_input,
        "session_id": st.session_state.session_id,
        "preferred_language": LANGUAGE_OPTIONS[selected_language],
    }

    st.session_state.messages.append({"role": "user", "content": user_input})

    try:
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        assistant_reply = data.get("response", "I could not generate a response.")
    except Exception as exc:
        assistant_reply = f"Could not reach the banking assistant: {exc}"

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    st.session_state.draft_message = ""


initialize_state()

st.markdown(
    """
    <div class="hero">
        <h1>AI Multilingual Banking Assistant</h1>
        <p>Choose your language, type naturally, and chat with the banking bot in that same language.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="toolbar">', unsafe_allow_html=True)
toolbar_col1, toolbar_col2 = st.columns([2, 1])
with toolbar_col1:
    selected_language = st.selectbox(
        "Choose language",
        list(LANGUAGE_OPTIONS.keys()),
        key="selected_language",
    )
with toolbar_col2:
    st.write("")
    st.write("")
    st.button("New Chat", use_container_width=True, on_click=reset_chat)
st.markdown("</div>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.text_area(
    "Type your question",
    key="draft_message",
    height=120,
    placeholder="Ask about loans, KYC, cards, fraud, ATM services, or account opening.",
)

render_keyboard(LANGUAGE_OPTIONS[selected_language])

send_col, clear_col = st.columns([3, 1])
send_col.button("Send", use_container_width=True, on_click=ask_question, type="primary")
clear_col.button("Clear", use_container_width=True, on_click=lambda: st.session_state.update({"draft_message": ""}))
