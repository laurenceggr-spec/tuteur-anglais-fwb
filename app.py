import streamlit as st
import tempfile
import os

# --- VÉRIFICATION DES LIBRAIRIES ---
try:
    from openai import OpenAI
    from gtts import gTTS
except ImportError:
    st.error("⚠️ Il manque les librairies 'openai' et 'gTTS'.")
    st.stop()

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="English Buddy AI", page_icon="🇬🇧")

st.title("🇬🇧 English Buddy")
st.caption("Ton prof d'anglais propulsé par OpenAI 🧠")

# --- BARRE LATÉRALE (RÉGLAGES & DÉFIS) ---
with st.sidebar:
    st.header("⚙️ Réglages")
    api_key = st.text_input("Clé API OpenAI (sk-...)", type="password", help="Colle ta clé ici")
    
    st.divider()
    
    st.header("🎯 Défis du Prof")
    st.info("Configurez les contraintes pour l'élève.")
    
    target_vocab = st.text_input("Mots imposés", placeholder="ex: yesterday, happy")
    grammar_focus = st.selectbox("Focus Grammaire", 
                                 ["Aucun", "Passé (Past Simple)", "Futur (Will)", "Présent Continu (-ing)", "Questions"])
    
    if st.button("🗑️ Effacer l'historique"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am your English Buddy. Ready for the challenge?"}
        ]
        st.rerun()

# --- INITIALISATION CLIENT OPENAI ---
client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Erreur de clé : {e}")

# --- HISTORIQUE DE CONVERSATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your English Buddy. Ready for the challenge?"}
    ]

# --- AFFICHAGE DES MESSAGES ---
for msg in st.session_state.messages:
    role_display = "user" if msg["role"] == "user" else "assistant"
    avatar = "🧑‍🎓" if role_display == "user" else "🤖"
    
    with st.chat_message(role_display, avatar=avatar):
        st.write(msg["content"])
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# --- ZONE DE SAISIE ET TRAITEMENT ---
user_input = st.chat_input("Réponds en anglais ici...")

if user_input:
    # 1. Afficher le message utilisateur
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.write(user_input)

    # 2. Préparer la réponse
    response_text = ""
    audio_path = None

    if not client:
        response_text = "Please enter your OpenAI API Key in the sidebar first! 🔑"
    else:
        try:
            # Construction du Prompt avec les contraintes (Le "Cerveau")
            constraint_text = ""
            if target_vocab:
                constraint_text += f"The student MUST try to use these words: [{target_vocab}]. Check if they used them. "
            if grammar_focus != "Aucun":
                constraint_text += f"The student SHOULD practice this grammar: [{grammar_focus}]. "

            system_prompt = f"""
            Act as a supportive English tutor for a child.
            TEACHER MISSION (Constraints): {constraint_text}
            
            Instructions:
            1. Reply in simple English (A1/A2 level).
            2. Keep it short (max 25 words).
            3. ALWAYS ask a follow-up question.
            4. If constraints are set:
               - If student used the required words/grammar, PRAISE them explicitly (e.g. "Great use of 'yesterday'!").
               - If student missed them, gently nudge them.
            5. Correct huge mistakes gently.
            """

            # Appel à l'IA
            response = client.chat.completions.create(
                model="gpt-4o-mini", # Ou gpt-3.5-turbo
                messages=[
                    {"role": "system", "content": system_prompt},
                    # On envoie les 4 derniers messages pour garder le contexte sans trop dépenser
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-4:]],
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7
            )
            response_text = response.choices[0].message.content

            # Génération Audio (TTS)
            tts = gTTS(text=response_text, lang='en')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tts.save(fp.name)
                audio_path = fp.name

        except Exception as e:
            response_text = f"Sorry, error connecting to OpenAI: {e}"

    # 3. Afficher la réponse de l'IA
    with st.chat_message("assistant", avatar="🤖"):
        st.write(response_text)
        if audio_path:
            st.audio(audio_path, format="audio/mp3")

    # 4. Sauvegarder
    msg_data = {"role": "assistant", "content": response_text}
    if audio_path:
        msg_data["audio"] = audio_path
    st.session_state.messages.append(msg_data)
