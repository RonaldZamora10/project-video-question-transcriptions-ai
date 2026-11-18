"""Interfaz web del sistema. Ejecutar con:  streamlit run app.py

Dos pestañas: "Preguntar" (app_pages/preguntar.py) y "Comparar modelos" (app_pages/modelos.py).
"""

import streamlit as st

from videoqa.config import load_config

st.set_page_config(page_title="Preguntas sobre videos", page_icon=":material/smart_display:", layout="wide")

# Streamlit no tiene opción de idioma: estos textos propios suyos se traducen o se ocultan con CSS.
# shortcut: depende de los data-testid internos de Streamlit 1.65; revisar si se actualiza Streamlit.
st.html(
    """
<style>
  [data-testid="stStatusWidget"] { display: none; }
  [data-testid="stFileUploaderDropzoneInstructions"] span,
  [data-testid="stFileUploaderDropzoneInstructions"] small { display: none; }
  [data-testid="stFileUploaderDropzoneInstructions"] > div::after {
    content: "Arrastra aquí el archivo"; font-size: 0.95rem;
  }
  [data-testid="stFileUploaderDropzone"] button p { font-size: 0; }
  [data-testid="stFileUploaderDropzone"] button p::after { content: "Buscar archivo"; font-size: 0.875rem; }
</style>
"""
)

page = st.navigation(
    [
        st.Page("app_pages/preguntar.py", title="Preguntar", icon=":material/forum:", default=True),
        st.Page("app_pages/modelos.py", title="Comparar modelos", icon=":material/insights:"),
    ],
    position="top",
)
page.run()

with st.sidebar:
    st.space("medium")
    with st.expander("Acerca del proyecto", icon=":material/school:"):
        settings = load_config()
        st.markdown(
            "Proyecto de **Sistemas Inteligentes**, Universidad ECCI. Responde preguntas sobre una charla usando "
            "solo lo que se dijo en ella.\n\n"
            f"1. **Whisper {settings['whisper']['model']}** convierte el audio en texto con el minuto de cada frase.\n"
            "2. El texto se divide en fragmentos de ~120 palabras.\n"
            f"3. **{settings['embeddings']['model'].split('/')[-1]}** representa el significado de cada fragmento.\n"
            "4. **ChromaDB** encuentra los fragmentos más parecidos a tu pregunta.\n"
            "5. Un **modelo de lenguaje local** (Ollama) redacta la respuesta y cita el minuto.\n\n"
            ":material/lock: Todo se procesa en este equipo; solo se usa internet para descargar videos de YouTube."
        )
