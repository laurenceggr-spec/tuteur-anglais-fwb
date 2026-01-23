import streamlit as st
import PyPDF2
import pandas as pd
from datetime import datetime

# 1. Configuration et Sécurité
st.set_page_config(page_title="English Lab FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# Initialisation du stockage temporaire des scores (Simulé)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "scores_db" not in st.session_state:
    st.session_state.scores_db = []

# --- ECRAN DE CONNEXION ---
if not st.session_state.authenticated:
    st.title("🚀 English Lab FWB - Plateforme Pro")
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Connexion")
        role = st.radio("Je suis :", ["Élève", "Professeur"])
        password = st.text_input("Code d'accès :", type="password", help="Élève: ELEC2024 | Prof: ADMIN123")
        
        if st.button("Lancer l'application"):
            if role == "Élève" and password == "ELEC2024":
                st.session_state.authenticated = True
                st.session_state.role = "Élève"
                st.rerun()
            elif role == "Professeur" and password == "ADMIN123":
                st.session_state.authenticated = True
                st.session_state.role = "Professeur"
                st.rerun()
            else:
                st.error("Code erroné. Veuillez vérifier vos accès.")
    
    with col2:
        st.info("**Note aux enseignants :** Cette plateforme est conforme aux socles de compétences FWB. Elle utilise l'IA pour l'évaluation formative orale.")

# --- DASHBOARD PROFESSEUR ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Espace Enseignant")
    if st.button("⬅️ Déconnexion"):
        st.session_state.authenticated = False
        st.rerun()
        
    st.subheader("Suivi des sessions en temps réel")
    if st.session_state.scores_db:
        df = pd.DataFrame(st.session_state.scores_db)
        st.dataframe(df, use_container_width=True)
        st.download_button("Exporter en CSV (Excel)", df.to_csv(index=False), "resultats_classe.csv")
    else:
        st.write("Aucune session terminée pour le moment.")

# --- INTERFACE ÉLÈVE (LABORATOIRE) ---
else:
    with st.sidebar:
        st.header("👤 Session Élève")
        user_name = st.text_input("Prénom & Nom :", placeholder="Ex: Lucas M.")
        ai_persona = st.text_input("L'IA incarne :", value="Friendly Teacher")
        
        st.divider()
        st.subheader("⚙️ Réglages Prof")
        conv_mode = st.radio("Mode :", ["Tuteur IA (Interactif)", "Monologue", "Dialogue élèves"])
        timer_mins = st.slider("Chrono (min) :", 1, 15, 5)
        voice_speed = st.slider("Vitesse voix :", 0.5, 1.2, 0.8)

        uploaded_file = st.file_uploader("Charger Lexique PDF", type="pdf")
        pdf_words = ""
        if uploaded_file:
            reader = PyPDF2.PdfReader(uploaded_file)
            pdf_words = " ".join([p.extract_text() for p in reader.pages])
                
        target_vocab = st.text_input("Mots cibles additionnels :", placeholder="word1, word2...")
        target_grammar = st.text_input("Grammaire cible :", placeholder="ex: Present Perfect")
        
        if st.button("🚪 Quitter"):
            st.session_state.authenticated = False
            st.rerun()

    # Préparation du vocabulaire cible (Checklist)
    vocab_list = list(set([w.strip().lower() for w in (target_vocab + "," + pdf_words[:500]).split(",") if len(w.strip()) > 3]))
    vocab_json = str(vocab_list).replace("'", '"')

    # Interface HTML / JS Gamifiée
    part1 = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            :root { --p: #2C3E50; --s: #3498DB; --bg: #F4F7F6; --err: #E74C3C; --ok: #27AE60; --gold: #F1C40F; }
            body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; padding: 0; height: 100vh; overflow:hidden; }
            .app { width: 100%; max-width: 700px; margin: auto; background: white; height: 100vh; display: flex; flex-direction: column; }
            header { background: var(--p); color: white; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; }
            .settings-bar { padding: 10px; background: #eee; border-bottom: 1px solid #ddd; }
            .challenge-box { background: #FEF9E7; padding: 8px; border: 1px dashed var(--gold); border-radius: 5px; font-size: 0.8rem; text-align: center; font-weight: bold; margin-bottom: 5px; }
            .topics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; padding: 8px; background: #fff; border-bottom: 1px solid #ddd; }
            .t-btn { font-size: 0.65rem; padding: 6px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: white; text-align: center; }
            .t-btn.active { background: var(--s); color: white; }
            .vocab-check { padding: 8px; background: #f9f9f9; display: flex; flex-wrap: wrap; gap: 5px; max-height: 70px; overflow-y: auto; border-bottom: 1px solid #ddd; }
            .v-badge { padding: 3px 8px; border-radius: 10px; background: #ddd; color: #777; font-size: 0.7rem; }
            .v-badge.found { background: var(--ok); color: white; transform: scale(1.05); }
            #chat { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }
            .msg { max-width: 80%; padding: 10px 15px; border-radius: 15px; font-size: 0.95rem; }
            .user { align-self: flex-end; background: var(--s); color: white; }
            .ai { align-self: flex-start; background: white; border: 1px solid #ddd; }
            .controls { padding: 15px; text-align: center; background: white; border-top: 1px solid #eee; display: flex; align-items: center; justify-content: space-between; padding-bottom: 30px; }
            #mic { width: 60px; height: 60px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 1.5rem; cursor: pointer; }
            #mic.listening { background: var(--ok); animation: pulse 1.5s infinite; }
            @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(39,174,96, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(39,174,96, 0); } }
        </style>
    </head>
    <body>
    <div class="app">
        <header><b>English Lab Pro</b> <div id="timer-display">--:--</div></header>
        <div class="settings-bar">
            <div class="challenge-box" id="challenge-txt">Challenge: Use "HELLO" (+50 pts)</div>
        </div>
        <div class="topics" id="t-grid"></div>
        <div class="vocab-check" id="vocab-display"></div>
        <div id="chat"><div class="msg ai">Ready to start, student! Click the mic.</div></div>
        <div class="controls">
            <button id="mic">🎤</button>
            <div style="text-align:right">⭐ <span id="score-val">0</span></div>
        </div>
    </div>
    <script>
    """

    part2 = f"""
        const API_KEY = "{api_key}";
        const USER_NAME = "{user_name or 'Élève'}";
        const PERSONA = "{ai_persona}";
        const MODE = "{conv_mode}";
        const LIMIT_TIME = {timer_mins} * 60;
        const VOICE_SPEED = {voice_speed};
        const VOCAB_TARGETS = {vocab_json};
        const GRAMMAR_TARGET = "{target_grammar}";
    """

    part3 = """
        let score = 0; let history = []; let fullTranscript = ""; 
        let timeLeft = LIMIT_TIME; let timerActive = false;
        let foundVocab = new Set(); let challengeWord = "hello";

        const FIELDS = [
            { n: 'Identity', e: '👤', w: 'name, age, family' }, { n: 'House', e: '🏠', w: 'kitchen, bedroom, garden' }, 
            { n: 'Hobbies', e: '⚽', w: 'football, music, swimming' }, { n: 'Food', e: '🍕', w: 'apple, lunch, hungry' },
            { n: 'Shopping', e: '🛍️', w: 'buy, price, money' }, { n: 'Health', e: '🍎', w: 'doctor, headache, fruit' },
            { n: 'Travel', e: '🚲', w: 'train, hotel, ticket' }, { n: 'Time', e: '⏰', w: 'morning, monday, night' }
        ];

        const grid = document.getElementById('t-grid');
        FIELDS.forEach(f => {
            const b = document.createElement('button'); b.className = "t-btn"; b.innerHTML = f.e + "<br>" + f.n;
            b.onclick = () => {
                const words = f.w.split(', ');
                challengeWord = words[Math.floor(Math.random() * words.length)];
                document.getElementById('challenge-txt').innerText = "Challenge: Use \\"" + challengeWord.toUpperCase() + "\\" (+50 pts)";
                document.querySelectorAll('.t-btn').forEach(x => x.classList.remove('active'));
                b.classList.add('active');
            };
            grid.appendChild(b);
        });

        const vDisplay = document.getElementById('vocab-display');
        VOCAB_TARGETS.forEach(w => {
            const s = document.createElement('span'); s.className = 'v-badge'; s.id = 'v-' + w; s.innerText = w;
            vDisplay.appendChild(s);
        });

        const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
        const rec = new Speech(); rec.lang = 'en-US';

        document.getElementById('mic').onclick = () => { startTimer(); try { rec.start(); } catch(e) { rec.stop(); } };
        rec.onstart = () => document.getElementById('mic').classList.add('listening');
        rec.onend = () => { 
            document.getElementById('mic').classList.remove('listening'); 
            if (timerActive && MODE !== "Tuteur IA (Interactif)") setTimeout(() => { try{rec.start();}catch(e){} }, 600);
        };
        rec.onresult = (e) => { processInput(e.results[0][0].transcript); };

        function processInput(text) {
            const bRow = document.createElement('div'); bRow.className = "msg user"; bRow.innerText = text;
            document.getElementById('chat').appendChild(bRow);
            fullTranscript += USER_NAME + ": " + text + "\\n";
            
            let bonus = 0;
            if (text.toLowerCase().includes(challengeWord.toLowerCase())) bonus += 50;
            VOCAB_TARGETS.forEach(w => {
                if (text.toLowerCase().includes(w) && !foundVocab.has(w)) {
                    foundVocab.add(w); document.getElementById('v-' + w).classList.add('found'); bonus += 30;
                }
            });
            score += (10 + bonus);
            document.getElementById('score-val').innerText = score;
            if (MODE === "Tuteur IA (Interactif)") callAI(text);
        }

        async function callAI(text) {
            const prompt = `Role: ${PERSONA}. Level: A2. Goal: Oral Practice. Grammar: ${GRAMMAR_TARGET}. 1 sentence response + 1 question. Student: ${USER_NAME}.`;
            const r = await fetch('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY },
                body: JSON.stringify({ model: "gpt-4o-mini", messages: [{role:"system", content: prompt}, ...history, {role:"user", content: text}] })
            });
            const d = await r.json(); const reply = d.choices[0].message.content;
            const aiRow = document.createElement('div'); aiRow.className = "msg ai"; aiRow.innerText = reply;
            document.getElementById('chat').appendChild(aiRow);
            fullTranscript += PERSONA + ": " + reply + "\\n\\n";
            const u = new SpeechSynthesisUtterance(reply); u.lang = 'en-US'; u.rate = VOICE_SPEED; window.speechSynthesis.speak(u);
            history.push({role:"user", content:text}, {role:"assistant", content:reply});
        }

        function startTimer() {
            if (timerActive) return; timerActive = true;
            const interval = setInterval(() => {
                timeLeft--;
                document.getElementById('timer-display').innerText = Math.floor(timeLeft/60) + ":" + (timeLeft%60 < 10 ? "0" : "") + (timeLeft%60);
                if (timeLeft <= 0) { clearInterval(interval); stopSession(); }
            }, 1000);
        }

        async function stopSession() {
            timerActive = false; rec.stop();
            alert("Session terminée ! Analyse en cours...");
            // Logique de téléchargement du rapport .txt (comme précédemment)
        }
    </script>
    </body>
    </html>
    """
    st.components.v1.html(part1 + part2 + part3, height=800)
