import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO

# 1. CONFIGURATION
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
        "min_turns": 5, # NOUVELLE CONTRAINTE
        "grammar": "Present Simple",
        "vocab": "wake up, breakfast, school"
    }

# --- LOGIQUE DE SAUVEGARDE ---
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

# --- INTERFACE PROFESSEUR ---
if st.session_state.get("role") == "Professeur":
    st.title("👨‍🏫 Dashboard Enseignant")
    tab1, tab2 = st.tabs(["⚙️ Configuration", "📊 Résultats & Suivi"])
    
    with tab1:
        with st.form("settings"):
            c1, c2 = st.columns(2)
            lang = c1.selectbox("Langue :", ["English", "Nederlands"])
            lvl = c1.selectbox("Niveau :", ["P3-P4", "P5-P6", "S1-S2", "S3"])
            turns = c2.number_input("Nombre de répliques minimum :", min_value=1, value=5)
            mode = c2.selectbox("Mode :", ["Tuteur IA", "Monologue (IA muette)", "Dialogue avec un ami", "Dialogue à deux élèves"])
            
            topic = st.text_input("Sujet de discussion :", value=st.session_state.class_settings["topic"])
            gram = st.text_input("Objectif Grammaire :", value=st.session_state.class_settings["grammar"])
            voc = st.text_area("Lexique cible (virgules) :", value=st.session_state.class_settings["vocab"])
            
            if st.form_submit_button("Appliquer à la classe"):
                st.session_state.class_settings.update({
                    "language": lang, "topic": topic, "mode": mode, "level": lvl, 
                    "grammar": gram, "vocab": voc, "min_turns": turns
                })
                st.success("Configuration mise à jour !")

        app_url = "https://tuteur-anglais.streamlit.app" 
        qr = qrcode.make(f"{app_url}/?mode=student")
        buf = BytesIO(); qr.save(buf)
        st.image(buf, width=150, caption="QR Code Session")

    with tab2:
        # LE BRIDGE (Cible pour le JS)
        bridge = st.text_input("DataBridge", key="bridge_input")
        if bridge: save_score(bridge)
        
        if st.session_state.scores_db:
            df = pd.DataFrame(st.session_state.scores_db)
            st.dataframe(df[['Élève', 'Score', 'Date']], use_container_width=True)
            sel_name = st.selectbox("Voir l'évaluation :", df['Élève'].tolist())
            st.info(df[df['Élève'] == sel_name]['Évaluation'].values[0])
        else: st.info("Aucune donnée reçue.")

# --- INTERFACE ÉLÈVE ---
elif st.session_state.get("role") == "Élève":
    s = st.session_state.class_settings
    user_name = st.sidebar.text_input("Ton Prénom :")
    
    if not user_name:
        st.warning("⚠️ Entre ton nom à gauche.")
    else:
        v_json = str([w.strip().lower() for w in s["vocab"].split(",") if len(w.strip()) > 2]).replace("'", '"')
        rec_lang = "en-US" if s['language'] == "English" else "nl-BE"
        tts_lang = "en-US" if s['language'] == "English" else "nl-NL"
        
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: sans-serif; background: #f0f2f6; margin: 0; padding: 10px; }}
                .container {{ max-width: 100%; background: white; padding: 15px; border-radius: 12px; }}
                #chat {{ height: 200px; overflow-y: auto; border: 1px solid #eee; padding: 10px; margin-bottom: 10px; display: flex; flex-direction: column; gap: 8px; font-size: 0.9rem; }}
                .msg {{ padding: 8px 12px; border-radius: 12px; }}
                .user {{ align-self: flex-end; background: #007bff; color: white; }}
                .ai {{ align-self: flex-start; background: #e9ecef; }}
                .btn {{ width: 100%; padding: 15px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }}
                #mic {{ background: #dc3545; color: white; margin-bottom: 8px; }}
                #stop {{ background: #ccc; color: white; pointer-events: none; }}
                #stop.ready {{ background: #28a745; pointer-events: auto; }}
                #report {{ display: none; background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 15px; max-height: 300px; overflow-y: auto; border-left: 5px solid #ffc107; font-size: 0.9rem; }}
                .listening {{ background: #218838 !important; animation: p 1s infinite; }}
                @keyframes p {{ 0% {{ opacity:1 }} 50% {{ opacity:0.7 }} 100% {{ opacity:1 }} }}
            </style>
        </head>
        <body>
            <div class="container">
                <p><b>{s['topic']}</b> | <span id="turn-count">0</span>/{s['min_turns']} répliques</p>
                <div id="chat"><div class="msg ai">Ready! Click the mic.</div></div>
                <button id="mic" class="btn">🎤 MICROPHONE</button>
                <button id="stop" class="btn">🛑 ENVOYER AU PROF</button>
                <div id="report"></div>
            </div>

            <script>
                const API_KEY = "{api_key}";
                const VOCAB = {v_json};
                const MIN_TURNS = {s['min_turns']};
                let score = 0; let found = new Set(); let transcript = ""; let turnCount = 0;

                // Fix Son Smartphone : Initier la synthèse sur un clic utilisateur
                let synth = window.speechSynthesis;
                document.getElementById('mic').addEventListener('click', () => {{
                    let ut = new SpeechSynthesisUtterance(""); synth.speak(ut);
                }});

                const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                rec.lang = "{rec_lang}";

                document.getElementById('mic').onclick = () => {{ try{{rec.start();}}catch(e){{rec.stop();}} }};
                rec.onstart = () => document.getElementById('mic').classList.add('listening');
                rec.onend = () => document.getElementById('mic').classList.remove('listening');

                rec.onresult = async (e) => {{
                    const text = e.results[0][0].transcript;
                    addMsg(text, 'user');
                    transcript += "Student: " + text + "\\n";
                    turnCount++;
                    document.getElementById('turn-count').innerText = turnCount;
                    if(turnCount >= MIN_TURNS) document.getElementById('stop').classList.add('ready');

                    VOCAB.forEach(w => {{ if(text.toLowerCase().includes(w)) {{ found.add(w); score += 50; }} }});
                    
                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST', headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{ model: "gpt-4o-mini", messages: [
                            {{role: "system", content: "You are a teacher. Language: {s['language']}. Topic: {s['topic']}. Level: {s['level']}. 1 short sentence."}},
                            {{role: "user", content: text}}
                        ] }})
                    }});
                    const d = await r.json(); const reply = d.choices[0].message.content;
                    transcript += "IA: " + reply + "\\n";
                    addMsg(reply, 'ai');
                    
                    const u = new SpeechSynthesisUtterance(reply); u.lang = "{tts_lang}";
                    synth.speak(u);
                }};

                function addMsg(t, c) {{
                    const d = document.createElement('div'); d.className = 'msg ' + c; d.innerText = t;
                    const chat = document.getElementById('chat'); chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
                }}

                document.getElementById('stop').onclick = async () => {{
                    document.getElementById('stop').innerText = "Analyse...";
                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST', headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{ model: "gpt-4o-mini", messages: [
                            {{role: "system", content: "Expert FWB. Évalue en français. Utilise le TU. Structure: Lexique /5, Grammaire /5, Aisance /5, Note /20. Conseil."}},
                            {{role: "user", content: transcript}}
                        ] }})
                    }});
                    const d = await r.json(); const evalu = d.choices[0].message.content;
                    
                    // BRIDGE : Ciblage ultra-robuste
                    const data = "{user_name}|" + score + "|" + Array.from(found).join(', ') + "|" + evalu.replace(/\\n/g, " ");
                    const inputs = window.parent.document.getElementsByTagName('input');
                    for (let i of inputs) {{
                        if (i.parentElement.innerHTML.includes("DataBridge")) {{
                            i.value = data;
                            i.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            i.dispatchEvent(new KeyboardEvent('keydown', {{ keyCode: 13, bubbles: true, key: 'Enter' }}));
                            break;
                        }}
                    }}

                    document.getElementById('report').innerText = "SCORE: " + score + "\\n\\n" + evalu;
                    document.getElementById('report').style.display = 'block';
                    document.getElementById('stop').style.display = 'none';
                    document.getElementById('mic').style.display = 'none';
                }};
            </script>
        </body>
        </html>
        """
        st.components.v1.html(html_code, height=700)

else:
    st.title("🚀 Language Lab FWB")
    role = st.radio("Accès :", ["Élève", "Professeur"])
    password = st.text_input("Code :", type="password")
    if st.button("Lancer"):
        if role == "Professeur" and password == "ADMIN123":
            st.session_state.role = "Professeur"; st.rerun()
        elif role == "Élève" and password == "ELEC2024":
            st.session_state.role = "Élève"; st.rerun()
