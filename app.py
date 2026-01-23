import streamlit as st
import PyPDF2
import pandas as pd
import qrcode
from io import BytesIO

# 1. CONFIGURATION & SÉCURITÉ
st.set_page_config(page_title="English Lab FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

if "scores_db" not in st.session_state:
    st.session_state.scores_db = []

if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "persona": "a supportive British teacher",
        "grammar": "Past Simple",
        "vocab": "yesterday, played, watched, went"
    }

# --- LOGIQUE DU PONT (PYTHON) ---
def save_score(data_string):
    try:
        if "|" in data_string:
            name, score, words = data_string.split("|")
            # Éviter les doublons lors du rafraîchissement
            if not any(d['Élève'] == name and d['Score'] == score for d in st.session_state.scores_db):
                st.session_state.scores_db.append({
                    "Élève": name,
                    "Score": score,
                    "Mots": words,
                    "Date": pd.Timestamp.now().strftime("%H:%M:%S")
                })
    except:
        pass

# --- GESTION DE L'AUTHENTIFICATION ---
url_params = st.query_params
if "mode" in url_params and url_params["mode"] == "student":
    st.session_state.authenticated = True
    st.session_state.role = "Élève"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- ECRAN DE CONNEXION ---
if not st.session_state.authenticated:
    st.title("🚀 English Lab FWB - Plateforme Pro")
    role = st.radio("Je suis :", ["Élève", "Professeur"], horizontal=True)
    password = st.text_input("Code d'accès :", type="password")
    if st.button("Lancer la session"):
        if role == "Élève" and password == "ELEC2024":
            st.session_state.authenticated = True
            st.session_state.role = "Élève"
            st.rerun()
        elif role == "Professeur" and password == "ADMIN123":
            st.session_state.authenticated = True
            st.session_state.role = "Professeur"
            st.rerun()
        else:
            st.error("Code incorrect.")

# --- ESPACE PROFESSEUR ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Dashboard Enseignant")
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        st.subheader("⚙️ Configurer la leçon")
        with st.form("settings"):
            pers = st.text_input("IA Persona :", value=st.session_state.class_settings["persona"])
            gram = st.text_input("Grammaire :", value=st.session_state.class_settings["grammar"])
            voc = st.text_area("Lexique cible :", value=st.session_state.class_settings["vocab"])
            if st.form_submit_button("Mettre à jour la classe"):
                st.session_state.class_settings.update({"persona": pers, "grammar": gram, "vocab": voc})
                st.success("Paramètres mis à jour !")

        st.subheader("📲 QR Code Session")
        app_url = https://https://tuteur-anglais.streamlit.app
        student_url = f"{app_url}/?mode=student"
        qr = qrcode.make(student_url)
        buf = BytesIO()
        qr.save(buf)
        st.image(buf, width=200)
        st.caption("Scannez pour rejoindre")

    with col_right:
        st.subheader("📊 Résultats en direct")
        bridge_data = st.text_input("Bridge", key="bridge_input", label_visibility="collapsed")
        if bridge_data:
            save_score(bridge_data)
        
        if st.session_state.scores_db:
            st.table(pd.DataFrame(st.session_state.scores_db))
        else:
            st.info("Aucun résultat reçu.")

    if st.button("Déconnexion"):
        st.session_state.authenticated = False
        st.rerun()

# --- INTERFACE ÉLÈVE ---
else:
    st.title("🎯 English Lab Session")
    user_name = st.sidebar.text_input("Prénom & Nom :")
    
    if not user_name:
        st.info("👋 Bienvenue ! Entre ton nom dans la barre latérale pour commencer.")
    else:
        s = st.session_state.class_settings
        v_list = str([w.strip().lower() for w in s["vocab"].split(",") if len(w.strip()) > 2]).replace("'", '"')

        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f6; }}
                .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                #chat {{ height: 250px; overflow-y: auto; border: 1px solid #eee; padding: 10px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 8px; border-radius: 8px; }}
                .msg {{ padding: 10px; border-radius: 10px; font-size: 0.9rem; }}
                .user {{ align-self: flex-end; background: #007bff; color: white; }}
                .ai {{ align-self: flex-start; background: #f1f1f1; color: #333; }}
                .btn {{ width: 100%; padding: 12px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; margin-bottom: 10px; transition: 0.3s; }}
                #mic {{ background: #dc3545; color: white; }}
                #stop {{ background: #28a745; color: white; }}
                #result-card {{ display: none; background: #fff3cd; border: 1px solid #ffeeba; padding: 15px; border-radius: 10px; margin-top: 20px; border-left: 5px solid #ffc107; }}
                .found-word {{ display: inline-block; background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 5px; margin: 2px; font-size: 0.8rem; }}
                .listening {{ animation: pulse 1.5s infinite; background: #28a745 !important; }}
                @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.7; }} 100% {{ opacity: 1; }} }}
            </style>
        </head>
        <body>
            <div class="container">
                <h3 style="margin-top:0;">Hi {user_name}! 🚀</h3>
                <div style="font-size: 0.8rem; margin-bottom: 10px; color: #666;">
                    <b>Target:</b> {s['grammar']} | <b>Teacher:</b> {s['persona']}
                </div>
                
                <div id="chat"><div class="msg ai">I'm ready! Let's practice. Click the mic!</div></div>
                
                <button id="mic" class="btn">🎤 CLICK TO SPEAK</button>
                <button id="stop" class="btn">🛑 STOP & GET RESULTS</button>

                <div id="result-card">
                    <h4 style="margin:0 0 10px 0;">🎉 Great job! Your Results:</h4>
                    <p><b>Total Score:</b> <span id="final-score">0</span> pts</p>
                    <p><b>Vocabulary used:</b> <br> <div id="words-used"></div></p>
                    <hr>
                    <p id="ai-feedback" style="font-style: italic; font-size: 0.9rem;"></p>
                </div>
            </div>

            <script>
                const API_KEY = "{api_key}";
                const VOCAB = {v_list};
                let score = 0; let found = new Set(); let transcript = "";

                const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                rec.lang = 'en-US';

                document.getElementById('mic').onclick = () => {{ try {{ rec.start(); }} catch(e) {{ rec.stop(); }} }};
                rec.onstart = () => document.getElementById('mic').classList.add('listening');
                rec.onend = () => document.getElementById('mic').classList.remove('listening');

                rec.onresult = async (e) => {{
                    const text = e.results[0][0].transcript;
                    addMsg(text, 'user');
                    transcript += "Student: " + text + "\\n";
                    
                    VOCAB.forEach(w => {{ if(text.toLowerCase().includes(w)) {{ found.add(w); score += 50; }} }});
                    score += 10;

                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{
                            model: "gpt-4o-mini",
                            messages: [
                                {{role: "system", content: "You are {s['persona']}. Target grammar: {s['grammar']}. Short response + question."}},
                                {{role: "user", content: text}}
                            ]
                        }})
                    }});
                    const d = await r.json();
                    const reply = d.choices[0].message.content;
                    transcript += "Tutor: " + reply + "\\n";
                    addMsg(reply, 'ai');
                    const u = new SpeechSynthesisUtterance(reply); u.lang = 'en-US'; window.speechSynthesis.speak(u);
                }};

                function addMsg(t, c) {{
                    const d = document.createElement('div'); d.className = 'msg ' + c; d.innerText = t;
                    const chat = document.getElementById('chat'); chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
                }}

                document.getElementById('stop').onclick = async () => {{
                    document.getElementById('mic').disabled = true;
                    document.getElementById('stop').innerText = "Analyzing...";
                    
                    // 1. Envoi au professeur (Bridge)
                    const data = "{user_name}|" + score + "|" + Array.from(found).join(', ');
                    const inputs = window.parent.document.querySelectorAll('input');
                    for (let i of inputs) {{
                        if (i.type === "text") {{
                            i.value = data;
                            i.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            i.dispatchEvent(new KeyboardEvent('keydown', {{ keyCode: 13, bubbles: true }}));
                            break;
                        }}
                    }}

                    // 2. Génération du feedback pour l'élève
                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{
                            model: "gpt-4o-mini",
                            messages: [
                                {{role: "system", content: "Tu es un tuteur d'anglais expert. Analyse la session de l'élève. Donne 2 points positifs et 1 conseil pour progresser sur la grammaire ({s['grammar']}). Sois très bref et encourageant. Réponds en FRANCAIS."}},
                                {{role: "user", content: transcript}}
                            ]
                        }})
                    }});
                    const d = await r.json();
                    
                    // Affichage des résultats
                    document.getElementById('final-score').innerText = score;
                    const wDiv = document.getElementById('words-used');
                    found.forEach(w => {{
                        const s = document.createElement('span'); s.className = 'found-word'; s.innerText = w;
                        wDiv.appendChild(s);
                    }});
                    document.getElementById('ai-feedback').innerText = d.choices[0].message.content;
                    document.getElementById('result-card').style.display = 'block';
                    document.getElementById('stop').style.display = 'none';
                }};
            </script>
        </body>
        </html>
        """
        st.components.v1.html(html_code, height=750)

    if st.sidebar.button("Déconnexion"):
        st.session_state.authenticated = False
        st.query_params.clear()
        st.rerun()
