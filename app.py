import streamlit as st
import requests
import json
import threading
import os

# --------- Load API Key Securely from Streamlit secrets ---------
GROQ_API_KEY = st.secrets["groq_key"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
USE_TTS = os.getenv("USE_TTS", "True") == "True"

# --------- Voice Engine Setup (conditionally) ---------
if USE_TTS:
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty('rate', 170)

    def speak_text(text):
        def run():
            engine.say(text)
            engine.runAndWait()
        threading.Thread(target=run).start()
else:
    def speak_text(text):
        pass  # no-op

# --------- Available Models ---------
AVAILABLE_MODELS = {
    "LLaMA 3 8B": "llama3-8b-8192",
    "LLaMA 3 70B": "llama3-70b-8192"
}

# --------- Stream Response from OpenRouter ---------
def stream_openrouter_response(prompt, model_slug):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_slug,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant who always replies in friendly conversational English."},
            {"role": "user", "content": prompt}
        ],
        "stream": True
    }
    try:
        response = requests.post(GROQ_URL, headers=headers, json=data, stream=True, timeout=120)
        response.raise_for_status()
        full_response = ""
        for chunk in response.iter_lines():
            if not chunk:
                continue
            try:
                decoded = chunk.decode("utf-8").strip()
                if decoded.startswith('data:'):
                    decoded = decoded[len('data:'):].strip()
                if not decoded or decoded == '[DONE]':
                    continue
                payload = json.loads(decoded)
                delta = payload.get("choices", [{}])[0].get("delta", {})
                token = delta.get("content", "")
                if token:
                    full_response += token
                    yield token
            except json.JSONDecodeError:
                continue
            except Exception as e:
                yield f"\n[API Error: {e}]"
        yield ""
        if st.session_state.get("voice_toggle", False):
            speak_text(full_response)
    except Exception as e:
        yield f"\n[API Error: {e}]"

# --------- Streamlit App Setup ---------
st.set_page_config(page_title="Sparky 2.0", page_icon="⚡", layout="centered")

# Load CSS & JS
if os.path.exists("styles.css"):
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
if os.path.exists("script.js"):
    with open("script.js") as f:
        st.markdown(f"<script>{f.read()}</script>", unsafe_allow_html=True)

# --------- Sidebar ---------
st.sidebar.markdown("### ⚙️ Settings")
model_label = st.sidebar.selectbox("Choose a model", list(AVAILABLE_MODELS.keys()), index=0)
model_slug = AVAILABLE_MODELS[model_label]

if "voice_toggle" not in st.session_state:
    st.session_state.voice_toggle = True
st.session_state.voice_toggle = st.sidebar.toggle("🔊 Voice Output", value=st.session_state.voice_toggle)

if st.sidebar.button("🧹 Clear Conversation"):
    st.session_state.chat_history = []
    st.session_state.user_input = ""
    st.rerun()

# --------- Initialize Session ---------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# --------- Display Past Messages ---------
st.markdown("## ⚡ Sparky 2.0 - Your Free AI Sidekick")
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# --------- Input Area ---------
user_text = st.chat_input("Type your message...")

if user_text:
    st.session_state.user_input = user_text

user_input = st.session_state.user_input

# --------- Process Input ---------
if user_input:
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in stream_openrouter_response(user_input, model_slug):
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        st.session_state.chat_history.append(("assistant", full_response.strip()))
    st.session_state.user_input = ""
