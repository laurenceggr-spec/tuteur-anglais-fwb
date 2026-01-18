response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}]
    )
    st.success("Connexion réussie avec OpenAI !")
    st.write(response.choices[0].message.content)
except Exception as e:
    st.error(f"La clé API est refusée par OpenAI. Erreur : {e}")
