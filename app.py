import streamlit as st
import qrcode
from io import BytesIO
from fpdf import FPDF
from openai import OpenAI

# 1. CONFIGURATION & MOTEUR
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))

if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English", 
        "level": "Primaire (Initiation/A1)",
        "mode": "Tuteur (Dialogue IA)",
        "topic": "Food and Drinks", 
        "teacher_email": "", 
        "vocab": "Apple, Banana, Milk, I like",
        "custom_prompt": "Fais semblant d'être un serveur dans un café."
    }

# --- FONCTION PDF (Barème Strict Page 4 - Validé) ---
def create_pdf(user_name, level, topic, evaluation_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Bilan d'Evaluation Officiel - FWB", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 8, txt=f"Eleve : {user_name} | Niveau : {level}", ln=True)
    pdf.ln(5)
    clean_text = evaluation_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIQUE DES ROLES ---
if "role" not in st.session_state:
    st.title("🚀 Language Lab FWB")
    c1, c2 = st.columns(2)
    if c1.button("Accès ÉLÈVE"): st.session_state.role = "Élève"; st.rerun()
    if c2.button("Accès PROFESSEUR"): st.session_state.role = "Professeur"; st.rerun()

# --- INTERFACE PROFESSEUR ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Configuration du Laboratoire")
    with st.form("config_pro"):
        col1, col2 = st.columns(2)
        levels = ["Primaire (Initiation/A1)", "S1-S2 (Vers A2.1)", "S3-S4 (Vers A2.2/B1)"]
        lvl = col1.selectbox("Degré / Niveau :", levels, index=levels.index(st.session_state.class_settings["level"]))
        lang = col1.selectbox("Langue :", ["English", "Nederlands"])
        mode = col1.selectbox("Mode d'activité :", ["Tuteur (Dialogue IA)", "Jeu de rôle", "Examen oral"])
        topic = col2.text_input("Sujet thématique :", value=st.session_state.class_settings["topic"])
        mail = col2.text_input("Email prof :", value=st.session_state.class_settings["teacher_email"])
        st.divider()
        voc = st.text_area("Attendus spécifiques :", value=st.session_state.class_settings["vocab"])
        mission = st.text_area("🎯 MISSION DU TUTEUR :", value=st.session_state.class_settings["custom_prompt"])
        
        if st.form_submit_button("✅ Enregistrer et Publier"):
            st.session_state.class_settings.update({
                "language": lang, "level": lvl, "topic": topic, 
                "teacher_email": mail, "vocab": voc, "custom_prompt": mission, "mode": mode
            })
            st.success("Session configurée avec succès !")

    st.divider()
    st.subheader("🔗 Partage avec les élèves")
    qr = qrcode.make("https://votre-app.streamlit.app") # Remplacez par votre URL réelle
    buf = BytesIO()
    qr.save(buf)
    st.image(buf, width=200, caption="Scanner pour accéder au labo")

# --- INTERFACE ÉLÈVE (Correction Langue Forcée) ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    st.title(f"🗣️ {s['topic']}")
    user_name = st.sidebar.text_input("Ton Prénom :")
    
    if not user_name:
        st.warning("👈 Entre ton prénom pour activer le micro.")
    else:
        rec_l = "en-US" if s['language'] == "English" else "nl-BE"
        tts_l = "en-US" if s['language'] == "English" else "nl-NL"
        
        # PROMPT RENFORCÉ : Interdiction stricte du français dans le dialogue
        adapt_prompt = f"""Tu es un tuteur de {s['language']} (Niveau {s['level']}).
        MISSION: {s['custom_prompt']}.
        RÈGLE ABSOLUE: Tu dois parler UNIQUEMENT en {s['language']}. 
        INTERDICTION de répondre en français, même si l'élève te parle en français.
        Si Niveau Primaire: phrases de 3 mots maximum.
        CORRECTIONS: Écris tes corrections en français UNIQUEMENT après le mot 'Correction:'."""

        html_code = f"""
        <div style="background:#f9f9f9; padding:15px; border-radius:10px; border:1px solid #ddd;">
            <div id="status" style="color:blue; font-weight:bold; margin-bottom:5px;">Système prêt</div>
            <div id="chat" style="height:250px; overflow-y:auto; margin-bottom:10px; padding:10px; background:white; border-radius:5px; border:1px solid #eee;"></div>
            <button id="go" style="width:100%; padding:20px; background:#dc3545; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold; font-size:1.1em;">🎤 CLIQUE ET PARLE</button>
        </div>
        <script>
            const API_KEY = "{st.secrets['OPENAI_API_KEY']}";
            let msgs = [{{role: "system", content: `{adapt_prompt}`}}];
            const btn = document.getElementById('go');
            const chat = document.getElementById('chat');
            const status = document.getElementById('status');
            const synth = window.speechSynthesis;
            const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            rec.lang = "{rec_l}";

            async function talk(txt) {{
                status.innerText = "L'IA réfléchit en {s['language']}...";
                if(txt) msgs.push({{role: "user", content: txt}});
                else msgs.push({{role: "user", content: "START MISSION IN {s['language']} NOW."}});
                
                try {{
                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{ model: "gpt-4o-mini", messages: msgs }})
                    }});
                    const d = await r.json();
                    const reply = d.choices[0].message.content;
                    msgs.push({{role: "assistant", content: reply}});
                    
                    chat.innerHTML += `<p style="margin:5px 0;"><b>Tuteur:</b> ${{reply.replace('Correction:', '<br><small style="color:red; font-style:italic;">Correction:</small>')}}</p>`;
                    chat.scrollTop = chat.scrollHeight;
                    
                    const u = new SpeechSynthesisUtterance(reply.split('Correction:')[0]);
                    u.lang = "{tts_l}";
                    synth.speak(u);
                    status.innerText = "À toi de répondre !";
                    btn.innerText = "🎤 CLIQUE ET RÉPONDS";
                }} catch(e) {{ status.innerText = "Erreur réseau."; }}
            }}

            btn.onclick = () => {{
                synth.cancel();
                if(msgs.length === 1) talk(null);
                else {{ 
                    rec.start(); 
                    status.innerText = "Écoute en cours..."; 
                    btn.innerText = "JE T'ÉCOUTE...";
                }}
            }};

            rec.onresult = (e) => {{
                const t = e.results[0][0].transcript;
                chat.innerHTML += `<p style="text-align:right; color:blue; margin:5px 0;"><b>Moi:</b> ${{t}}</p>`;
                talk(t);
            }};
        </script>
        """
        st.components.v1.html(html_code, height=500)

        # --- EVALUATION (Rappel Barème Strict) ---
        st.divider()
        trans = st.text_area("Copie le dialogue pour ton bilan final :")
        if st.button("🏁 Générer mon Bilan FWB"):
            eval_p = f"Examine {user_name} (Niveau {s['level']}) via ABCD. Barème strict: 1xC=8/20, 2xC ou 1xD=6/20. Tutoie l'élève."
            res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": f"{eval_p} Dialogue: {trans}"}])
            st.info(res.choices[0].message.content)
            pdf = create_pdf(user_name, s['level'], s['topic'], res.choices[0].message.content)
            st.download_button("📥 Télécharger le PDF", pdf, f"Bilan_{user_name}.pdf")
