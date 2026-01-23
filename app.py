import streamlit as st
import tempfile
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="English Buddy (OpenAI)", page_icon="🇬🇧")
st.title("🇬🇧 English Buddy")
st.caption("Ton prof d'anglais propulsé par OpenAI 🧠")

# --- VÉRIFICATION DES LIBRAIRIES ---
try:
    from openai import OpenAI
    from gtts import gTTS
except ImportError as e:
    st.error("⚠️ Il manque des librairies !")
    st.info("Vérifiez que votre fichier requirements.txt contient : streamlit, openai, gTTS")
    st.stop()

# --- 1. GESTION DE LA CLÉ API OPENAI ---
api_key = st.sidebar.text_input("Clé API OpenAI (sk-...)", type="password", help="Colle ta clé OpenAI ici")

client = None
if api_key:
    try:
        # Initialisation du client OpenAI
        client = OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Erreur de clé : {e}")

# --- 2. HISTORIQUE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your English Buddy. What is your name?"}
    ]

# Afficher la conversation
for msg in st.session_state.messages:
    # On map 'assistant' pour l'affichage
    role_display = "user" if msg["role"] == "user" else "assistant"
    with st.chat_message(role_display):
        st.write(msg["content"])
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# --- 3. ZONE DE SAISIE ---
user_input = st.chat_input("Écris ta réponse ici en anglais...")

if user_input:
    # A. Afficher le message utilisateur
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # B. Générer la réponse (OpenAI)
    response_text = ""
    audio_path = None

    if not client:
        response_text = "Please enter your OpenAI API Key in the sidebar! 🔑"
    else:
        try:
            # Appel à GPT-4o-mini (Rapide et pas cher) ou gpt-3.5-turbo
            response = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[
                    {"role": "system", "content": """
                     Tu es un tuteur d'anglais bienveillant pour un enfant.
                     Réponds en anglais simple (A1/A2).
                     Fais des phrases courtes (max 25 mots).
                     Corrige gentiment les fautes.
                     Termine TOUJOURS par une question simple.
                     """},
                    # On inclut l'historique récent pour le contexte (optionnel, ici on met juste le dernier message pour économiser)
                    {"role": "user", "content": user_input}
                ]
            )
            response_text = response.choices[0].message.content

            # C. Générer l'audio (TTS)
            tts = gTTS(text=response_text, lang='en')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tts.save(fp.name)
                audio_path = fp.name

        except Exception as e:
            response_text = f"Sorry, error connecting to OpenAI: {e}"

    # D. Afficher la réponse
    with st.chat_message("assistant"):
        st.write(response_text)
        if audio_path:
            st.audio(audio_path, format="audio/mp3")

    # E. Sauvegarder
    msg_data = {"role": "assistant", "content": response_text}
    if audio_path:
        msg_data["audio"] = audio_path
    st.session_state.messages.append(msg_data)
