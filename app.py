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
    
    timer_mins = st.slider("Durée de la session (minutes) :", 1, 15, 5)
    voice_speed = st.slider("Vitesse de la voix IA :", 0.5, 1.5, 0.9, step=0.1)

    st.subheader("📚 Contraintes spécifiques")
    uploaded_file = st.file_uploader("Charger un lexique (PDF)", type="pdf")
    pdf_words = ""
    if uploaded_file:
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            pdf_words += page.extract_text()
            
    target_vocab = st.text_input("Mots-clés additionnels :", placeholder="word1, word2...")
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
        
        /* Réintégration des onglets et réglages */
        .settings-bar { padding: 10px; background: #eee; border-bottom: 1px solid #ddd; }
        .goal-input { width: 100%; padding: 8px; border-radius: 5px; border: 1px solid #3498DB; margin-top: 5px; font-size: 0.85rem; box-sizing: border-box; }
        .challenge-box { background: #FEF9E7; padding: 8px; border: 1px dashed var(--gold); border-radius: 5px; font-size: 0.85rem; color: #7D6608; text-align: center; font-weight: bold; margin-top: 5px; }
        .topics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; padding: 10px; border-bottom: 2px solid #ddd; background: #fff; }
        .t-btn { font-size: 0.7rem; padding: 8px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: white; text-align: center; }
        .t-btn.active { background: var(--s); color: white; border-color: var(--s); }
        
        .info-bar { background: #f9f9f9; padding: 5px 15px; font-size: 0.8rem; display: flex; justify-content: space-between; border-bottom: 1px solid #ddd; }
        #chat { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }
        .msg { max-width: 85%; padding: 10px 15px; border-radius: 15px; font-size: 0.95rem; }
        .user { align-self: flex-end; background: var(--s); color: white; border-bottom-right-radius: 2px; }
        .ai { align-self: flex-start; background: white; border: 1px solid #ddd; border-bottom-left-radius: 2px; }
        .timer-warn { color: var(--err); font-weight: bold; animation: blink 1s infinite; }
        @keyframes blink { 50% { opacity: 0.5; } }

        .controls { padding: 15px; text-align: center; background: white; border-top: 1px solid #eee; padding-bottom: 30px; }
        #mic { width: 65px; height: 65px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 1.8rem; cursor: pointer; transition: 0.3s; }
        #mic.listening { background: var(--ok); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(39,174,96, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(39,174,96, 0); } }
    </style>
</head>
<body>
<div class="app">
    <header><b>English Tutor FWB Pro</b> <div id="timer-display">--:--</div></header>
    
    <div class="settings-bar">
        <select id="lvl" style="width:100%; padding:5px; border-radius:5px;">
            <option value="P3-P6">Niveau Primaire (P3-P6)</option>
            <option value="S1-S2">Niveau S1-S2 (A2.1)</option>
            <option value="S3">Niveau S3 (A2.2)</option>
        </select>
        <input type="text" id="lesson-goal" class="goal-input" placeholder="Objectif de la leçon (ex: Commander au resto)...">
        <div class="challenge-box" id="challenge-txt">Challenge: Use "HELLO" (+50 pts)</div>
    </div>

    <div class="topics" id="t-grid"></div>

    <div class="info-bar">
        <span>👤 <b id="display-name">Guest</b></span>
        <span>⭐ <b id="score-val">0</b> pts</span>
    </div>

    <div id="chat"><div class="msg ai">Hello! Chose a topic and click the mic to start your session.</div></div>
    
    <div class="controls">
        <button id="mic">🎤</button>
        <p id="status" style="margin-top:8px; font-size:0.75rem; color:#666;">Press to Speak</p>
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
    const EXTRA_CONSTRAINTS = "{combined_constraints}";
    const GRAMMAR_TARGET = "{target_grammar}";
"""

part3 = """
    const FIELDS = [
        { n: 'Identity', e: '👤', w: 'name, age, brother, Belgium' }, 
        { n: 'House', e: '🏠', w: 'bedroom, kitchen, chair, table' }, 
        { n: 'Hobbies', e: '⚽', w: 'football, music, games, swimming' }, 
        { n: 'Food', e: '🍕', w: 'apple, bread, breakfast, hungry' },
        { n: 'Shopping', e: '🛍️', w: 'buy, price, shop, money' },
        { n: 'Health', e: '🍎', w: 'headache, doctor, fruit, sport' },
        { n: 'Travel', e: '🚲', w: 'bus, train, holiday, hotel' },
        { n: 'Time', e: '⏰', w: 'monday, morning, night, weekend' }
    ];

    let topic = "Identity"; let challengeWord = "name"; let score = 0; let history = [];
    let fullTranscript = ""; let timeLeft = LIMIT_TIME; let timerActive = false;
    let isAutoRestart = (MODE !== "Tuteur IA (Interactif)");

    document.getElementById('display-name').innerText = USER_NAME;

    // --- GRILLE DES THÈMES ---
    const grid = document.getElementById('t-grid');
    FIELDS.forEach((f, i) => {
        const b = document.createElement('button');
        b.className = "t-btn " + (i === 0 ? "active" : "");
        b.innerHTML = f.e + "<br>" + f.n;
        b.onclick = () => {
            topic = f.n;
            const words = f.w.split(', ');
            challengeWord = words[Math.floor(Math.random() * words.length)];
            document.getElementById('challenge-txt').innerText = "Challenge: Use \\"" + challengeWord.toUpperCase() + "\\" (+50 pts)";
            document.querySelectorAll('.t-btn').forEach(x => x.classList.remove('active'));
            b.classList.add('active');
        };
        grid.appendChild(b);
    });

    // --- CHRONO ---
    function startTimer() {
        if (timerActive) return;
        timerActive = true;
        const interval = setInterval(() => {
            if(!timerActive) { clearInterval(interval); return; }
            timeLeft--;
            let mins = Math.floor(timeLeft / 60);
            let secs = timeLeft % 60;
            document.getElementById('timer-display').innerText = mins + ":" + (secs < 10 ? "0" : "") + secs;
            if (timeLeft <= 30) document.getElementById('timer-display').classList.add('timer-warn');
            if (timeLeft <= 0) { clearInterval(interval); stopSession(); }
        }, 1000);
    }

    // --- MICRO ---
    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new Speech(); rec.lang = 'en-US'; rec.continuous = false;

    document.getElementById('mic').onclick = () => {
        startTimer();
        try { rec.start(); } catch(e) { rec.stop(); }
    };

    rec.onstart = () => { 
        document.getElementById('mic').classList.add('listening'); 
        document.getElementById('status').innerText = "I'm listening...";
    };
    rec.onend = () => { 
        document.getElementById('mic').classList.remove('listening'); 
        document.getElementById('status').innerText = "Press to Speak";
        if (timerActive && isAutoRestart) { setTimeout(() => { try{rec.start();}catch(e){} }, 600); }
    };

    rec.onresult = (e) => {
        const text = e.results[0][0].transcript;
        processInput(text);
    };

    async function processInput(text) {
        addMsg(text, 'user');
        fullTranscript += USER_NAME + ": " + text + "\\n";
        
        // Scoring
        let bonus = 0;
        if (text.toLowerCase().includes(challengeWord.toLowerCase())) bonus += 50;
        if (EXTRA_CONSTRAINTS.toLowerCase().split(',').some(w => w.length > 2 && text.toLowerCase().includes(w.trim()))) bonus += 30;
        
        score += (10 + bonus);
        document.getElementById('score-val').innerText = score;

        if (MODE === "Tuteur IA (Interactif)") { callAI(text); }
    }

    async function callAI(text) {
        const lvl = document.getElementById('lvl').value;
        const goal = document.getElementById('lesson-goal').value;
        const prompt = `Friendly English tutor (Belgium). Level: ${lvl}. Topic: ${topic}. Goal: ${goal}. 
        Constraints to encourage: ${EXTRA_CONSTRAINTS}. Grammar: ${GRAMMAR_TARGET}.
        Rule: 1 sentence + 1 question. Student name: ${USER_NAME}.`;
        
        try {
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
        } catch(e) { addMsg("Connection error.", "ai"); }
    }

    function speak(t) {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(t);
        u.lang = 'en-US'; u.rate = VOICE_SPEED;
        window.speechSynthesis.speak(u);
    }

    function addMsg(t, cl) {
        const b = document.getElementById('chat');
        const d = document.createElement('div');
        d.className = "msg " + cl; d.innerText = t;
        b.appendChild(d); b.scrollTop = b.scrollHeight;
    }

    async function stopSession() {
        timerActive = false; rec.stop(); isAutoRestart = false;
        addMsg("⌛ Time is up! Generating your FWB report...", "ai");
        
        const evalPrompt = `Tu es un prof d'anglais belge. Évalue la session de ${USER_NAME}. 
        Niveau: ${document.getElementById('lvl').value}. Objectif: ${document.getElementById('lesson-goal').value}.
        TUTOIE l'élève. Analyse le vocabulaire (${EXTRA_CONSTRAINTS}) et la grammaire (${GRAMMAR_TARGET}).
        Structure: 1. Objectif & Lexique (/5), 2. Grammaire (/5), 3. Interaction (/5), 4. Note /20 et Conseil.
        Transcript: ${fullTranscript}`;

        const r = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY },
            body: JSON.stringify({
                model: "gpt-4o-mini",
                messages: [{role:"system", content: "Expert FWB. Tutoiement obligatoire."}, {role:"user", content: evalPrompt}]
            })
        });
        const d = await r.json();
        const ev = d.choices[0].message.content;
        
        const blob = new Blob(["=== RAPPORT FWB - " + USER_NAME + " ===\\n\\n" + ev], {type:"text/plain"});
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "Evaluation_" + USER_NAME + ".txt";
        a.click();
        addMsg("✅ Report downloaded!", "ai");
    }
</script>
</body>
</html>
"""

st.components.v1.html(part1 + part2 + part3, height=850)
