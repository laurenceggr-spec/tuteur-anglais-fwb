import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import tempfile
import os

# Configuration de la page
st.set_page_config(page_title="English Buddy AI", page_icon="🇬🇧")

st.title("🇬🇧 English Buddy")
st.caption("Ton prof d'anglais personnel dans le cloud ☁️")

# --- 1. GESTION DE LA CLÉ API ---
# On regarde si la clé est dans les "secrets" de Streamlit ou saisie par l'utilisateur
api_key = st.sidebar.text_input("Clé API Google Gemini", type="password", help="Colle ta clé ici pour activer l'IA")

if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Erreur de clé : {e}")

# --- 2. HISTORIQUE DE CONVERSATION ---
# Streamlit recharge la page à chaque action, on doit sauvegarder l'historique
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your English Buddy. What is your name?"}
    ]

# Afficher l'historique des messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        # Si c'est un message de l'IA et qu'il a un audio associé (optionnel)
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# --- 3. ZONE DE SAISIE ---
user_input = st.chat_input("Écris ta réponse ici en anglais...")

if user_input:
    # A. Afficher le message de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # B. Générer la réponse de l'IA
    if not api_key:
        response_text = "Please enter your API Key in the sidebar to chat with me! 🤖"
    else:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Prompt pédagogique
            prompt = f"""
            Tu es un tuteur d'anglais bienveillant pour un enfant.
            L'élève dit : "{user_input}".
            Consignes :
            1. Réponds en anglais simple (Niveau A1/A2).
            2. Fais court (max 25 mots).
            3. Si grosse faute, corrige gentiment.
            4. Termine TOUJOURS par une question simple pour relancer.
            """
            response = model.generate_content(prompt)
            response_text = response.text
        except Exception as e:
            response_text = f"Sorry, I have a headache (Error: {e})"

    # C. Générer l'audio (TTS)
    # On crée un fichier temporaire pour le son
    try:
        tts = gTTS(text=response_text, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            audio_path = fp.name
    except Exception as e:
        audio_path = None
        st.error(f"Erreur Audio: {e}")

    # D. Afficher la réponse de l'IA
    with st.chat_message("assistant"):
        st.write(response_text)
        if audio_path:
            st.audio(audio_path, format="audio/mp3")

    # E. Sauvegarder dans l'historique
    message_data = {"role": "assistant", "content": response_text}
    if audio_path:
        # Note: Dans une vraie appli, il faudrait gérer le nettoyage des fichiers temp
        message_data["audio"] = audio_path
    
    st.session_state.messages.append(message_data)
