import streamlit as st
import PyPDF2
import pandas as pd
import qrcode
from io import BytesIO

# 1. CONFIGURATION
st.set_page_config(page_title="English Lab FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

if "scores_db" not in st.session_state:
    st.session_state.scores_db = []

if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "level": "S1-S2 (A2.1)",
        "topic": "Daily Routine",
        "mode": "Tuteur IA",
        "grammar": "Present Simple",
        "vocab": "wake up, breakfast, school"
    }

# --- LOGIQUE DU PONT (PYTHON) ---
def save_score(data_string):
    try:
        if "|" in data_string:
            parts = data_string.split("|")
            if len(parts) >= 4:
                name, score, words, evalu = parts[0], parts[1], parts[2], parts[3]
                if not any(d['Élève'] == name and d['Score'] == score for d in st.session_state.scores_db):
                    st.session_state.scores_db.append({
                        "Élève": name,
                        "Sujet": st.session_state.class_settings["topic"],
                        "Score": score,
                        "Mots": words,
                        "Évaluation": evalu,
                        "Date": pd.Timestamp.now().strftime("%H:%M")
                    })
    except: pass

# --- AUTHENTIFICATION ---
url_params = st.query_params
if "mode" in url_params and url_params["mode"] == "student":
    st.session_state.authenticated = True
    st.session_state.role = "Élève"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- ECRAN CONNEXION ---
if not st.session_state.authenticated:
    st.title("🚀 English Lab FWB")
    role = st.radio("Rôle :", ["Élève", "Professeur"], horizontal=True)
    password = st.text_input("Code :", type="password")
    if st.button("Entrer"):
        if (role == "Élève" and password == "ELEC2024") or (role == "Professeur" and password == "ADMIN123"):
            st.session_state.authenticated = True
            st.session_state.role = role
            st.rerun()

# --- ESPACE PROFESSEUR ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Centre de Commande")
    col_l, col_r = st.columns([1, 1.2])
    
    with col_l:
        st.subheader("⚙️ Paramètres de la session")
        with st.form("settings"):
            topic = st.text_input("Sujet de discussion :", value=st.session_state.class_settings["topic"])
            mode = st.selectbox("Mode d'interaction :", ["Tuteur IA", "Monologue (IA muette)", "Dialogue avec un ami", "Dialogue à deux élèves"])
            lvl = st.selectbox("Niveau :", ["P3-P4", "P5-P6", "S1-S2 (A2.1)", "S3 (A2.2)"])
            gram = st.text_input("Objectif Grammaire :", value=st.session_state.class_settings["grammar"])
            voc = st.text_area("Lexique imposé :", value=st.session_state.class_settings["vocab"])
            
            if st.form_submit_button("Lancer la session"):
                st.session_state.class_settings.update({
                    "topic": topic, "mode": mode, "level": lvl, "grammar": gram, "vocab": voc
                })
                st.success("Configuration mise à jour !")

        st.subheader("📲 QR Code Élève")
        app_url = "https://tuteur-anglais.streamlit.app" 
        qr = qrcode.make(f"{app_url}/?mode=student")
        buf = BytesIO(); qr.save(buf)
        st.image(buf, width=180)

    with col_r:
        st.subheader("📊 Résultats")
        bridge = st.text_input("Bridge", key="bridge_input", label_visibility="collapsed")
        if bridge: save_score(bridge)
        
        if st.session_state.scores_db:
            df = pd.DataFrame(st.session_state.scores_db)
            st.dataframe(df[['Élève', 'Sujet', 'Score', 'Date']], use_container_width=True)
            sel = st.selectbox("Détail évaluation :", df['Élève'].tolist())
            st.info(df[df['Élève'] == sel]['Évaluation'].values[0])
        else: st.info("Aucun élève connecté.")

    if st.button("Déconnexion"):
        st.session_state.authenticated = False
        st.rerun()

# --- INTERFACE ÉLÈVE ---
else:
    st.title("🎯 English Lab Session")
    user_name = st.sidebar.text_input("Nom(s) de(s) élève(s) :", placeholder="Ex: Tom & Sarah")
    
    if not user_name:
        st.warning("Indique ton nom (ou les deux noms) dans la barre latérale.")
    else:
        s = st.session_state.class_settings
        v_json = str([w.strip().lower() for w in s["vocab"].split(",") if len(w.strip()) > 2]).replace("'", '"')

        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; background: #f0f2f6; }}
                .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 12px; }}
                #chat {{ height: 250px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 15px; display: flex; flex-direction: column; gap: 8px; }}
                .msg {{ padding: 8px 12px; border-radius: 12px; font-size: 0.9rem; }}
                .user {{ align-self: flex-end; background: #007bff; color: white; }}
                .ai {{ align-self: flex-start; background: #eee; }}
                .btn {{ width: 100%; padding: 12px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }}
                #mic {{ background: #dc3545; color: white; margin-bottom: 10px; }}
                #stop {{ background: #28a745; color: white; }}
                .report {{ display: none; background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 15px; white-space: pre-wrap; }}
                .listening {{ background: #28a745 !important; animation: p 1s infinite; }}
                @keyframes p {{ 0%{{opacity:1}} 50%{{opacity:0.7}} 100%{{opacity:1}} }}
            </style>
        </head>
        <body>
            <div class="container">
                <h4>Topic: {s['topic']}</h4>
                <p style="font-size:0.8rem; color:#666;">Mode: {s['mode']}</p>
                <div id="chat"><div class="msg ai">Hello {user_name}! Topic: <b>{s['topic']}</b>. Ready for your dialogue? Click the mic!</div></div>
                <button id="mic" class="btn">🎤 MICROPHONE (SPEAK NOW)</button>
                <button id="stop" class="btn">🛑 FINISH & ANALYZE DIALOGUE</button>
                <div id="report" class="report"></div>
            </div>

            <script>
                const API_KEY = "{api_key}";
                const VOCAB = {v_json};
                const MODE = "{s['mode']}";
                let score = 0; let found = new Set(); let transcript = "";

                const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                rec.lang = 'en-US';

                document.getElementById('mic').onclick = () => {{ try{{rec.start();}}catch(e){{rec.stop();}} }};
                rec.onstart = () => document.getElementById('mic').classList.add('listening');
                rec.onend = () => document.getElementById('mic').classList.remove('listening');

                rec.onresult = async (e) => {{
                    const text = e.results[0][0].transcript;
                    addMsg(text, 'user');
                    transcript += "Student(s): " + text + "\\n";
                    VOCAB.forEach(w => {{ if(text.toLowerCase().includes(w)) {{ found.add(w); score += 50; }} }});
                    score += 10;

                    if (MODE === "Tuteur IA" || MODE === "Dialogue avec un ami") {{
                        let p = (MODE === "Tuteur IA") ? "You are a teacher." : "You are a young friend.";
                        const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                            method: 'POST', headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                            body: JSON.stringify({{ model: "gpt-4o-mini", messages: [
                                {{role: "system", content: p + " Topic: {s['topic']}. Level: {s['level']}. 1 sentence response."}},
                                {{role: "user", content: text}}
                            ] }})
                        }});
                        const d = await r.json(); const reply = d.choices[0].message.content;
                        transcript += "IA: " + reply + "\\n";
                        addMsg(reply, 'ai');
                        window.speechSynthesis.speak(new SpeechSynthesisUtterance(reply));
                    }} else {{
                        addMsg("(Recording dialogue...)", 'ai');
                    }}
                }};

                function addMsg(t, c) {{
                    const d = document.createElement('div'); d.className = 'msg ' + c; d.innerText = t;
                    const chat = document.getElementById('chat'); chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
                }}

                document.getElementById('stop').onclick = async () => {{
                    document.getElementById('stop').innerText = "Processing evaluation...";
                    
                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST', headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{ model: "gpt-4o-mini", messages: [
                            {{role: "system", content: "Tu es un expert FWB. Évalue ce dialogue entre élèves sur '{s['topic']}'. Utilise le TU ou VOUS. Structure: 1. Lexique (/5), 2. Grammaire ({s['grammar']}) (/5), 3. Interaction entre les élèves (/5), 4. Note globale /20. Conseil précis."}},
                            {{role: "user", content: transcript}}
                        ] }})
                    }});
                    const d = await r.json(); const evalu = d.choices[0].message.content;

                    const data = "{user_name}|" + score + "|" + Array.from(found).join(', ') + "|" + evalu.replace(/\\n/g, " ");
                    const bridge = window.parent.document.querySelector('input[aria-label="Bridge"]');
                    if (bridge) {{
                        bridge.value = data;
                        bridge.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        bridge.dispatchEvent(new KeyboardEvent('keydown', {{ keyCode: 13, bubbles: true }}));
                    }}

                    document.getElementById('report').innerText = "SCORE: " + score + "\\n\\n" + evalu;
                    document.getElementById('report').style.display = 'block';
                    document.getElementById('stop').style.display = 'none';
                }};
            </script>
        </body>
        </html>
        """
        st.components.v1.html(html_code, height=750)
