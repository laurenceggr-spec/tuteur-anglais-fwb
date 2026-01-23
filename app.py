import streamlit as st
import PyPDF2
import io

# 1. Configuration de la page
st.set_page_config(page_title="English Tutor FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# --- BARRE LATÉRALE : RÉGLAGES PÉDAGOGIQUES ---
with st.sidebar:
    st.header("⚙️ Paramètres de la Leçon")
    
    # 1. Vocabulaire spécifique (PDF)
    uploaded_file = st.file_uploader("Charger un lexique (PDF)", type="pdf")
    pdf_words = ""
    if uploaded_file:
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            pdf_words += page.extract_text()
        st.success("Lexique PDF intégré !")

    # 2. Vocabulaire manuel (mots séparés par des virgules)
    target_vocab = st.text_input("Mots-clés cibles (séparés par des virgules) :", 
                                placeholder="ex: environment, global warming, nature")
    
    # 3. Grammaire cible
    target_grammar = st.text_input("Grammaire à vérifier :", 
                                  placeholder="ex: Present Perfect, Passive Voice")

# Nettoyage pour injection JS (on combine le texte du PDF et les mots manuels)
combined_constraints = f"{target_vocab}, {pdf_words[:500]}".replace('"', '').replace('\n', ' ')

# 2. Construction de l'interface
part1 = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        :root { --p: #2C3E50; --s: #3498DB; --bg: #F4F7F6; --err: #E74C3C; --ok: #27AE60; --gold: #F1C40F; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; padding: 0; overflow: hidden; height: 100vh; }
        .app { width: 100%; max-width: 500px; margin: auto; background: white; height: 100vh; display: flex; flex-direction: column; }
        header { background: var(--p); color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .settings-bar { padding: 10px; background: #eee; border-bottom: 1px solid #ddd; }
        .goal-input { width: 100%; padding: 8px; border-radius: 5px; border: 1px solid #3498DB; margin-top: 5px; font-size: 0.85rem; box-sizing: border-box; }
        .challenge-box { background: #FEF9E7; padding: 8px; border: 1px dashed var(--gold); border-radius: 5px; font-size: 0.85rem; color: #7D6608; text-align: center; font-weight: bold; margin-top: 5px; }
        .topics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; padding: 10px; border-bottom: 2px solid #ddd; }
        .t-btn { font-size: 0.7rem; padding: 8px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: white; text-align: center; }
        .t-btn.active { background: var(--s); color: white; border-color: var(--s); }
        #chat { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }
        .msg { max-width: 85%; padding: 12px; border-radius: 18px; line-height: 1.4; font-size: 1rem; word-wrap: break-word; }
        .user { align-self: flex-end; background: var(--s); color: white; border-bottom-right-radius: 2px; }
        .ai { align-self: flex-start; background: white; border: 1px solid #ddd; border-bottom-left-radius: 2px; }
        .bonus-msg { font-size: 0.8rem; color: var(--ok); font-weight: bold; margin-top: -5px; margin-bottom: 5px; align-self: flex-end; }
        .controls { padding: 15px; text-align: center; border-top: 1px solid #eee; background: white; display: flex; flex-direction: column; align-items: center; gap: 10px; padding-bottom: 30px; }
        .btn-row { display: flex; align-items: center; gap: 10px; }
        #mic { width: 60px; height: 60px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 1.5rem; cursor: pointer; }
        #mic.listening { background: var(--ok); animation: pulse 1.5s infinite; }
        .eval-btn { background: var(--p); color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; font-size: 0.8rem; font-weight: bold; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(39,174,96, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(39,174,96, 0); } }
    </style>
</head>
<body>
<div class="app">
    <header><b>English Tutor FWB Pro</b> <div>⭐ <span id="score-val">0</span></div></header>
    <div class="settings-bar">
        <select id="lvl" style="width:100%; padding:5px;">
            <option value="A1">Niveau P3-P6 (A1)</option>
            <option value="A2.1">Niveau S1-S2 (A2.1)</option>
            <option value="A2.2">Niveau S3 (A2.2)</option>
        </select>
        <input type="text" id="lesson-goal" class="goal-input" placeholder="Objectif de la leçon...">
        <div class="challenge-box" id="challenge-txt">Challenge: Use "NAME" (+50 pts)</div>
    </div>
    <div class="topics" id="t-grid"></div>
    <div id="chat"><div class="msg ai">Hello! I'm ready to practice your specific goals. Speak to me!</div></div>
    <div class="controls">
        <div class="btn-row">
            <button id="mic">🎤</button>
            <button id="eval-btn" class="eval-btn">📊 Mon Évaluation FWB</button>
        </div>
        <p id="status" style="font-size:0.7rem; color:#666; margin:0;">Appuie pour parler</p>
    </div>
</div>
<script>
"""

part2 = f"""
    const API_KEY = "{api_key}";
    const RAW_CONSTRAINTS = "{combined_constraints}";
    const TARGET_GRAMMAR = "{target_grammar}";
"""

part3 = """
    const FIELDS = [
        { n: 'Identity', e: '👤', w: 'name, age, brother, sister, Belgium' }, 
        { n: 'House', e: '🏠', w: 'bedroom, kitchen, garden, chair, table' }, 
        { n: 'Hobbies', e: '⚽', w: 'football, music, video games, swimming' }, 
        { n: 'Food', e: '🍕', w: 'apple, bread, breakfast, hungry, thirsty' },
        { n: 'Shopping', e: '🛍️', w: 'buy, price, shop, money, expensive' },
        { n: 'Health', e: '🍎', w: 'headache, doctor, fruit, vegetable, sport' },
        { n: 'Travel', e: '🚲', w: 'bus, train, bike, holiday, hotel' },
        { n: 'Time', e: '⏰', w: 'monday, morning, night, weekend, o-clock' }
    ];

    let topic = "Identity"; let challengeWord = "name"; let score = 0; let history = [];
    let fullTranscript = "";
    let voiceInitialized = false;

    // Initialisation de la grille
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

    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = (Speech) ? new Speech() : null;
    if (rec) { rec.lang = 'en-US'; rec.continuous = false; }

    document.getElementById('mic').onclick = () => {
        if (!voiceInitialized) { window.speechSynthesis.speak(new SpeechSynthesisUtterance("")); voiceInitialized = true; }
        if (!rec) { alert("Navigateur non compatible."); return; }
        try { rec.start(); } catch(e) {}
    };

    rec.onstart = () => { document.getElementById('mic').classList.add('listening'); };
    rec.onresult = (e) => { processUserSpeech(e.results[0][0].transcript); };
    rec.onend = () => { document.getElementById('mic').classList.remove('listening'); };

    async function processUserSpeech(userText) {
        addMsg(userText, 'user');
        
        // --- LOGIQUE DE SCORING DYNAMIQUE ---
        let currentBonus = 0;
        let foundWords = [];
        
        // 1. Check Challenge Word
        if (userText.toLowerCase().includes(challengeWord.toLowerCase())) {
            currentBonus += 50;
            foundWords.push("CHALLENGE ✨");
        }

        // 2. Check Pedagogical Vocabulary
        const vocabList = RAW_CONSTRAINTS.split(',').map(s => s.trim().toLowerCase()).filter(s => s.length > 3);
        vocabList.forEach(w => {
            if (userText.toLowerCase().includes(w) && !foundWords.includes(w)) {
                currentBonus += 30;
                foundWords.push(w);
            }
        });

        if (currentBonus > 0) {
            score += currentBonus;
            document.getElementById('score-val').innerText = score;
            const bDiv = document.createElement('div');
            bDiv.className = "bonus-msg";
            bDiv.innerText = "Bonus: +" + currentBonus + " pts (" + foundWords.join(', ') + ")";
            document.getElementById('chat').appendChild(bDiv);
        }

        callAI(userText);
    }

    async function callAI(userText) {
        fullTranscript += "Élève: " + userText + "\\n";
        const level = document.getElementById('lvl').value;
        const goal = document.getElementById('lesson-goal').value || "General practice";
        
        const systemPrompt = `You are a friendly English Tutor in Belgium. 
        Level: ${level}. Goal: ${goal}. 
        Specific Vocab to encourage: ${RAW_CONSTRAINTS}.
        Grammar to encourage: ${TARGET_GRAMMAR}.
        Rule: 1 sentence response + 1 question. Be supportive.`;

        try {
            const r = await fetch('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY },
                body: JSON.stringify({
                    model: "gpt-4o-mini",
                    messages: [{role:"system", content:systemPrompt}, ...history, {role:"user", content:userText}]
                })
            });
            const d = await r.json();
            const reply = d.choices[0].message.content;
            addMsg(reply, 'ai');
            fullTranscript += "Tutor: " + reply + "\\n\\n";
            
            const u = new SpeechSynthesisUtterance(reply); u.lang = 'en-US';
            window.speechSynthesis.speak(u);
            history.push({role:"user", content:userText}, {role:"assistant", content:reply});
        } catch(e) { addMsg("Error connecting to AI.", "ai"); }
    }

    function addMsg(t, cl) {
        const box = document.getElementById('chat');
        const div = document.createElement('div');
        div.className = "msg " + cl;
        div.innerText = t;
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
    }

    document.getElementById('eval-btn').onclick = async () => {
        if (history.length < 2) { alert("Speak a bit more first!"); return; }
        addMsg("⌛ Analyse criteria (FWB)...", "ai");
        
        const evalPrompt = `Évalue l'élève (Niveau ${document.getElementById('lvl').value}).
        Objectif: ${document.getElementById('lesson-goal').value}.
        Vocabulaire imposé: ${RAW_CONSTRAINTS}.
        Grammaire imposée: ${TARGET_GRAMMAR}.
        
        Structure le rapport en Français (Tutoiement) :
        1. Respect de la consigne (/5)
        2. Richesse du vocabulaire et utilisation du lexique spécifique (/5)
        3. Correction de la grammaire et application de la grammaire cible (/5)
        4. Aisance et interaction (/5)
        5. Note globale /20 et CONSEIL.
        
        Texte: ${fullTranscript}`;

        try {
            const r = await fetch('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY },
                body: JSON.stringify({
                    model: "gpt-4o-mini",
                    messages: [{role:"system", content: "Expert enseignant FWB."}, {role:"user", content: evalPrompt}]
                })
            });
            const d = await r.json();
            const evalText = d.choices[0].message.content;
            alert(evalText);
            const blob = new Blob([evalText], { type: "text/plain" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url; a.download = "Evaluation.txt"; a.click();
        } catch(e) { alert("Evaluation error."); }
    };
</script>
</body>
</html>
"""

st.components.v1.html(part1 + part2 + part3, height=800)
