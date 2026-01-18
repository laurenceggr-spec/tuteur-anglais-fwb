import streamlit as st
import base64

# 1. Configuration
st.set_page_config(page_title="English Tutor FWB Pro", layout="centered")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# 2. Le code HTML
raw_html = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        :root { --p: #2C3E50; --s: #3498DB; --bg: #F4F7F6; --err: #E74C3C; --ok: #27AE60; --gold: #F1C40F; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; display: flex; justify-content: center; height: 100vh; overflow: hidden; }
        .app { width: 100%; max-width: 500px; background: white; display: flex; flex-direction: column; box-shadow: 0 0 20px rgba(0,0,0,0.1); height: 100vh; }
        header { background: var(--p); color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .settings-bar { padding: 10px; background: #eee; border-bottom: 1px solid #ddd; display: flex; flex-direction: column; gap: 5px; }
        select { width: 100%; padding: 8px; border-radius: 5px; border: 1px solid #ccc; font-size: 14px; }
        .challenge-box { background: #FEF9E7; padding: 8px; border: 1px dashed var(--gold); border-radius: 5px; font-size: 0.85rem; color: #7D6608; text-align: center; font-weight: bold; }
        .topics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; padding: 10px; border-bottom: 2px solid #ddd; background: #fff; }
        .t-btn { font-size: 0.7rem; padding: 8px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: white; transition: 0.2s; text-align: center; }
        .t-btn.active { background: var(--s); color: white; border-color: var(--s); }
        #chat { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }
        .msg { max-width: 85%; padding: 12px; border-radius: 18px; line-height: 1.4; font-size: 1rem; position: relative; word-wrap: break-word; }
        .user { align-self: flex-end; background: var(--s); color: white; border-bottom-right-radius: 2px; }
        .ai { align-self: flex-start; background: white; border: 1px solid #ddd; color: #333; border-bottom-left-radius: 2px; }
        .controls { padding: 20px; text-align: center; border-top: 1px solid #eee; background: white; }
        #mic { width: 70px; height: 70px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 1.8rem; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.2); outline: none; }
        #mic.listening { background: var(--ok); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(39,174,96, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(39,174,96, 0); } }
    </style>
</head>
<body>
<div class="app">
    <header>
        <div style="font-weight:bold;">English Tutor FWB 🇧🇪</div>
        <div>⭐ <span id="score-val">0</span></div>
    </header>
    <div class="settings-bar">
        <select id="lvl">
            <option value="A1 (P3-P6)">Niveau P3-P6 (A1)</option>
            <option value="A2.1 (S1-S2)">Niveau S1-S2 (A2.1)</option>
            <option value="A2.2 (S3)">Niveau S3 (A2.2)</option>
        </select>
        <div class="challenge-box" id="challenge-txt">Challenge: Use the word "NAME" for +50 pts!</div>
    </div>
    <div class="topics" id="t-grid"></div>
    <div id="chat">
        <div class="msg ai">Hello! I'm your tutor. Choose a topic and let's speak!</div>
    </div>
    <div class="controls">
        <button id="mic">🎤</button>
        <p id="status" style="margin-top:10px; color:#666; font-size:0.8rem;">Click to talk</p>
    </div>
</div>
<script>
    const API_KEY = "TOKEN_KEY";
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
    const grid = document.getElementById('t-grid');
    FIELDS.forEach((f, i) => {
        const b = document.createElement('button');
        b.className = "t-btn " + (i === 0 ? "active" : "");
        b.innerHTML = f.e + "<br>" + f.n;
        b.onclick = () => {
            topic = f.n;
            const words = f.w.split(', ');
            challengeWord = words[Math.floor(Math.random() * words.length)];
            document.getElementById('challenge-txt').innerText = "Challenge: Use the word \\"" + challengeWord.toUpperCase() + "\\" for +50 pts!";
            document.querySelectorAll('.t-btn').forEach(x => x.classList.remove('active'));
            b.classList.add('active');
            addMsg("Topic: " + f.n, 'ai');
            history = [];
        };
        grid.appendChild(b);
    });
    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Speech) {
        alert("Attention: La reconnaissance vocale n'est pas supportée sur ce navigateur. Utilisez Chrome.");
    }
    const rec = new Speech(); rec.lang = 'en-US'; rec.continuous = false;
    document.getElementById('mic').onclick = () => { try { rec.start(); } catch(e) { console.log(e); } };
    rec.onstart = () => { document.getElementById('mic').classList.add('listening'); document.getElementById('status').innerText = "I am listening..."; };
    rec.onresult = (e) => { callOpenAI(e.results[0][0].transcript); };
    rec.onend = () => { document.getElementById('mic').classList.remove('listening'); document.getElementById('status').innerText = "Click to talk"; };
    async function callOpenAI(userText) {
        addMsg(userText, 'user');
        let bonus = userText.toLowerCase().includes(challengeWord.toLowerCase()) ? 50 : 0;
        if(bonus > 0) setTimeout(() => addMsg("🎯 Challenge +50 pts!", 'ai'), 500);
        const level = document.getElementById('lvl').value;
        const currentField = FIELDS.find(f => f.n === topic);
        const systemPrompt = "Friendly English Tutor (FWB Belgium). Level: " + level + ". Topic: " + topic + ". Vocabulary: " + currentField.w + ". Rules: 1 sentence, correct errors, end with question.";
        const messages = [{ role: "system", content: systemPrompt }, ...history, { role: "user", content: userText }];
        try {
            const r = await fetch('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY },
                body: JSON.stringify({ model: "gpt-4o-mini", messages: messages })
            });
            const d = await r.json();
            const reply = d.choices[0].message.content;
            addMsg(reply, 'ai');
            const u = new SpeechSynthesisUtterance(reply); u.lang = 'en-US'; u.rate = 0.85; window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
            history.push({ role: "user", content: userText }); history.push({ role: "assistant", content: reply });
            score += (10 + bonus); document.getElementById('score-val').innerText = score;
        } catch (e) { addMsg("Error: Check API credits.", "ai"); }
    }
    function addMsg(t, cl) {
        const box = document.getElementById('chat'); const div = document.createElement('div');
        div.className = "msg " + cl; div.innerText = t; box.appendChild(div); box.scrollTop = box.scrollHeight;
    }
</script>
</body>
</html>
"""

# 3. Remplacement et encodage
final_html = raw_html.replace("TOKEN_KEY", api_key)
b64_html = base64.b64encode(final_html.encode()).decode()

# 4. AFFICHAGE AVEC AUTORISATION MICRO
st.components.v1.html(
    f'<iframe src="data:text/html;base64,{b64_html}" style="width:100%; height:800px; border:none;" allow="microphone"></iframe>',
    height=800
)
