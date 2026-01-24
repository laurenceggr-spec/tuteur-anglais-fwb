import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO

# 1. CONFIGURATION INITIALE
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
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

# --- LOGIQUE DE SAUVEGARDE (PYTHON) ---
def save_score(data_string):
    try:
        if "|" in data_string:
            parts = data_string.split("|")
            if len(parts) >= 4:
                name, score, words, evalu = parts[0], parts[1], parts[2], parts[3]
                # On évite les doublons si la page rafraîchit
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

# --- AUTHENTIFICATION & ROUTING ---
url_params = st.query_params
if "mode" in url_params and url_params["mode"] == "student":
    st.session_state.authenticated = True
    st.session_state.role = "Élève"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- ECRAN DE CONNEXION ---
if not st.session_state.authenticated:
    st.title("🚀 Language Lab FWB")
    role = st.radio("Accès :", ["Élève", "Professeur"], horizontal=True)
    password = st.text_input("Code d'accès :", type="password")
    if st.button("Se connecter"):
        if (role == "Élève" and password == "ELEC2024") or (role == "Professeur" and password == "ADMIN123"):
            st.session_state.authenticated = True
            st.session_state.role = role
            st.rerun()

# --- ESPACE PROFESSEUR ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Dashboard Enseignant")
    col_l, col_r = st.columns([1, 1.3])
    
    with col_l:
        st.subheader("⚙️ Configuration de la leçon")
        with st.form("settings"):
            lang = st.selectbox("Langue :", ["English", "Nederlands"])
            topic = st.text_input("Sujet de discussion :", value=st.session_state.class_settings["topic"])
            mode = st.selectbox("Mode :", ["Tuteur IA", "Monologue (IA muette)", "Dialogue avec un ami", "Dialogue à deux élèves"])
            lvl = st.selectbox("Niveau :", ["P3-P4", "P5-P6", "S1-S2 (A2.1)", "S3 (A2.2)"])
            gram = st.text_input("Focus Grammaire :", value=st.session_state.class_settings["grammar"])
            voc = st.text_area("Lexique cible (séparé par virgules) :", value=st.session_state.class_settings["vocab"])
            
            if st.form_submit_button("Diffuser la configuration"):
                st.session_state.class_settings.update({
                    "language": lang, "topic": topic, "mode": mode, "level": lvl, "grammar": gram, "vocab": voc
                })
                st.success(f"Session {lang} prête !")

        st.subheader("📲 Accès Élève")
        app_url = "https://tuteur-anglais.streamlit.app" # <--- VÉRIFIE TON URL ICI
        qr = qrcode.make(f"{app_url}/?mode=student")
        buf = BytesIO(); qr.save(buf)
        st.image(buf, width=200, caption="Scannez pour rejoindre")

    with col_r:
        st.subheader("📊 Monitoring en direct")
        # LE BRIDGE : Champ crucial pour la réception des données
        bridge = st.text_input("DataBridge", key="bridge_input", help="Champ technique pour la réception IA")
        if bridge:
            save_score(bridge)
        
        if st.session_state.scores_db:
            df = pd.DataFrame(st.session_state.scores_db)
            st.dataframe(df[['Élève', 'Langue', 'Score', 'Date']], use_container_width=True)
            sel_name = st.selectbox("Consulter l'évaluation de :", df['Élève'].tolist())
            report = df[df['Élève'] == sel_name]['Évaluation'].values[0]
            st.markdown(f"**Rapport Pédagogique :**\n\n{report}")
        else:
            st.info("En attente de la fin de session des élèves...")

    if st.button("Déconnexion"):
        st.session_state.authenticated = False
        st.rerun()

# --- INTERFACE ÉLÈVE ---
else:
    s = st.session_state.class_settings
    st.title(f"🎯 {s['language']} Lab")
    user_name = st.sidebar.text_input("Prénom & Nom :")
    
    if not user_name:
        st.warning("Veuillez entrer votre nom dans la barre latérale pour activer le micro.")
    else:
        v_json = str([w.strip().lower() for w in s["vocab"].split(",") if len(w.strip()) > 2]).replace("'", '"')
        rec_lang = "en-US" if s['language'] == "English" else "nl-BE"
        tts_lang = "en-US" if s['language'] == "English" else "nl-NL"
        
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f6; }}
                .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                #chat {{ height: 300px; overflow-y: auto; border: 1px solid #eee; padding: 15px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 10px; border-radius: 10px; background: #fafafa; }}
                .msg {{ padding: 10px 15px; border-radius: 15px; font-size: 0.95rem; line-height: 1.4; }}
                .user {{ align-self: flex-end; background: #007bff; color: white; border-bottom-right-radius: 2px; }}
                .ai {{ align-self: flex-start; background: #e9ecef; color: #333; border-bottom-left-radius: 2px; }}
                .btn {{ width: 100%; padding: 15px; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; transition: 0.3s; font-size: 1rem; }}
                #mic {{ background: #dc3545; color: white; margin-bottom: 12px; }}
                #stop {{ background: #28a745; color: white; }}
                #report {{ display: none; background: #fff3cd; padding: 20px; border-radius: 10px; margin-top: 20px; border-left: 6px solid #ffc107; white-space: pre-wrap; }}
                .listening {{ background: #218838 !important; animation: pulse 1s infinite; }}
                @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.7; }} 100% {{ opacity: 1; }} }}
            </style>
        </head>
        <body>
            <div class="container">
                <h3 style="margin-top:0; color:#007bff;">{s['language']} Session</h3>
                <p style="font-size:0.85rem; color:#666;"><b>Topic:</b> {s['topic']} | <b>Mode:</b> {s['mode']}</p>
                <div id="chat"><div class="msg ai">Ready! Click the microphone to start speaking.</div></div>
                <button id="mic" class="btn">🎤 CLICK TO SPEAK</button>
                <button id="stop" class="btn">🛑 SEND TO TEACHER</button>
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
                        let sys = (MODE === "Dialogue avec un ami") ? "Informal friend." : "Helpful teacher.";
                        const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                            method: 'POST', headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                            body: JSON.stringify({{ model: "gpt-4o-mini", messages: [
                                {{role: "system", content: sys + " Language: " + LANG + ". Topic: {s['topic']}. Level: {s['level']}. One short sentence response."}},
                                {{role: "user", content: text}}
                            ] }})
                        }});
                        const d = await r.json(); const reply = d.choices[0].message.content;
                        transcript += "IA: " + reply + "\\n";
                        addMsg(reply, 'ai');
                        const u = new SpeechSynthesisUtterance(reply); u.lang = "{tts_lang}";
                        window.speechSynthesis.speak(u);
                    }} else if (MODE === "Dialogue à deux élèves") {{
                        addMsg("(Recording both voices...)", 'ai');
                    }}
                }};

                function addMsg(t, c) {{
                    const d = document.createElement('div'); d.className = 'msg ' + c; d.innerText = t;
                    const chat = document.getElementById('chat'); chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
                }}

                document.getElementById('stop').onclick = async () => {{
                    document.getElementById('stop').innerText = "Analyzing & Sending...";
                    
                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST', headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{ model: "gpt-4o-mini", messages: [
                            {{role: "system", content: "Expert FWB. Évalue cette session en " + LANG + " (Sujet: {s['topic']}). Utilise le TU. Structure: 1. Lexique (/5), 2. Grammaire ({s['grammar']}) (/5), 3. Aisance (/5), 4. Note globale /20. Conseil encourageant."}},
                            {{role: "user", content: transcript}}
                        ] }})
                    }});
                    const d = await r.json(); const evalu = d.choices[0].message.content;

                    // LE BRIDGE : Envoi robuste au dashboard prof
                    const data = "{user_name}|" + score + "|" + Array.from(found).join(', ') + "|" + evalu.replace(/\\n/g, " ");
                    const parentInputs = window.parent.document.querySelectorAll('input');
                    
                    parentInputs.forEach(input => {{
                        if (input.closest('.stTextInput') && input.closest('.stTextInput').innerText.includes("DataBridge")) {{
                            input.value = data;
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new KeyboardEvent('keydown', {{ keyCode: 13, bubbles: true, key: 'Enter' }}));
                        }}
                    }});

                    document.getElementById('report').innerText = "FINAL SCORE: " + score + "\\n\\n" + evalu;
                    document.getElementById('report').style.display = 'block';
                    document.getElementById('stop').style.display = 'none';
                    document.getElementById('mic').style.display = 'none';
                }};
            </script>
        </body>
        </html>
        """
        st.components.v1.html(html_code, height=750)
