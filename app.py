import streamlit as st
import PyPDF2

# 1. Configuration
st.set_page_config(page_title="English Tutor FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("👤 Élève")
    user_name = st.text_input("Nom de l'élève :", placeholder="Jean Dupont")
    ai_persona = st.text_input("L'IA doit être :", value="Friendly Teacher", placeholder="Ex: Harry Potter, a pilot...")
    
    st.header("⚙️ Paramètres")
    conv_mode = st.radio("Mode :", ["Tuteur IA (Interactif)", "Monologue", "Dialogue élèves"])
    timer_mins = st.slider("Chrono (min) :", 1, 5, 3)
    voice_speed = st.slider("Vitesse voix :", 0.5, 1.2, 0.8)

    st.subheader("📚 Lexique & PDF")
    uploaded_file = st.file_uploader("Lexique PDF", type="pdf")
    pdf_words = ""
    if uploaded_file:
        reader = PyPDF2.PdfReader(uploaded_file)
        pdf_words = " ".join([p.extract_text() for p in reader.pages])
            
    target_vocab = st.text_input("Mots cibles :", placeholder="word1, word2...")
    target_grammar = st.text_input("Grammaire :", placeholder="ex: Past Simple")

# Nettoyage des mots pour la checklist (on garde les mots de plus de 3 lettres)
vocab_list = list(set([w.strip().lower() for w in (target_vocab + "," + pdf_words[:300]).split(",") if len(w.strip()) > 3]))
vocab_json = str(vocab_list).replace("'", '"')

part1 = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root { --p: #2C3E50; --s: #3498DB; --bg: #F4F7F6; --err: #E74C3C; --ok: #27AE60; --gold: #F1C40F; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; padding: 0; height: 100vh; overflow:hidden; }
        .app { width: 100%; max-width: 700px; margin: auto; background: white; height: 100vh; display: flex; flex-direction: column; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
        
        header { background: var(--p); color: white; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; }
        .settings-bar { padding: 10px; background: #eee; border-bottom: 1px solid #ddd; }
        
        /* Checklist des mots */
        .vocab-check { padding: 10px; background: #fefefe; border-bottom: 1px solid #ddd; display: flex; flex-wrap: wrap; gap: 5px; max-height: 80px; overflow-y: auto; }
        .v-badge { padding: 4px 8px; border-radius: 12px; background: #ddd; color: #666; font-size: 0.75rem; transition: 0.3s; }
        .v-badge.found { background: var(--ok); color: white; transform: scale(1.1); }

        .topics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; padding: 8px; background: #fff; border-bottom: 1px solid #ddd; }
        .t-btn { font-size: 0.65rem; padding: 6px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: white; }
        .t-btn.active { background: var(--s); color: white; }
        
        #chat { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }
        .msg { max-width: 80%; padding: 10px 15px; border-radius: 15px; font-size: 0.95rem; position: relative; }
        .user { align-self: flex-end; background: var(--s); color: white; }
        .ai { align-self: flex-start; background: white; border: 1px solid #ddd; }
        
        .controls { padding: 15px; text-align: center; background: white; border-top: 1px solid #eee; display: flex; align-items: center; justify-content: space-around; }
        #mic { width: 60px; height: 60px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 1.5rem; cursor: pointer; }
        #mic.listening { background: var(--ok); animation: pulse 1.5s infinite; }
        .hint-btn { background: var(--gold); border: none; padding: 8px 12px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(39,174,96, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(39,174,96, 0); } }
    </style>
</head>
<body>
<div class="app">
    <header><b>English Lab FWB</b> <div id="timer-display">--:--</div></header>
    
    <div class="settings-bar">
        <select id="lvl" style="width:100%; padding:5px; border-radius:5px;">
            <option value="A1">Primary (P3-P6)</option>
            <option value="A2.1">Lower Secondary (S1-S2)</option>
            <option value="A2.2">Upper Secondary (S3)</option>
        </select>
        <div class="vocab-check" id="vocab-display"></div>
    </div>

    <div class="topics" id="t-grid"></div>

    <div id="chat"><div class="msg ai">Hello! I am your <b>target persona</b>. Ready to practice?</div></div>
    
    <div class="controls">
        <button class="hint-btn" id="hint-btn">💡 Hint</button>
        <button id="mic">🎤</button>
        <div id="score-box" style="text-align:right">⭐ <b id="score-val">0</b></div>
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
    let foundVocab = new Set(); let fillerCount = 0;

    // --- INITIALISATION VOCAB ---
    const vDisplay = document.getElementById('vocab-display');
    VOCAB_TARGETS.forEach(w => {
        const s = document.createElement('span');
        s.className = 'v-badge'; s.id = 'v-' + w; s.innerText = w;
        vDisplay.appendChild(s);
    });

    const FIELDS = [
        { n: 'Identity', e: '👤', w: 'name, age, family' }, { n: 'House', e: '🏠', w: 'room, bed, kitchen' }, 
        { n: 'Food', e: '🍕', w: 'eat, water, pizza' }, { n: 'Travel', e: '🚲', w: 'car, bus, plane' }
    ];

    const grid = document.getElementById('t-grid');
    FIELDS.forEach(f => {
        const b = document.createElement('button'); b.className = "t-btn"; b.innerHTML = f.e + "<br>" + f.n;
        b.onclick = () => { history = []; addMsg("Topic changed to: " + f.n, "ai"); };
        grid.appendChild(b);
    });

    // --- LOGIQUE MICRO ---
    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new Speech(); rec.lang = 'en-US';

    document.getElementById('mic').onclick = () => {
        startTimer();
        try { rec.start(); } catch(e) { rec.stop(); }
    };

    rec.onstart = () => document.getElementById('mic').classList.add('listening');
    rec.onend = () => {
        document.getElementById('mic').classList.remove('listening');
        if (timerActive && MODE !== "Tuteur IA (Interactif)") setTimeout(() => rec.start(), 600);
    };

    rec.onresult = (e) => {
        const text = e.results[0][0].transcript;
        processInput(text);
    };

    function processInput(text) {
        addMsg(text, 'user');
        fullTranscript += USER_NAME + ": " + text + "\\n";
        
        // Détection vocabulaire
        VOCAB_TARGETS.forEach(w => {
            if (text.toLowerCase().includes(w) && !foundVocab.has(w)) {
                foundVocab.add(w);
                document.getElementById('v-' + w).classList.add('found');
                score += 50;
            }
        });

        // Détection fillers (simplifiée)
        if (text.toLowerCase().includes("euh") || text.toLowerCase().includes("mmm")) fillerCount++;

        score += 10;
        document.getElementById('score-val').innerText = score;
        if (MODE === "Tuteur IA (Interactif)") callAI(text);
    }

    async function callAI(text) {
        const prompt = `Role: ${PERSONA}. Context: English Lesson. Level: ${document.getElementById('lvl').value}. 
        Grammar Target: ${GRAMMAR_TARGET}. Rule: 1 sentence + 1 question. Student: ${USER_NAME}.`;
        
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
        fullTranscript += PERSONA + ": " + reply + "\\n\\n";
        
        const u = new SpeechSynthesisUtterance(reply); u.lang = 'en-US'; u.rate = VOICE_SPEED;
        window.speechSynthesis.speak(u);
        history.push({role:"user", content:text}, {role:"assistant", content:reply});
    }

    document.getElementById('hint-btn').onclick = () => {
        addMsg("💡 Try using: 'Can you repeat?', 'I think that...', or a keyword from the top!", "ai");
    };

    function startTimer() {
        if (timerActive) return;
        timerActive = true;
        const interval = setInterval(() => {
            timeLeft--;
            let m = Math.floor(timeLeft/60); let s = timeLeft%60;
            document.getElementById('timer-display').innerText = m + ":" + (s<10?"0":"") + s;
            if (timeLeft <= 0) { clearInterval(interval); stopSession(); }
        }, 1000);
    }

    async function stopSession() {
        timerActive = false; rec.stop();
        addMsg("⌛ Fin ! Analyse en cours...", "ai");
        
        const evalPrompt = `Analyse la session de ${USER_NAME}. Il a parlé à ${PERSONA}.
        Mots validés: ${Array.from(foundVocab).join(', ')}. Fillers détectés: ${fillerCount}.
        Tutoie l'élève. Structure: Lexique, Grammaire, Fluidité (en évitant les 'euh'), Note /20.
        Transcript: ${fullTranscript}`;

        const r = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY },
            body: JSON.stringify({
                model: "gpt-4o-mini",
                messages: [{role:"system", content: "Prof Belge expert."}, {role:"user", content: evalPrompt}]
            })
        });
        const d = await r.json();
        const ev = d.choices[0].message.content;
        
        const blob = new Blob(["RAPPORT FWB - " + USER_NAME + "\\n\\n" + ev], {type:"text/plain"});
        const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
        a.download = "Eval_" + USER_NAME + ".txt"; a.click();
    }

    function addMsg(t, cl) {
        const b = document.getElementById('chat'); const d = document.createElement('div');
        d.className = "msg " + cl; d.innerText = t; b.appendChild(d); b.scrollTop = b.scrollHeight;
    }
</script>
</body>
</html>
"""

st.components.v1.html(part1 + part2 + part3, height=850)
