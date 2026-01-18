import streamlit as st

st.set_page_config(page_title="English Tutor FWB", layout="centered")

html_code = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>English Tutor - FWB Edition</title>
    <style>
        :root { --p: #2C3E50; --s: #3498DB; --bg: #F4F7F6; --err: #E74C3C; --ok: #27AE60; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; display: flex; justify-content: center; height: 100vh; overflow: hidden; }
        .app { width: 100%; max-width: 500px; background: white; display: flex; flex-direction: column; box-shadow: 0 0 20px rgba(0,0,0,0.1); height: 100vh; }
        header { background: var(--p); color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .settings-bar { padding: 10px; background: #eee; border-bottom: 1px solid #ddd; display: flex; gap: 10px; }
        select { flex: 1; padding: 8px; border-radius: 5px; border: 1px solid #ccc; }
        .topics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; padding: 10px; border-bottom: 2px solid #ddd; background: #fff; }
        .t-btn { font-size: 0.7rem; padding: 8px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: white; transition: 0.2s; text-align: center; }
        .t-btn.active { background: var(--s); color: white; border-color: var(--s); }
        #chat { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }
        .msg { max-width: 85%; padding: 12px; border-radius: 18px; line-height: 1.4; font-size: 1rem; position: relative; word-wrap: break-word; }
        .user { align-self: flex-end; background: var(--s); color: white; border-bottom-right-radius: 2px; }
        .ai { align-self: flex-start; background: white; border: 1px solid #ddd; color: #333; border-bottom-left-radius: 2px; }
        .error-msg { background: #FDEDEC; color: var(--err); align-self: center; font-size: 0.8rem; border: 1px solid var(--err); padding: 10px; border-radius: 5px; }
        .controls { padding: 20px; text-align: center; border-top: 1px solid #eee; background: white; }
        #mic { width: 70px; height: 70px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 1.8rem; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.2); outline: none; }
        #mic.listening { background: var(--ok); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(39,174,96, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(39,174,96, 0); } }
    </style>
</head>
<body>

<div class="app">
    <header>
        <button onclick="askKey()" style="background:none; border:none; color:white; font-size:1.5rem; cursor:pointer;">⚙️</button>
        <div style="font-weight:bold;">English Tutor 🇧🇪</div>
        <div>⭐ <span id="score-val">0</span></div>
    </header>

    <div class="settings-bar">
        <select id="lvl">
            <option value="A1 (P3-P6)">Niveau P3-P6 (A1)</option>
            <option value="A2.1 (S1-S2)">Niveau S1-S2 (A2.1)</option>
            <option value="A2.2 (S3)">Niveau S3 (A2.2)</option>
        </select>
    </div>

    <div class="topics" id="t-grid"></div>

    <div id="chat">
        <div class="msg ai">Hello! I'm your tutor. Clique sur l'engrenage pour ta clé API, puis sur le micro pour me parler !</div>
    </div>

    <div class="controls">
        <button id="mic">🎤</button>
        <p id="status" style="margin-top:10px; color:#666; font-size:0.8rem;">Clique pour parler</p>
    </div>
</div>

<script>
    const FIELDS = [
        { n: 'Identity', e: '👤' }, { n: 'House', e: '🏠' }, { n: 'Hobbies', e: '⚽' }, 
        { n: 'Travel', e: '🚲' }, { n: 'Health', e: '🍎' }, { n: 'Shopping', e: '🛍️' },
        { n: 'Food', e: '🍕' }, { n: 'Time', e: '⏰' }
    ];

    let key = localStorage.getItem('gemini_key') || "";
    let topic = "Identity";
    let score = 0;
    let history = [];

    const grid = document.getElementById('t-grid');
    FIELDS.forEach((f, i) => {
        const b = document.createElement('button');
        b.className = `t-btn ${i === 0 ? 'active' : ''}`;
        b.innerHTML = `${f.e}<br>${f.n}`;
        b.onclick = () => {
            topic = f.n;
            document.querySelectorAll('.t-btn').forEach(x => x.classList.remove('active'));
            b.classList.add('active');
            addMsg(`Topic changed to: ${f.n}. Ready!`, 'ai');
            history = []; 
        };
        grid.appendChild(b);
    });

    window.askKey = function() {
        const input = prompt("Colle ta clé API Gemini ici :", key);
        if (input) {
            key = input.trim();
            localStorage.setItem('gemini_key', key);
            location.reload();
        }
    };

    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (Speech) {
        const rec = new Speech();
        rec.lang = 'en-US';

        document.getElementById('mic').onclick = () => {
            if (!key) return askKey();
            try { rec.start(); } catch(e) {}
        };

        rec.onstart = () => {
            document.getElementById('mic').classList.add('listening');
            document.getElementById('status').innerText = "Listening...";
        };

        rec.onresult = (e) => {
            const txt = e.results[0][0].transcript;
            addMsg(txt, 'user');
            callAI(txt);
        };

        rec.onend = () => {
            document.getElementById('mic').classList.remove('listening');
            document.getElementById('status').innerText = "Click to talk";
        };
    }

    async function callAI(userText) {
        const level = document.getElementById('lvl').value;
        // URL MISE À JOUR VERS V1
        const url = `https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=${key}`;

        const context = history.map(h => `${h.role}: ${h.text}`).join("\\n");
        const promptText = `Act as a friendly English Tutor (FWB Belgium context). Level: ${level}. Topic: ${topic}. History: ${context}. Student said: "${userText}". Respond in 1 short sentence, correct errors gently like 'You said... but it's better to say...', and ask 1 question. Use very simple English.`;

        try {
            const r = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contents: [{ parts: [{ text: promptText }] }] })
            });
            const d = await r.json();

            if (d.error) {
                addMsg(`API Error: ${d.error.message}`, 'error-msg');
            } else if (d.candidates && d.candidates[0].content) {
                const reply = d.candidates[0].content.parts[0].text;
                addMsg(reply, 'ai');
                speak(reply);
                history.push({role: "Student", text: userText});
                history.push({role: "Tutor", text: reply});
                score += 10;
                document.getElementById('score-val').innerText = score;
            }
        } catch (e) {
            addMsg("Connection error. Try again.", "error-msg");
        }
    }

    function addMsg(t, cl) {
        const box = document.getElementById('chat');
        const div = document.createElement('div');
        div.className = `msg ${cl}`;
        div.innerText = t;
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
    }

    function speak(t) {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(t);
        u.lang = 'en-US';
        u.rate = 0.9;
        window.speechSynthesis.speak(u);
    }
</script>
</body>
</html>
"""

st.components.v1.html(html_code, height=750)
