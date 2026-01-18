import streamlit as st
from openai import OpenAI

# 1. Configuration de la page
st.set_page_config(page_title="Tuteur Anglais FWB", page_icon="🇧🇪")
st.title("🇬🇧 English Speaking Partner")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 2. Initialisation de la mémoire (si elle n'existe pas encore)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": """
        Tu es un tuteur d'anglais bienveillant pour un élève belge (référentiel FWB). 
        Niveau : A1/A2. 
        Mission : Réponds en UNE phrase courte. 
        Si l'élève a fait une faute, corrige-le gentiment en disant 'You said... but it's better to say...'. 
        Termine toujours par une question simple pour continuer la conversation.
        Utilise un vocabulaire très simple (famille, école, loisirs).
        """}
    ]

# 3. Affichage de l'historique (optionnel, pour que l'élève voie la discussion)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 4. Interface Audio
audio_value = st.audio_input("Clique sur le micro et parle à ton tuteur :")

if audio_value:
    audio_value.name = "audio.wav"
    
    with st.spinner("Transcription..."):
        # A. Audio vers Texte
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_value
        )
        user_text = transcript.text
        
        # On ajoute le message de l'élève à l'historique
        st.session_state.messages.append({"role": "user", "content": user_text})
        
        # On affiche le texte immédiatement
        with st.chat_message("user"):
            st.markdown(user_text)

    with st.spinner("Le tuteur réfléchit..."):
        # B. Réponse de l'IA avec TOUT l'historique
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages
        )
        ai_message = response.choices[0].message.content
        
        # On ajoute la réponse de l'IA à l'historique
        st.session_state.messages.append({"role": "assistant", "content": ai_message})

        # On affiche la réponse
        with st.chat_message("assistant"):
            st.markdown(ai_message)

        # C. Synthèse Vocale
        speech_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=ai_message
        )
        st.audio(speech_response.content, autoplay=True)

# Bouton pour recommencer à zéro
if st.button("Recommencer la conversation"):
    st.session_state.messages = [st.session_state.messages[0]]
    st.rerun()
