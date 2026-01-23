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
            
    target_vocab = st.text_input("Mots cibles additionnels :", placeholder="word1, word2...")
    target_grammar = st.text_input("Grammaire :", placeholder="ex: Past Simple")

# Préparation du vocabulaire cible (Checklist)
vocab_list = list(set([w.strip().lower() for w in (target_vocab + "," + pdf_words[:500]).split(",") if len(w.strip()) > 3]))
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
        .app { width: 100%; max-width: 700px; margin: auto; background: white; height: 100vh; display: flex; flex-direction: column; }
        
        header { background: var(--p); color: white; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; }
        
        .settings-bar { padding: 10px; background: #eee; border-bottom: 1px solid #ddd; }
        .lvl-select { width: 100%; padding: 5px; border-radius: 5px; margin-bottom: 5px; }
        
        /* Bandeau Challenge */
        .challenge-box { background: #FEF9E7; padding: 8px; border: 1px dashed var(--gold); border-radius: 5px; font-size: 0.8rem; color: #7D6608; text-align: center; font-weight: bold; margin-bottom: 5px; }

        /* Grille des Thèmes */
        .topics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; padding: 8px; background: #fff; border-bottom: 1px solid #ddd; }
        .t-btn { font-size: 0.65rem; padding: 6px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: white; text-align: center; }
        .t-btn.active { background: var(--s); color: white; border-color: var(--s); }

        /* Checklist des mots du PDF/Manuel */
        .vocab-check { padding: 8px; background: #f9f9f9; display: flex; flex-wrap: wrap; gap: 5px; max-height: 70px; overflow-y: auto; border-bottom: 1px solid #ddd; }
        .v-badge { padding: 3px 8px; border-radius: 10px; background: #ddd; color: #777; font-size: 0.7rem; transition: 0.3s; border: 1px solid #ccc; }
        .v-badge.found { background: var(--ok); color: white; border-color: var(--ok); transform: scale(1.05); }

        #chat { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }
        .msg { max-width: 80%; padding: 10px 15px; border-radius: 15px; font-size: 0.95rem; }
        .user { align-self: flex-end; background: var(--s); color: white; border-bottom-right-radius: 2px; }
        .ai { align-self: flex-start; background: white; border: 1px solid #ddd; border-bottom-left-radius: 2px; }
        
        .controls { padding: 15px; text-align: center; background: white; border-top: 1px solid #eee; display: flex; align-items: center; justify-content: space-between; padding-bottom: 30px; }
        #mic { width: 60px; height: 60px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 1.5rem; cursor: pointer; }
        #mic.listening { background: var(--ok); animation: pulse 1.5s infinite; }
        .hint-btn { background: var(--gold); border: none; padding: 10px 15px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 0.8rem; }
        #score-val { font-weight: bold; color: var(--p); font-size: 1.1rem; }

        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(39,174,96, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(39,174,96, 0); } }
    </style>
</head>
<body>
<div class="app">
    <header><b>English Lab FWB</b> <div id="timer-display">--:--</div></header>
    
    <div class="settings-bar">
        <select id="lvl" class="lvl-select">
            <option value="A1">Niveau Primaire (P3-P6)</option>
            <option value="A2.1">Niveau S1-S2 (A2.1)</option>
            <option value="A2.2">Niveau S3 (A2.2)</option>
        </select>
        <div class="challenge-box" id="challenge-txt">Challenge: Use "HELLO" (+50 pts)</div>
    </div>

    <div class="topics" id="t-grid"></div>
    <div class="vocab-check" id="vocab-display"></div>

    <div id="chat"><div class="msg ai">Hello <b><span id="name-span"></span></b>! Pick a topic, look at the vocabulary targets, and let's talk!</div></div>
    
    <div class="controls">
        <button class="hint-btn" id="hint-btn">💡 Hint</button>
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

    document.getElementById('name-span').innerText = USER_NAME;

    // --- GRILLE DES THEMES ---
    const FIELDS = [
        { n: 'Identity', e: '👤', w: 'name, age, brother, belgium' }, 
        { n: 'House', e: '🏠', w: 'bedroom, kitchen, garden, chair' }, 
        { n: 'Hobbies', e: '⚽', w: 'football, music, games, swimming' }, 
        { n: 'Food', e: '🍕', w: 'apple, bread, breakfast, hungry' },
        { n: 'Shopping', e: '🛍️', w: 'buy, price, shop, money' },
        { n: 'Health', e: '🍎', w: 'headache, doctor, fruit, sport' },
        { n: 'Travel', e: '🚲', w: 'bus, train, holiday, hotel' },
        { n: 'Time', e: '⏰', w: 'monday, morning, night, weekend' }
    ];

    const grid = document.getElementById('t-grid');
    FIELDS.forEach((f, i) => {
        const b = document.createElement('button');
        b.className = "t-btn " + (i === 0 ? "active" : "");
        b.innerHTML = f.e + "<br>" + f.n;
        b.onclick = () => {
            const words = f.w.split(', ');
            challengeWord = words[Math.floor(Math.random() * words.length)];
            document.getElementById('challenge-txt').innerText = "Challenge: Use \\"" + challengeWord.toUpperCase() + "\\" (+50 pts)";
            document.querySelectorAll('.t-btn').forEach(x => x.classList.remove('active'));
            b.classList.add('active');
            addMsg("Topic changed to " + f.n, "ai");
        };
        grid.appendChild(b);
    });

    // --- CHECKLIST VOCAB ---
    const vDisplay = document.getElementById('vocab-display');
    VOCAB_TARGETS.forEach(w => {
        const s = document.createElement('span');
        s.className = 'v-badge'; s.id = 'v-' + w; s.innerText = w;
        vDisplay.appendChild(s);
    });

    // --- MICRO ---
    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new Speech(); rec.lang = 'en-US';

    document.getElementById('mic').onclick = () => {
        startTimer();
        try { rec.start(); } catch(e) { rec.stop(); }
    };

    rec.onstart = () => document.getElementById('mic').classList.add('listening');
    rec.onend = () => {
        document.getElementById('mic').classList.remove('listening');
        if (timerActive && MODE !== "Tuteur IA (Interactif)") setTimeout(() => { try{rec.start();}catch(e){} }, 600);
    };

    rec.onresult = (e) => {
        const text = e.results[0][0].transcript;
        processInput(text);
    };

    function processInput(text) {
        addMsg(text, 'user');
        fullTranscript += USER_NAME + ": " + text + "\\n";
        
        let bonus = 0;
        // Check Challenge
        if (text.toLowerCase().includes(challengeWord.toLowerCase())) bonus += 50;

        // Check Checklist
        VOCAB_TARGETS.forEach(w => {
            if (text.toLowerCase().includes(w) && !foundVocab.has(w)) {
                foundVocab.add(w);
                document.getElementById('v-' + w).classList.add('found');
                bonus += 30;
            }
        });

        score += (10 + bonus);
        document.getElementById('score-val').innerText = score;
        if (MODE === "Tuteur IA (Interactif)") callAI(text);
    }

    async function callAI(text) {
        const prompt = `Role: ${PERSONA}. Level: ${document.getElementById('lvl').value}. 
        Grammar Target: ${GRAMMAR_TARGET}. Rule: 1 sentence + 1 question. Student: ${USER_NAME}.`;
        
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
            fullTranscript += PERSONA + ": " + reply + "\\n\\n";
            
            const u = new SpeechSynthesisUtterance(reply); u.lang = 'en-US'; u.rate = VOICE_SPEED;
            window.speechSynthesis.speak(u);
            history.push({role:"user", content:text}, {role:"assistant", content:reply});
        } catch(e) { addMsg("Error.", "ai"); }
    }

    document.getElementById('hint-btn').onclick = () => {
        addMsg("💡 Try saying: 'I'm not sure, but...', 'Could you explain?', or use a word from the list!", "ai");
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
        addMsg("⌛ Session Finished! Downloading your report...", "ai");
        
        const evalPrompt = `Évalue la session de ${USER_NAME} (Tutoiement).
        Mots du PDF validés: ${Array.from(foundVocab).join(', ')}.
        Objectif Grammaire: ${GRAMMAR_TARGET}.
        Score: ${score}.
        Transcript: ${fullTranscript}`;

        const r = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY },
            body: JSON.stringify({
                model: "gpt-4o-mini",
                messages: [{role:"system", content: "Expert FWB."}, {role:"user", content: evalPrompt}]
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
