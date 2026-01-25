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

# --- FONCTION PDF (CONFORME PAGE 4 - GRILLE ABCD) ---
def create_pdf(user_name, level, topic, evaluation_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Bilan d'Evaluation Officiel - FWB", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt=f"Eleve : {user_name} | Niveau : {level} | Sujet : {topic}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    # Nettoyage pour format PDF
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
            st.success("Configuration enregistrée.")

    st.divider()
    st.subheader("🔗 Partage")
    qr = qrcode.make("https://tuteur-anglais.streamlit.app") 
    buf = BytesIO(); qr.save(buf)
    st.image(buf, width=150, caption="QR Code Elève")

# --- INTERFACE ÉLÈVE ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    st.title(f"🗣️ {s['topic']}")
    user_name = st.sidebar.text_input("Ton Prénom :")
    
    if not user_name:
        st.info("👈 Entre ton prénom pour commencer.")
    else:
        # Langues micro et synthèse
        rec_l = "en-US" if s['language'] == "English" else "nl-BE"
        tts_l = "en-US" if s['language'] == "English" else "nl-NL"
        
        # PROMPT DE DIALOGUE (Immersion)
        adapt_prompt = f"""Tu es un tuteur de {s['language']} (Niveau {s['level']}). 
        MISSION: {s['custom_prompt']}. PARLE UNIQUEMENT EN {s['language']}.
        Si Niveau Primaire: phrases très courtes.
        CORRECTIONS: Toujours après 'Correction:' en français."""

        html_code = f"""
        <div style="background:#f9f9f9; padding:15px; border-radius:10px; border:1px solid #ddd; text-align:center;">
            <div id="status" style="color:blue; font-weight:bold; margin-bottom:10px;">Système Prêt</div>
            <div id="chat" style="height:250px; overflow-y:auto; margin-bottom:10px; padding:10px; background:white; text-align:left; border:1px solid #eee;"></div>
            <button id="go" style="width:100%; padding:20px; background:#dc3545; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">🎤 CLIQUE ET PARLE</button>
        </div>
        <script>
            const API_KEY = "{st.secrets['OPENAI_API_KEY']}";
            let msgs = [{{role: "system", content: `{adapt_prompt}`}}];
            const btn = document.getElementById('go');
            const chat = document.getElementById('chat');
            const status = document.getElementById('status');
            const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            rec.lang = "{rec_l}";

            async function talk(txt) {{
                status.innerText = "L'IA réfléchit...";
                if(txt) msgs.push({{role: "user", content: txt}});
                else msgs.push({{role: "user", content: "LANCE LA MISSION EN {s['language']}."}});
                
                const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                    body: JSON.stringify({{ model: "gpt-4o-mini", messages: msgs }})
                }});
                const d = await r.json();
                const reply = d.choices[0].message.content;
                msgs.push({{role: "assistant", content: reply}});
                chat.innerHTML += `<p><b>Tuteur:</b> ${{reply.replace('Correction:', '<br><small style="color:red;">Correction:</small>')}}</p>`;
                chat.scrollTop = chat.scrollHeight;
                
                const u = new SpeechSynthesisUtterance(reply.split('Correction:')[0]);
                u.lang = "{tts_l}";
                window.speechSynthesis.speak(u);
                status.innerText = "À toi !";
            }}

            btn.onclick = () => {{
                if(msgs.length === 1) talk(null);
                else {{ rec.start(); status.innerText = "Écoute..."; }}
            }};

            rec.onresult = (e) => {{
                const t = e.results[0][0].transcript;
                chat.innerHTML += `<p style="text-align:right;"><b>Moi:</b> ${{t}}</p>`;
                talk(t);
            }};
        </script>
        """
        st.components.v1.html(html_code, height=480)

        # --- EVALUATION CONFORME GRILLE ABCD PAGE 4 ---
        st.divider()
        trans = st.text_area("Copie le dialogue pour l'évaluation :", height=150)
        if st.button("🏁 Générer mon Bilan Officiel FWB"):
            with st.spinner("Analyse selon la Grille ABCD..."):
                eval_prompt = f"""Tu es un examinateur officiel de la Fédération Wallonie-Bruxelles.
                Evalue {user_name} sur ce dialogue selon les critères ABCD du document fourni.
                Niveau cible: {s['level']}. Sujet: {s['topic']}.
                
                BARÈME MATHÉMATIQUE STRICT (Page 4) :
                - Si A ou B partout : Note sur 20 (>=10/20).
                - 1 x C = 8/20.
                - 2 x C ou 1 x D = 6/20.
                - 3 x C ou 2 x D = 4/20.
                
                TON BILAN DOIT CONTENIR :
                1. Un tableau ABCD pour les 4 critères.
                2. La note sur 20 justifiée par le barème ci-dessus.
                3. Un coaching bienveillant (tutoie l'élève).
                4. 3 pistes de progrès."""
                
                res = client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=[{"role": "user", "content": f"{eval_prompt} Dialogue: {trans}"}]
                )
                bilan_final = res.choices[0].message.content
                st.markdown(bilan_final)
                
                pdf = create_pdf(user_name, s['level'], s['topic'], bilan_final)
                st.download_button("📥 Télécharger mon PDF", pdf, f"Bilan_{user_name}.pdf")
                
                m = s['teacher_email']
                link = f"mailto:{m}?subject=Bilan%20FWB%20{user_name}"
                st.markdown(f'<a href="{link}" target="_blank"><div style="background:#28a745; color:white; padding:15px; border-radius:10px; text-align:center;">📧 Envoyer au professeur</div></a>', unsafe_allow_html=True)
