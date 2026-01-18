import streamlit as st

# Configuration de la page
st.set_page_config(page_title="English Tutor FWB", layout="centered")

# Récupération de la clé depuis les secrets Streamlit
# Assurez-vous d'avoir OPENAI_API_KEY dans vos secrets
api_key = st.secrets.get("OPENAI_API_KEY", "")

html_code = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        :root {{ --p: #2C3E50; --s: #3498DB; --bg: #F4F7F6; --err: #E74C3C; --ok: #27AE60; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; display: flex; justify-content: center; height: 100vh; overflow: hidden; }}
        .app {{ width: 100%; max-width: 500px; background: white; display: flex; flex-direction: column; box-shadow: 0 0 20px rgba(0,0,0,0.1); height: 100vh; }}
        header {{ background: var(--p); color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }}
        .settings-bar {{ padding: 10px; background: #eee; border-bottom: 1px solid #ddd; display: flex; gap: 10px; }}
        select {{ flex: 1; padding: 8px; border-radius: 5px; border: 1px solid #ccc; }}
        .topics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; padding: 10px; border-bottom: 2px solid #ddd; background: #fff; }}
        .t-btn {{ font-size: 0.7rem; padding: 8px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: white; transition: 0.2s; text-align: center; }}
        .t-btn.active {{ background: var(--s); color: white; border-color: var(--s); }}
        #chat {{ flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }}
        .msg {{ max-width: 85%; padding: 12px; border-radius: 18px; line-height: 1.4; font-size: 1rem; position: relative; word-wrap: break-word; }}
        .user {{ align-self: flex-end; background: var(--s); color: white; border-bottom-right-radius: 2px; }}
        .ai {{ align-self: flex-start; background: white; border: 1px solid #ddd; color: #333; border-bottom-left-radius: 2px; }}
        .error-msg {{ background: #FDEDEC; color: var(--err); align-self: center; font-size: 0.8rem; border: 1px solid var(--err); padding: 10px; border-radius: 5px; }}
        .controls {{ padding: 20px; text-align: center; border-top: 1px solid #eee; background: white; }}
        #mic {{ width: 70px; height: 70px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 1.8rem; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.2); outline: none; }}
        #mic.listening {{ background: var(--ok); animation: pulse 1.5s infinite; }}
        @keyframes pulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(39,174,96, 0.7); }} 70% {{ box-shadow: 0 0 0 15px rgba(39,174,96, 0); }} }}
    </style>
</head>
<body>
<div class="app">
    <header>
        <div style="font-weight:bold;">English Tutor 🇧🇪</div>
        <div>⭐ <span id="score-val">0</span></div>
    </header>
    <div class="settings-bar">
        <select id="lvl">
            <option value="A1">Niveau P3-P6 (A1)</option>
            <option value="A2.1">Niveau S1-S2 (A2.1)</option>
            <option value="A2.2">Niveau S3 (A2.2)</option>
        </select>
    </div>
    <div class="topics" id="t-grid"></div>
    <div id="chat">
        <div class="msg ai">Hello! I'm your tutor. Clique sur le micro pour me parler !</div>
    </div>
    <div class="controls">
        <button id="mic">🎤</button>
        <p id="status">Clique pour parler</p>
    </div>
</div>

<script>
    const API_KEY = "{api_key}";
    const FIELDS = [
        {{ n: 'Identity', e: '👤' }}, {{ n: 'House', e: '🏠' }}, {{ n: 'Hobbies', e: '⚽' }}, 
        {{ n: 'Travel', e: '🚲' }}, {{ n: 'Health', e: '🍎' }}, {{ n: 'Shopping', e: '🛍️' }},
        {{ n: 'Food', e: '🍕' }}, {{ n: 'Time', e: '⏰' }}
    ];

    let topic = "Identity";
    let score = 0;
    let history = [];

    // Initialisation thèmes
    const grid = document.getElementById('t-grid');
    FIELDS.forEach((f, i) => {{
        const b = document.createElement('button');
        b.className = `t-btn ${{i === 0 ? 'active' : ''}}`;
        b.innerHTML = `${{f.e}}<br>${{f.n}}`;
        b.onclick = () => {{
            topic = f.n;
            document.querySelectorAll('.t-btn').forEach(x => x.classList.remove('active'));
            b.classList.add('active');
            addMsg(`Topic: ${{f.n}}. Let's go!`, 'ai');
            history = [];
        }};
        grid.appendChild(b);
    }});

    // Reconnaissance vocale
    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new Speech();
    rec.lang = 'en-US';

    document.getElementById('mic').onclick = () => rec.start();
    rec.onstart = () => {{
        document.getElementById('mic').classList.add('listening');
        document.getElementById('status').innerText = "I'm listening...";
    }};
    rec.onresult = (e) => callOpenAI(e.results[0][0].transcript);
    rec.onend = () => document.getElementById('mic').classList.remove('listening');

    async function callOpenAI(userText) {{
        addMsg(userText, 'user');
        const level = document.getElementById('lvl').value;
        
        const messages = [
            {{ role: "system", content: `Friendly English Tutor (Belgium FWB context). Level: ${{level}}. Topic: ${{topic}}. Respond in 1 short sentence, correct errors gently (You said... but it's better to say...), and ask 1 simple question.` }},
            ...history,
            {{ role: "user", content: userText }}
        ];

        try {{
            const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json', 'Authorization': `Bearer ${{API_KEY}}` }},
                body: JSON.stringify({{ model: "gpt-4o-mini", messages: messages }})
            }});
            const d = await r.json();
            const reply = d.choices[0].message.content;
            
            addMsg(reply, 'ai');
            speak(reply);
            
            history.push({{ role: "user", content: userText }});
            history.push({{ role: "assistant", content: reply }});
            score += 10;
            document.getElementById('score-val').innerText = score;
        }} catch (e) {{
            addMsg("Error: Check your API Key credits.", "error-msg");
        }}
    }}

    function addMsg(t, cl) {{
        const box = document.getElementById('chat');
        const div = document.createElement('div');
        div.className = `msg ${{cl}}`;
        div.innerText = t;
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
    }}

    function speak(t) {{
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(t);
        u.lang = 'en-US';
        u.rate = 0.9;
        window.speechSynthesis.speak(u);
    }}
</script>
</body>
</html>
"""

st.components.v1.html(html_code, height=750)
