import streamlit as st
import PyPDF2
import pandas as pd
import qrcode
from io import BytesIO

# 1. CONFIGURATION
st.set_page_config(page_title="English & Dutch Lab FWB", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

if "scores_db" not in st.session_state:
    st.session_state.scores_db = []

if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English",
        "level": "S1-S2 (A2.1)",
        "topic": "Daily Routine",
        "mode": "Tuteur IA",
        "grammar": "Present Simple",
        "vocab": "wake up, breakfast, school"
    }

# --- LOGIQUE DU PONT (JS -> PYTHON) ---
def save_score(data_string):
    try:
        if "|" in data_string:
            parts = data_string.split("|")
            if len(parts) >= 4:
                name, score, words, evalu = parts[0], parts[1], parts[2], parts[3]
                if not any(d['Élève'] == name and d['Score'] == score for d in st.session_state.scores_db):
                    st.session_state.scores_db.append({
                        "Élève": name,
                        "Langue": st.session_state.class_settings["language"],
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
    st.title("🚀 Labo de Langues FWB")
    role = st.radio("Rôle :", ["Élève", "Professeur"], horizontal=True)
    password = st.text_input("Code :", type="password")
    if st.button("Se connecter"):
        if (role == "Élève" and password == "ELEC2024") or (role == "Professeur" and password == "ADMIN123"):
            st.session_state.authenticated = True
            st.session_state.role = role
            st.rerun()

# --- ESPACE PROFESSEUR ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Centre de Commande Bilingue")
    col_l, col_r = st.columns([1, 1.2])
    
    with col_l:
        st.subheader("⚙️ Paramètres")
        with st.form("settings"):
            lang = st.selectbox("Langue enseignée :", ["English", "Nederlands"])
            topic = st.text_input("Sujet :", value=st.session_state.class_settings["topic"])
            mode = st.selectbox("Mode :", ["Tuteur IA", "Monologue (IA muette)", "Dialogue avec un ami", "Dialogue à deux élèves"])
            lvl = st.selectbox("Niveau :", ["P3-P4", "P5-P6", "S1-S2 (A2.1)", "S3 (A2.2)"])
            gram = st.text_input("Objectif Grammaire :", value=st.session_state.class_settings["grammar"])
            voc = st.text_area("Lexique imposé :", value=st.session_state.class_settings["vocab"])
            
            if st.form_submit_button("Lancer la session"):
                st.session_state.class_settings.update({
                    "language": lang, "topic": topic, "mode": mode, "level": lvl, "grammar": gram, "vocab": voc
                })
                st.success(f"Session {lang} activée !")

        st.subheader("📲 QR Code")
        app_url = "https://tuteur-anglais.streamlit.app" # À MODIFIER
        qr = qrcode.make(f"{app_url}/?mode=student")
        buf = BytesIO(); qr.save(buf)
        st.image(buf, width=180)

    with col_r:
        st.subheader("📊 Résultats")
        bridge = st.text_input("Bridge", key="bridge_input", label_visibility="collapsed")
        if bridge: save_score(bridge)
        
        if st.session_state.scores_db:
            df = pd.DataFrame(st.session_state.scores_db)
            st.dataframe(df[['Élève', 'Langue', 'Sujet', 'Score', 'Date']], use_container_width=True)
            sel = st.selectbox("Rapport détaillé :", df['Élève'].tolist())
            st.info(df[df['Élève'] == sel]['Évaluation'].values[0])
        else: st.info("Aucun résultat.")

    if st.button("Déconnexion"):
        st.session_state.authenticated = False
        st.rerun()

# --- INTERFACE ÉLÈVE ---
else:
    s = st.session_state.class_settings
    st.title(f"🎯 {'Oefen' if s['language'] == 'Nederlands' else 'Practice'} {s['language']}")
    user_name = st.sidebar.text_input("Naam / Nom :")
    
    if not user_name:
        st.warning("Indique ton nom dans la barre latérale.")
    else:
        v_json = str([w.strip().lower() for w in s["vocab"].split(",") if len(w.strip()) > 2]).replace("'", '"')
        
        # Configuration langues
        rec_lang = "en-US" if s['language'] == "English" else "nl-BE"
        tts_lang = "en-US" if s['language'] == "English" else "nl-NL"
        ai_intro = f"Hello {user_name}! Topic: {s['topic']}" if s['language']=="English" else f"Dag {user_name}! Onderwerp: {s['topic']}"

        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; background: #f0f2f6; }}
                .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                #chat {{ height: 280px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 15px; display: flex; flex-direction: column; gap: 8px; border-radius: 8px; }}
                .msg {{ padding: 10px 14px; border-radius: 12px; font-size: 0.95rem; }}
                .user {{ align-self: flex-end; background: #007bff; color: white; }}
                .ai {{ align-self: flex-start; background: #eee; }}
                .btn {{ width: 100%; padding: 15px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.2s; }}
                #mic {{ background: #dc3545; color: white; margin-bottom: 10px; font-size: 1.1rem; }}
                #stop {{ background: #28a745; color: white; }}
                .report {{ display: none; background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 15px; white-space: pre-wrap; border-left: 5px solid #ffc107; }}
                .listening {{ background: #28a745 !important; animation: p 1s infinite; }}
                @keyframes p {{ 0%{{opacity:1}} 50%{{opacity:0.7}} 100%{{opacity:1}} }}
            </style>
        </head>
        <body>
            <div class="container">
                <h3 style="margin-top:0;">{s['language']} Session</h3>
                <div id="chat"><div class="msg ai">{ai_intro}</div></div>
                <button id="mic" class="btn">🎤 {'CLICK TO SPEAK' if s['language']=='English' else 'KLIK OM TE SPREKEN'}</button>
                <button id="stop" class="btn">🛑 {'FINISH' if s['language']=='English' else 'STOPPEN'}</button>
                <div id="report" class="report"></div>
            </div>

            <script>
                const API_KEY = "{api_key}";
                const VOCAB = {v_json};
                const MODE = "{s['mode']}";
                const LANG = "{s['language']}";
                let score = 0; let found = new Set(); let transcript = "";

                const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                rec.lang = "{rec_lang}";

                document.getElementById('mic').onclick = () => {{ try{{rec.start();}}catch(e){{rec.stop();}} }};
                rec.onstart = () => document.getElementById('mic').classList.add('listening');
                rec.onend = () => document.getElementById('mic').classList.remove('listening');

                rec.onresult = async (e) => {{
                    const text = e.results[0][0].transcript;
                    addMsg(text, 'user');
                    transcript += "Student: " + text + "\\n";
                    VOCAB.forEach(w => {{ if(text.toLowerCase().includes(w)) {{ found.add(w); score += 50; }} }});
                    score += 10;

                    if (MODE !== "Monologue (IA muette)" && MODE !== "Dialogue à deux élèves") {{
                        let p = (MODE === "Dialogue avec un ami") ? "You are a friend." : "You are a teacher.";
                        const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                            method: 'POST', headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                            body: JSON.stringify({{ model: "gpt-4o-mini", messages: [
                                {{role: "system", content: p + " Language: " + LANG + ". Topic: {s['topic']}. Level: {s['level']}. Respond in 1 short sentence."}},
                                {{role: "user", content: text}}
                            ] }})
                        }});
                        const d = await r.json(); const reply = d.choices[0].message.content;
                        transcript += "IA: " + reply + "\\n";
                        addMsg(reply, 'ai');
                        const u = new SpeechSynthesisUtterance(reply); u.lang = "{tts_lang}";
                        window.speechSynthesis.speak(u);
                    }}
                }};

                function addMsg(t, c) {{
                    const d = document.createElement('div'); d.className = 'msg ' + c; d.innerText = t;
                    const cDiv = document.getElementById('chat'); cDiv.appendChild(d); cDiv.scrollTop = cDiv.scrollHeight;
                }}

                document.getElementById('stop').onclick = async () => {{
                    document.getElementById('stop').innerText = "...";
                    
                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST', headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{ model: "gpt-4o-mini", messages: [
                            {{role: "system", content: "Tu es un expert FWB. Évalue cette session en " + LANG + " sur '{s['topic']}'. Utilise le TU. Structure: 1. Lexique (/5), 2. Grammaire ({s['grammar']}) (/5), 3. Aisance (/5), 4. Note globale /20. Conseil précis."}},
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

    if st.sidebar.button("Déconnexion"):
        st.session_state.authenticated = False
        st.rerun()
