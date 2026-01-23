import streamlit as st
import PyPDF2
import pandas as pd

# 1. Configuration et Sécurité
st.set_page_config(page_title="English Lab FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# --- SIMULATION BASE DE DONNÉES CENTRALE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "scores_db" not in st.session_state:
    st.session_state.scores_db = []
# Paramètres pilotés par le prof
if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "persona": "A friendly British teacher",
        "grammar": "Present Continuous",
        "vocab": "morning, breakfast, school",
        "mode": "Tuteur IA (Interactif)"
    }

# --- LOGIQUE DE RÉCEPTION DES RÉSULTATS ---
query_params = st.query_params
if "new_score" in query_params:
    st.session_state.scores_db.append({
        "Élève": query_params.get("student"),
        "Score": query_params.get("score"),
        "Mots": query_params.get("words"),
        "Date": pd.Timestamp.now().strftime("%d/%m %H:%M")
    })
    st.query_params.clear()

# --- ECRAN DE CONNEXION ---
if not st.session_state.authenticated:
    st.title("🚀 English Lab FWB - Plateforme Pro")
    role = st.radio("Je suis :", ["Élève", "Professeur"], horizontal=True)
    password = st.text_input("Code d'accès :", type="password")
    if st.button("Lancer la session"):
        if role == "Élève" and password == "ELEC2024":
            st.session_state.authenticated = True
            st.session_state.role = "Élève"
            st.rerun()
        elif role == "Professeur" and password == "ADMIN123":
            st.session_state.authenticated = True
            st.session_state.role = "Professeur"
            st.rerun()
        else:
            st.error("Code incorrect.")

# --- ESPACE PROFESSEUR (COMMANDE) ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Centre de Commande Enseignant")
    col_set, col_res = st.columns([1, 1.5])
    
    with col_set:
        st.subheader("📝 Configurer la leçon")
        with st.form("settings_form"):
            new_persona = st.text_input("Rôle de l'IA :", value=st.session_state.class_settings["persona"])
            new_grammar = st.text_input("Grammaire cible :", value=st.session_state.class_settings["grammar"])
            
            uploaded_file = st.file_uploader("Charger un lexique PDF :", type="pdf")
            new_vocab = st.text_area("Mots cibles (séparés par virgules) :", value=st.session_state.class_settings["vocab"])
            
            if st.form_submit_button("Mettre à jour pour toute la classe"):
                pdf_content = ""
                if uploaded_file:
                    reader = PyPDF2.PdfReader(uploaded_file)
                    pdf_content = ",".join([p.extract_text()[:200] for p in reader.pages])
                
                st.session_state.class_settings.update({
                    "persona": new_persona,
                    "grammar": new_grammar,
                    "vocab": new_vocab + "," + pdf_content
                })
                st.success("Consignes envoyées aux élèves !")

    with col_res:
        st.subheader("📊 Résultats en direct")
        if st.session_state.scores_db:
            df = pd.DataFrame(st.session_state.scores_db)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun élève n'a encore validé sa session.")
    
    if st.button("🚪 Déconnexion"):
        st.session_state.authenticated = False
        st.rerun()

# --- INTERFACE ÉLÈVE (ÉPURÉE) ---
else:
    st.title("🎯 English Training Session")
    user_name = st.sidebar.text_input("Entre ton Prénom & Nom :")
    
    if not user_name:
        st.warning("Veuillez entrer votre nom dans la barre latérale pour commencer.")
    else:
        # On récupère les consignes fixées par le prof
        settings = st.session_state.class_settings
        vocab_list = [w.strip().lower() for w in settings["vocab"].split(",") if len(w.strip()) > 3]
        vocab_json = str(vocab_list).replace("'", '"')

        part1 = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                :root { --p: #2C3E50; --s: #3498DB; --bg: #F4F7F6; --err: #E74C3C; --ok: #27AE60; }
                body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; }
                .app { width: 100%; max-width: 800px; margin: auto; background: white; height: 90vh; display: flex; flex-direction: column; border: 1px solid #ddd; border-radius: 10px; overflow: hidden; }
                header { background: var(--p); color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
                #chat { flex: 1; padding: 15px; overflow-y: auto; background: #fafafa; display: flex; flex-direction: column; gap: 10px; }
                .msg { max-width: 80%; padding: 12px; border-radius: 15px; }
                .user { align-self: flex-end; background: var(--s); color: white; }
                .ai { align-self: flex-start; background: #eee; }
                .controls { padding: 20px; border-top: 1px solid #ddd; display: flex; justify-content: space-around; align-items: center; }
                #mic { width: 60px; height: 60px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 1.5rem; cursor: pointer; }
                #mic.listening { background: var(--ok); animation: pulse 1.5s infinite; }
                .stop-btn { background: #E67E22; color: white; border: none; padding: 10px 25px; border-radius: 5px; cursor: pointer; font-weight: bold; }
                @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(39,174,96, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(39,174,96, 0); } }
            </style>
        </head>
        <body>
        <div class="app">
            <header><b>Lab Session</b> <div id="score-box">⭐ <span id="score-val">0</span></div></header>
            <div id="chat"><div class="msg ai">Welcome! I'm ready. Click the mic to speak.</div></div>
            <div class="controls">
                <button id="mic">🎤</button>
                <button class="stop-btn" id="stop-btn">FINISH & SEND</button>
            </div>
        </div>
        <script>
        """

        part2 = f"""
            const API_KEY = "{api_key}";
            const USER_NAME = "{user_name}";
            const PERSONA = "{settings['persona']}";
            const VOCAB_TARGETS = {vocab_json};
            const GRAMMAR_TARGET = "{settings['grammar']}";
        """

        part3 = """
            let score = 0; let history = []; let fullTranscript = ""; 
            let foundVocab = new Set();

            const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            rec.lang = 'en-US';

            document.getElementById('mic').onclick = () => { try { rec.start(); } catch(e) { rec.stop(); } };
            rec.onstart = () => document.getElementById('mic').classList.add('listening');
            rec.onend = () => document.getElementById('mic').classList.remove('listening');
            rec.onresult = (e) => { 
                const text = e.results[0][0].transcript;
                addMsg(text, 'user');
                fullTranscript += USER_NAME + ": " + text + "\\n";
                
                VOCAB_TARGETS.forEach(w => {
                    if (text.toLowerCase().includes(w) && !foundVocab.has(w)) {
                        foundVocab.add(w); score += 50;
                    }
                });
                score += 10;
                document.getElementById('score-val').innerText = score;
                callAI(text);
            };

            async function callAI(text) {
                const prompt = `Role: ${PERSONA}. Level: A2. Rule: 1 sentence + 1 question. Grammar: ${GRAMMAR_TARGET}. Student: ${USER_NAME}.`;
                const r = await fetch('https://api.openai.com/v1/chat/completions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY },
                    body: JSON.stringify({ model: "gpt-4o-mini", messages: [{role:"system", content: prompt}, ...history, {role:"user", content: text}] })
                });
                const d = await r.json(); const reply = d.choices[0].message.content;
                addMsg(reply, 'ai');
                fullTranscript += "Tutor: " + reply + "\\n\\n";
                const u = new SpeechSynthesisUtterance(reply); u.lang = 'en-US'; window.speechSynthesis.speak(u);
                history.push({role:"user", content:text}, {role:"assistant", content:reply});
            }

            document.getElementById('stop-btn').onclick = async () => {
                const params = new URLSearchParams({
                    new_score: "1",
                    student: USER_NAME,
                    score: score,
                    words: Array.from(foundVocab).join(', ')
                });
                window.parent.location.search = params.toString();
            };

            function addMsg(t, cl) {
                const b = document.getElementById('chat'); const d = document.createElement('div');
                d.className = "msg " + cl; d.innerText = t; b.appendChild(d); b.scrollTop = b.scrollHeight;
            }
        </script>
        </body>
        </html>
        """
        st.components.v1.html(part1 + part2 + part3, height=700)

    if st.sidebar.button("Déconnexion"):
        st.session_state.authenticated = False
        st.rerun()
