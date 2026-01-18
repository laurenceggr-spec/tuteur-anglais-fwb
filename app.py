import streamlit as st

# 1. Configuration de la page
st.set_page_config(page_title="English Tutor FWB", layout="centered")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# 2. Construction du HTML
part1 = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root { --p: #2C3E50; --s: #3498DB; --bg: #F4F7F6; --err: #E74C3C; --ok: #27AE60; --gold: #F1C40F; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; padding: 0; overflow: hidden; }
        .app { width: 100%; max-width: 500px; margin: auto; background: white; height: 100vh; display: flex; flex-direction: column; }
        header { background: var(--p); color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .settings-bar { padding: 10px; background: #eee; border-bottom: 1px solid #ddd; }
        .challenge-box { background: #FEF9E7; padding: 8px; border: 1px dashed var(--gold); border-radius: 5px; font-size: 0.85rem; color: #7D6608; text-align: center; font-weight: bold; }
        .topics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; padding: 10px; border-bottom: 2px solid #ddd; }
        .t-btn { font-size: 0.7rem; padding: 8px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: white; text-align: center; }
        .t-btn.active { background: var(--s); color: white; border-color: var(--s); }
        #chat { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }
        .msg { max-width: 85%; padding: 12px; border-radius: 18px; line-height: 1.4; font-size: 1rem; word-wrap: break-word; }
        .user { align-self: flex-end; background: var(--s); color: white; border-bottom-right-radius: 2px; }
        .ai { align-self: flex-start; background: white; border: 1px solid #ddd; border-bottom-left-radius: 2px; }
        .controls { padding: 20px; text-align: center; border-top: 1px solid #eee; background: white; }
        #mic { width: 70px; height: 70px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 1.8rem; cursor: pointer; }
        #mic.listening { background: var(--ok); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(39,174,96, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(39,174,96, 0); } }
    </style>
</head>
<body>
<div class="app">
    <header><b>English Tutor FWB 🇧🇪</b> <div>⭐ <span id="score-val">0</span></div></header>
    <div class="settings-bar">
        <select id="lvl" style="width:100%; margin-bottom:5px; padding:5px;">
            <option value="A1">Niveau P3-P6 (A1)</option>
            <option value="A2.1">Niveau S1-S2 (A2.1)</option>
            <option value="A2.2">Niveau S3 (A2.2)</option>
        </select>
        <div class="challenge-box" id="challenge-txt">Challenge: Use "NAME" (+50 pts)</div>
    </div>
    <div class="topics" id="t-grid"></div>
    <div id="chat"><div class="msg ai">Hello! I'm your tutor. Choose a topic and click the mic to speak!</div></div>
    <div class="controls">
        <button id="mic">🎤</button>
        <p id="status" style="font-size:0.8rem; color:#666; margin-top:10px;">Click to talk</p>
    </div>
</div>
<script>
"""

# Insertion de la clé API
part2 = f'const API_KEY = "{api_key}";'

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
            addMsg("Topic: " + f.n + ". Let's practice!", 'ai');
            history = [];
        };
        grid.appendChild(b);
    });

    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new Speech();
    rec.lang = 'en-US';
    rec.interimResults = false;

    document.getElementById('mic').onclick = () => {
        try { rec.start(); } catch(e) { console.log("Micro already active"); }
    };

    rec.onstart = () => {
        document.getElementById('mic').classList.add('listening');
        document.getElementById('status').innerText = "I am listening...";
    };

    rec.onresult = (e) => {
        const text = e.results[0][0].transcript;
        callAI(text);
    };

    rec.onend = () => {
        document.getElementById('mic').classList.remove('listening');
        document.getElementById('status').innerText = "Click to talk";
    };

    async function callAI(userText) {
        addMsg(userText, 'user');
        
        let bonus = 0;
        if (userText.toLowerCase().includes(challengeWord.toLowerCase())) {
            bonus = 50;
        }

        const level = document.getElementById('lvl').value;
        const currentField = FIELDS.find(f => f.n === topic);
        
        // Prompt avec tolérance pour le prénom Laurence / Lawrence
        const systemPrompt = "Act as a friendly English Tutor (FWB Belgium). Level: " + level + ". Topic: " + topic + ". " +
        "Note: The student has a French name. If you hear 'Lawrence' or 'Lauren', they mean 'Laurence'. " +
        "Rules: 1 short sentence response, correct errors gently (You said... but it's better to say...), end with 1 simple question.";
        
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
            if (bonus > 0) addMsg("🎯 Bonus Challenge +50 points!", "ai");
            
            const u = new SpeechSynthesisUtterance(reply); 
            u.lang = 'en-US'; 
            u.rate = 0.9;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
            
            history.push({role:"user", content:userText}, {role:"assistant", content:reply});
            score += (10 + bonus);
            document.getElementById('score-val').innerText = score;
        } catch(e) { 
            addMsg("Connection error. Please try again.", "ai"); 
        }
    }

    function addMsg(t, cl) {
        const box = document.getElementById('chat');
        const div = document.createElement('div');
        div.className = "msg " + cl;
        div.innerText = t;
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
    }
</script>
</body>
</html>
"""

st.components.v1.html(part1 + part2 + part3, height=800)
