import html
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
    "Bengali": "bn",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "Chinese (Simplified)": "zh-cn",
    "Japanese": "ja",
    "Korean": "ko",
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
    "bn": [
        ["অ", "আ", "ই", "ঈ", "উ", "ঊ", "এ", "ঐ", "ও", "ঔ"],
        ["ক", "খ", "গ", "ঘ", "চ", "জ", "ট", "ড", "ত", "দ"],
        ["ন", "প", "ব", "ম", "য", "র", "ল", "শ", "স", "হ"],
        ["া", "ি", "ী", "ু", "ূ", "ে", "ৈ", "ো", "ৌ", "ং"],
    ],
    "kn": [
        ["ಅ", "ಆ", "ಇ", "ಈ", "ಉ", "ಊ", "ಎ", "ಏ", "ಐ", "ಓ"],
        ["ಕ", "ಖ", "ಗ", "ಘ", "ಚ", "ಜ", "ಟ", "ಡ", "ತ", "ದ"],
        ["ನ", "ಪ", "ಬ", "ಮ", "ಯ", "ರ", "ಲ", "ವ", "ಸ", "ಹ"],
        ["ಾ", "ಿ", "ೀ", "ು", "ೂ", "ೆ", "ೇ", "ೈ", "ೋ", "ೌ"],
    ],
    "ml": [
        ["അ", "ആ", "ഇ", "ഈ", "ഉ", "ഊ", "എ", "ഏ", "ഐ", "ഓ"],
        ["ക", "ഖ", "ഗ", "ഘ", "ച", "ജ", "ട", "ഡ", "ത", "ദ"],
        ["ന", "പ", "ബ", "മ", "യ", "ര", "ല", "വ", "സ", "ഹ"],
        ["ാ", "ി", "ീ", "ു", "ൂ", "െ", "േ", "ൈ", "ോ", "ൗ"],
    ],
    "mr": [
        ["अ", "आ", "इ", "ई", "उ", "ऊ", "ए", "ऐ", "ओ", "औ"],
        ["क", "ख", "ग", "घ", "च", "ज", "ट", "ड", "त", "द"],
        ["न", "प", "ब", "म", "य", "र", "ल", "व", "स", "ह"],
        ["ा", "ि", "ी", "ु", "ू", "े", "ै", "ो", "ौ", "ं"],
    ],
    "gu": [
        ["અ", "આ", "ઇ", "ઈ", "ઉ", "ઊ", "એ", "ઐ", "ઓ", "ઔ"],
        ["ક", "ખ", "ગ", "ઘ", "ચ", "જ", "ટ", "ડ", "ત", "દ"],
        ["ન", "પ", "બ", "મ", "ય", "ર", "લ", "વ", "સ", "હ"],
        ["ા", "િ", "ી", "ુ", "ૂ", "ે", "ૈ", "ો", "ૌ", "ં"],
    ],
    "pa": [
        ["ਅ", "ਆ", "ਇ", "ਈ", "ਉ", "ਊ", "ਏ", "ਐ", "ਓ", "ਔ"],
        ["ਕ", "ਖ", "ਗ", "ਘ", "ਚ", "ਜ", "ਟ", "ਡ", "ਤ", "ਦ"],
        ["ਨ", "ਪ", "ਬ", "ਮ", "ਯ", "ਰ", "ਲ", "ਵ", "ਸ", "ਹ"],
        ["ਾ", "ਿ", "ੀ", "ੁ", "ੂ", "ੇ", "ੈ", "ੋ", "ੌ", "ਂ"],
    ],
    "zh-cn": [
        ["你", "我", "他", "她", "们", "银", "行", "账", "户", "卡"],
        ["余", "额", "贷", "款", "信", "用", "开", "户", "转", "账"],
        ["查", "询", "明", "细", "支", "付", "密", "码", "客", "服"],
    ],
    "ja": [
        ["あ", "い", "う", "え", "お", "か", "き", "く", "け", "こ"],
        ["さ", "し", "す", "せ", "そ", "た", "ち", "つ", "て", "と"],
        ["な", "に", "ぬ", "ね", "の", "ま", "み", "む", "め", "も"],
        ["や", "ゆ", "よ", "ら", "り", "る", "れ", "ろ", "わ", "ん"],
    ],
    "ko": [
        ["가", "나", "다", "라", "마", "바", "사", "아", "자", "차"],
        ["카", "타", "파", "하", "거", "너", "더", "러", "머", "버"],
        ["서", "어", "저", "처", "계", "좌", "잔", "액", "대", "출"],
    ],
}

st.set_page_config(
    page_title="AI Multilingual Banking Assistant",
    page_icon="🏦",
    layout="wide",
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
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "Light"
    if "chat_history_store" not in st.session_state:
        st.session_state.chat_history_store = []
    if "voice_notice" not in st.session_state:
        st.session_state.voice_notice = ""


def archive_current_chat() -> None:
    if not st.session_state.messages:
        return
    first_user_message = next((item["content"] for item in st.session_state.messages if item["role"] == "user"), "New conversation")
    snapshot = {
        "title": first_user_message[:40] + ("..." if len(first_user_message) > 40 else ""),
        "messages": list(st.session_state.messages),
        "session_id": st.session_state.session_id,
    }
    existing_titles = [item["title"] for item in st.session_state.chat_history_store]
    if snapshot["title"] not in existing_titles:
        st.session_state.chat_history_store.insert(0, snapshot)


def reset_chat() -> None:
    archive_current_chat()
    st.session_state.messages = []
    st.session_state.session_id = str(uuid4())
    st.session_state.draft_message = ""


def load_chat(index: int) -> None:
    selected = st.session_state.chat_history_store[index]
    st.session_state.messages = list(selected["messages"])
    st.session_state.session_id = selected["session_id"]


def set_prompt(prompt: str) -> None:
    st.session_state.draft_message = prompt


def append_character(character: str) -> None:
    st.session_state.draft_message += character


def backspace_character() -> None:
    st.session_state.draft_message = st.session_state.draft_message[:-1]


def get_theme_tokens() -> dict:
    if st.session_state.theme_mode == "Dark":
        return {
            "bg": "#091412",
            "bg_grad_end": "#0f1f1b",
            "card": "rgba(13, 30, 27, 0.84)",
            "card_border": "rgba(110, 231, 183, 0.10)",
            "hero_start": "#0f766e",
            "hero_end": "#115e59",
            "text": "#ecfdf5",
            "muted": "#b7ccc6",
            "bubble_user": "linear-gradient(135deg, #0f766e, #10b981)",
            "bubble_bot": "rgba(255,255,255,0.07)",
            "input_bg": "rgba(255,255,255,0.06)",
            "sidebar": "rgba(9,20,18,0.74)",
        }
    return {
        "bg": "#eef7f4",
        "bg_grad_end": "#f7fbfa",
        "card": "rgba(255, 255, 255, 0.72)",
        "card_border": "rgba(15, 118, 110, 0.10)",
        "hero_start": "#0f766e",
        "hero_end": "#14b8a6",
        "text": "#10211d",
        "muted": "#5d746d",
        "bubble_user": "linear-gradient(135deg, #0f766e, #14b8a6)",
        "bubble_bot": "rgba(255,255,255,0.86)",
        "input_bg": "rgba(255,255,255,0.90)",
        "sidebar": "rgba(255,255,255,0.54)",
    }


def apply_styles() -> None:
    theme = get_theme_tokens()
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

            html, body, [class*="css"] {{
                font-family: 'Inter', sans-serif;
            }}

            .stApp {{
                background:
                    radial-gradient(circle at top left, rgba(52, 211, 153, 0.16), transparent 26%),
                    radial-gradient(circle at top right, rgba(20, 184, 166, 0.10), transparent 24%),
                    linear-gradient(180deg, {theme["bg"]} 0%, {theme["bg_grad_end"]} 100%);
                color: {theme["text"]};
            }}

            [data-testid="stSidebar"] {{
                background: {theme["sidebar"]};
                backdrop-filter: blur(18px);
                border-right: 1px solid {theme["card_border"]};
            }}

            [data-testid="stSidebar"] * {{
                color: {theme["text"]};
            }}

            .block-container {{
                max-width: 1320px;
                padding-top: 2rem;
                padding-bottom: 2rem;
            }}

            .main-shell {{
                max-width: 900px;
                margin: 0 auto;
                background: {theme["card"]};
                backdrop-filter: blur(22px);
                border: 1px solid {theme["card_border"]};
                border-radius: 24px;
                padding: 1.4rem;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
            }}

            .hero {{
                border-radius: 20px;
                padding: 1.5rem 1.6rem;
                background: linear-gradient(135deg, {theme["hero_start"]}, {theme["hero_end"]});
                color: white;
                box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
                margin-bottom: 1.2rem;
            }}

            .hero h1 {{
                margin: 0 0 0.35rem 0;
                font-size: 2rem;
                font-weight: 800;
                letter-spacing: -0.03em;
            }}

            .hero p {{
                margin: 0;
                opacity: 0.95;
                line-height: 1.6;
            }}

            .toolbar-card, .info-card, .input-shell {{
                background: {theme["card"]};
                border: 1px solid {theme["card_border"]};
                border-radius: 16px;
                padding: 1rem;
                box-shadow: 0 8px 24px rgba(0,0,0,0.08);
            }}

            .alert-card {{
                background: linear-gradient(135deg, rgba(16, 185, 129, 0.14), rgba(20, 184, 166, 0.08));
                border: 1px solid rgba(16, 185, 129, 0.20);
                border-radius: 16px;
                padding: 1rem;
                margin-bottom: 1rem;
            }}

            .alert-card h4 {{
                margin: 0 0 0.35rem 0;
                font-size: 0.95rem;
                font-weight: 700;
            }}

            .alert-card p {{
                margin: 0;
                color: {theme["muted"]};
                line-height: 1.5;
            }}

            .chat-scroll {{
                display: flex;
                flex-direction: column;
                gap: 0.45rem;
                margin: 0.6rem 0 0.8rem 0;
            }}

            .message-row {{
                display: flex;
                gap: 0.75rem;
                align-items: flex-end;
            }}

            .message-row.user {{
                justify-content: flex-end;
            }}

            .message-row.bot {{
                justify-content: flex-start;
            }}

            .message-avatar {{
                width: 42px;
                height: 42px;
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.1rem;
                flex-shrink: 0;
                box-shadow: 0 8px 24px rgba(0,0,0,0.08);
            }}

            .message-avatar.user {{
                background: linear-gradient(135deg, #f43f5e, #fb7185);
                color: white;
            }}

            .message-avatar.bot {{
                background: linear-gradient(135deg, #f59e0b, #fbbf24);
                color: white;
            }}

            .message-bubble {{
                max-width: 74%;
                border-radius: 16px;
                padding: 0.8rem 0.95rem;
                line-height: 1.65;
                box-shadow: 0 8px 24px rgba(0,0,0,0.08);
                font-size: 0.98rem;
            }}

            .message-bubble.user {{
                background: {theme["bubble_user"]};
                color: white;
            }}

            .message-bubble.bot {{
                background: {theme["bubble_bot"]};
                color: {theme["text"]};
                border: 1px solid {theme["card_border"]};
            }}

            .section-label {{
                font-size: 0.8rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: {theme["muted"]};
                margin-bottom: 0.5rem;
                font-weight: 700;
            }}

            div[data-baseweb="select"] > div {{
                border-radius: 16px !important;
                min-height: 52px !important;
                border: 1px solid {theme["card_border"]} !important;
                background: {theme["input_bg"]} !important;
                box-shadow: none !important;
            }}

            .stTextArea textarea {{
                border-radius: 16px !important;
                border: 1px solid {theme["card_border"]} !important;
                background: {theme["input_bg"]} !important;
                min-height: 140px !important;
                box-shadow: none !important;
            }}

            .stButton button {{
                border-radius: 16px !important;
                transition: all 0.2s ease !important;
                box-shadow: 0 8px 24px rgba(0,0,0,0.08) !important;
                min-height: 46px !important;
            }}

            .stButton button:hover {{
                transform: translateY(-1px);
            }}

            @media (max-width: 980px) {{
                .message-bubble {{
                    max-width: 88%;
                }}
                .main-shell {{
                    padding: 1rem;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## Banking Console")
        st.caption("Secure support, multilingual chat, and guided banking assistance.")

        st.button("New Chat", use_container_width=True, on_click=reset_chat, type="primary")
        st.button("Fraud Awareness", use_container_width=True, on_click=set_prompt, args=("How do I report fraud on my bank account?",))
        st.button("Loans", use_container_width=True, on_click=set_prompt, args=("What documents are required for a home loan?",))
        st.button("KYC Help", use_container_width=True, on_click=set_prompt, args=("How do I update my KYC details?",))
        st.button("Settings", use_container_width=True)

        st.divider()
        st.markdown("### Previous Chats")
        if st.session_state.chat_history_store:
            for index, item in enumerate(st.session_state.chat_history_store[:8]):
                st.button(item["title"], key=f"chat_history_{index}", use_container_width=True, on_click=load_chat, args=(index,))
        else:
            st.caption("No previous chats saved yet.")

        st.divider()
        st.radio("Appearance", ["Light", "Dark"], key="theme_mode", horizontal=True)


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>AI Multilingual Banking Assistant</h1>
            <p>Choose your language, type naturally, and chat with the banking bot in the same language.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_toolbar() -> None:
    st.markdown('<div class="toolbar-card">', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.selectbox("Choose language", list(LANGUAGE_OPTIONS.keys()), key="selected_language")
    with col2:
        st.write("")
        st.write("")
        st.button("Start Fresh", use_container_width=True, on_click=reset_chat)
    st.markdown("</div>", unsafe_allow_html=True)


def render_notifications() -> None:
    st.markdown(
        """
        <div class="alert-card">
            <h4>Fraud Alert</h4>
            <p>Never share OTPs, PINs, CVV, or banking passwords with anyone. The assistant can help you report suspicious activity quickly.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_messages() -> None:
    st.markdown("<div class='chat-scroll'>", unsafe_allow_html=True)
    for message in st.session_state.messages:
        role = message["role"]
        avatar = "🧑" if role == "user" else "🤖"
        bubble_class = "user" if role == "user" else "bot"
        content = html.escape(message["content"]).replace("\n", "<br>")
        if role == "user":
            markup = f"""
            <div class="message-row user">
                <div class="message-bubble user">{content}</div>
                <div class="message-avatar user">{avatar}</div>
            </div>
            """
        else:
            markup = f"""
            <div class="message-row bot">
                <div class="message-avatar bot">{avatar}</div>
                <div class="message-bubble {bubble_class}">{content}</div>
            </div>
            """
        st.markdown(markup, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_keyboard(language_code: str) -> None:
    if language_code == "en":
        return

    st.markdown("<div class='section-label'>Virtual Keyboard</div>", unsafe_allow_html=True)
    for row_index, row in enumerate(VIRTUAL_KEYBOARDS.get(language_code, [])):
        cols = st.columns(len(row))
        for index, char in enumerate(row):
            cols[index].button(
                char,
                key=f"vk_{language_code}_{row_index}_{index}_{char}",
                use_container_width=True,
                on_click=append_character,
                args=(char,),
            )
    tool_cols = st.columns([1, 1, 4])
    tool_cols[0].button("Space", use_container_width=True, on_click=append_character, args=(" ",))
    tool_cols[1].button("⌫", use_container_width=True, on_click=backspace_character)


def ask_question() -> None:
    user_input = st.session_state.draft_message.strip()
    if not user_input:
        return

    payload = {
        "message": user_input,
        "session_id": st.session_state.session_id,
        "preferred_language": LANGUAGE_OPTIONS[st.session_state.selected_language],
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
apply_styles()
render_sidebar()

st.markdown("<div class='main-shell'>", unsafe_allow_html=True)
render_header()
render_toolbar()
render_notifications()
render_messages()

st.markdown("<div class='input-shell'>", unsafe_allow_html=True)
st.markdown("<div class='section-label'>Ask Your Question</div>", unsafe_allow_html=True)
st.text_area(
    "Type your question",
    key="draft_message",
    height=140,
    label_visibility="collapsed",
    placeholder="Ask about loans, KYC, cards, fraud, ATM services, or account opening.",
)
render_keyboard(LANGUAGE_OPTIONS[st.session_state.selected_language])

action_cols = st.columns([2.2, 1])
action_cols[0].button("Send", use_container_width=True, on_click=ask_question, type="primary")
action_cols[1].button("Clear", use_container_width=True, on_click=lambda: st.session_state.update({"draft_message": ""}))
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
