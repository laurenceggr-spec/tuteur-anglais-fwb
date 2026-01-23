import streamlit as st
import PyPDF2
import io

# 1. Configuration de la page
st.set_page_config(page_title="English Tutor FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("👤 Identification")
    user_name = st.text_input("Nom de l'élève :", placeholder="Ex: Jean Dupont")
    
    st.header("⚙️ Paramètres Pédagogiques")
    conv_mode = st.radio("Mode de conversation :", 
                         ["Tuteur IA (Interactif)", "Monologue (L'IA écoute)", "Dialogue entre élèves"])
    
    timer_mins = st.slider("Durée de la session (minutes) :", 1, 10, 3)
    voice_speed = st.slider("Vitesse de la voix IA :", 0.5, 1.5, 0.9, step=0.1)

    uploaded_file = st.file_uploader("Charger un lexique (PDF)", type="pdf")
    pdf_words = ""
    if uploaded_file:
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            pdf_words += page.extract_text()
            
    target_vocab = st.text_input("Mots-clés cibles :", placeholder="word1, word2...")
    target_grammar = st.text_input("Grammaire cible :", placeholder="ex: Passive voice")

combined_constraints = f"{target_vocab}, {pdf_words[:500]}".replace('"', '').replace('\n', ' ')

# 2. Interface HTML / JS
part1 = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root { --p: #2C3E50; --s: #3498DB; --bg: #F4F7F6; --err: #E74C3C; --ok: #27AE60; --gold: #F1C40F; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; padding: 0; height: 100vh; overflow:hidden; }
        .app { width: 100%; max-width: 600px; margin: auto; background: white; height: 100vh; display: flex; flex-direction: column; }
        header { background: var(--p); color: white; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; }
        .info-bar { background: #eee; padding: 8px; font-size: 0.8rem; display: flex; justify-content: space-around; border-bottom: 1px solid #ddd; }
        #chat { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }
        .msg { max-width: 85%; padding: 10px 15px; border-radius: 15px; font-size: 0.95rem; }
        .user { align-self: flex-end; background: var(--s); color: white; }
        .ai { align-self: flex-start; background: #e9e9e9; color: #333; }
        .timer-warn { color: var(--err); font-weight: bold; }
        .controls { padding: 20px; text-align: center; background: white; border-top: 1px solid #eee; }
        #mic { width: 70px; height: 70px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 2rem; cursor: pointer; transition: 0.3s; }
        #mic.listening { background: var(--ok); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(39,174,96, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(39,174,96, 0); } }
    </style>
</head>
<body>
<div class="app">
    <header><b>English Tutor FWB</b> <div id="timer-display">--:--</div></header>
    <div class="info-bar">
        <span>👤 <b id="display-name">Guest</b></span>
        <span>⭐ Score: <b id="score-val">0</b></span>
    </div>
    <div id="chat"><div class="msg ai">Welcome! Click the mic to start.</div></div>
    <div class="controls">
        <button id="mic">🎤</button>
        <p id="status" style="margin-top:10px; font-size:0.8rem;">Click to start</p>
    </div>
</div>
<script>
"""

part2 = f"""
    const API_KEY = "{api_key}";
    const USER_NAME = "{user_name or 'Élève'}";
    const MODE = "{conv_mode}";
    const LIMIT_TIME = {timer_mins} * 60;
    const VOICE_SPEED = {voice_speed};
    const CONSTRAINTS = "{combined_constraints}";
    const GRAMMAR = "{target_grammar}";
"""

part3 = """
    let score = 0; let history = []; let fullTranscript = "";
    let timeLeft = LIMIT_TIME; let timerActive = false;
    let isAutoRestart = (MODE !== "Tuteur IA (Interactif)");

    document.getElementById('display-name').innerText = USER_NAME;

    // --- LOGIQUE CHRONOMÈTRE ---
    function startTimer() {
        if (timerActive) return;
        timerActive = true;
        const interval = setInterval(() => {
            timeLeft--;
            let mins = Math.floor(timeLeft / 60);
            let secs = timeLeft % 60;
            document.getElementById('timer-display').innerText = mins + ":" + (secs < 10 ? "0" : "") + secs;
            if (timeLeft <= 30) document.getElementById('timer-display').classList.add('timer-warn');
            if (timeLeft <= 0) {
                clearInterval(interval);
                stopSession();
            }
        }, 1000);
    }

    // --- RECONNAISSANCE VOCALE ---
    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new Speech();
    rec.lang = 'en-US';

    document.getElementById('mic').onclick = () => {
        startTimer();
        try { rec.start(); } catch(e) { rec.stop(); }
    };

    rec.onstart = () => { document.getElementById('mic').classList.add('listening'); };
    rec.onend = () => { 
        document.getElementById('mic').classList.remove('listening');
        if (timerActive && isAutoRestart) { setTimeout(() => rec.start(), 500); }
    };

    rec.onresult = (e) => {
        const text = e.results[0][0].transcript;
        processInput(text);
    };

    async function processInput(text) {
        addMsg(text, 'user');
        fullTranscript += USER_NAME + ": " + text + "\\n";
        
        // Scoring simple
        if (CONSTRAINTS.toLowerCase().split(',').some(w => text.toLowerCase().includes(w.trim()))) {
            score += 20; document.getElementById('score-val').innerText = score;
        }

        if (MODE === "Tuteur IA (Interactif)") {
            callAI(text);
        }
    }

    async function callAI(text) {
        const prompt = `You are a friendly tutor. Level: A2. Goal: Practice conversation. 
        Current Student: ${USER_NAME}. Constraints: ${CONSTRAINTS}. Rule: 1 sentence + 1 question.`;
        
        const r = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY },
            body: JSON.stringify({
                model: "gpt-4o-mini",
                messages: [{role:"system", content: prompt}, ...history, {role:"user", content: text}]
            })
        });
        const d = await r.json();
        const reply = d.choices[0].message.content;
        addMsg(reply, 'ai');
        fullTranscript += "Tutor: " + reply + "\\n\\n";
        speak(reply);
        history.push({role:"user", content:text}, {role:"assistant", content:reply});
    }

    function speak(t) {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(t);
        u.lang = 'en-US';
        u.rate = VOICE_SPEED;
        window.speechSynthesis.speak(u);
    }

    function addMsg(t, cl) {
        const b = document.getElementById('chat');
        const d = document.createElement('div');
        d.className = "msg " + cl;
        d.innerText = t;
        b.appendChild(d);
        b.scrollTop = b.scrollHeight;
    }

    async function stopSession() {
        timerActive = false;
        rec.stop();
        isAutoRestart = false;
        addMsg("⌛ Temps écoulé ! Génération de ton évaluation...", "ai");
        
        const evalPrompt = `Agis comme un prof d'anglais belge. Analyse cette session pour l'élève nommé ${USER_NAME}. 
        Mode: ${MODE}. Contraintes: ${CONSTRAINTS}. Grammaire: ${GRAMMAR}.
        TUTOIE l'élève directement ("Tu as fait...", "Je te conseille...").
        Structure: 1. Respect des consignes (/5), 2. Vocabulaire (/5), 3. Grammaire (/5), 4. Note /20 et Conseil.
        Transcript: ${fullTranscript}`;

        const r = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY },
            body: JSON.stringify({
                model: "gpt-4o-mini",
                messages: [{role:"system", content: "Expert FWB. Tu tutoies l'élève."}, {role:"user", content: evalPrompt}]
            })
        });
        const d = await r.json();
        const ev = d.choices[0].message.content;
        
        const blob = new Blob(["RAPPORT POUR: " + USER_NAME + "\\n\\n" + ev], {type:"text/plain"});
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "Eval_" + USER_NAME + ".txt";
        a.click();
        alert("Session terminée, " + USER_NAME + ". Ton évaluation a été téléchargée.");
    }
</script>
</body>
</html>
"""

st.components.v1.html(part1 + part2 + part3, height=800)
