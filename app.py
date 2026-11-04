"""Interfaz web del sistema. Ejecutar con:  streamlit run app.py"""

import re

import streamlit as st

from videoqa.answer import MODES, answer_question
from videoqa.config import find_video_file, load_catalog, project_path
from videoqa.index import ensure_index
from videoqa.transcribe import ensure_transcript, format_timestamp, load_transcript, load_whisper

MAX_UPLOAD_MB = 500  # el video más pesado del dataset ocupa ~340 MB

st.set_page_config(page_title="Preguntas sobre videos", page_icon="🎥", layout="wide")


# st.cache_resource es la forma recomendada de cargar modelos una sola vez por sesión del servidor.
# Fuente: https://docs.streamlit.io/develop/concepts/architecture/caching
@st.cache_resource(show_spinner="Cargando Whisper…")
def get_whisper():
    return load_whisper()


def prepare_video(video_id: str, media_path) -> tuple[dict, object]:
    """Transcribe (solo la primera vez) e indexa el video. Devuelve la transcripción y su índice."""
    transcript = load_transcript(video_id)
    if transcript is None:
        with st.spinner("Transcribiendo el video con Whisper. En CPU tarda alrededor de un tercio de su duración…"):
            transcript = ensure_transcript(video_id, media_path, get_whisper())
    with st.spinner("Preparando el índice de búsqueda…"):
        collection = ensure_index(video_id, transcript)
    return transcript, collection


def save_upload(uploaded) -> tuple[str, object]:
    """Guarda el archivo subido en data/videos/subidos/ y devuelve su id y su ruta."""
    stem, _, extension = uploaded.name.rpartition(".")
    video_id = "subido_" + (re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")[:40] or "video")
    folder = project_path("uploads")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{video_id}.{extension.lower()}"
    if not path.exists():
        path.write_bytes(uploaded.getbuffer())
    return video_id, path


def choose_video() -> tuple[str, object] | None:
    st.sidebar.header("1. Video")
    st.sidebar.radio("Origen", ["Dataset del proyecto"], label_visibility="collapsed")

    available = [video for video in load_catalog() if find_video_file(video["id"])]
    if not available:
        st.sidebar.warning("No hay videos en data/videos/. Revisa el README.")
        return None
    video = st.sidebar.selectbox(
        "Charla", available, format_func=lambda v: f"{v['id'][:2]}. {v['title']} — {v['speaker']} ({v['duration']})"
    )
    return video["id"], find_video_file(video["id"])


def show_answer(result) -> None:
    st.subheader("Respuesta")
    st.write(result.text)
    st.caption(
        f"{MODES[result.mode]} · {result.latency_seconds} s · "
        f"{result.prompt_tokens} tokens de entrada · {result.output_tokens} de salida"
    )
    if result.citations:
        st.write("Ir al momento citado:")
        columns = st.columns(min(len(result.citations), 6))
        for position, seconds in enumerate(result.citations):
            columns[position % len(columns)].button(
                format_timestamp(seconds),
                key=f"cita_{seconds}",
                on_click=st.session_state.update,
                args=({"start": seconds},),
            )
    if result.sources:
        with st.expander("Fragmentos que recibió el modelo"):
            for chunk in result.sources:
                st.markdown(
                    f"**[{format_timestamp(chunk['start'])} - {format_timestamp(chunk['end'])}]** "
                    f"· similitud {chunk['similarity']}\n\n{chunk['text']}"
                )


def main() -> None:
    st.title("🎥 Preguntas y respuestas sobre videos")
    st.write("Pregunta en lenguaje natural sobre una charla. La respuesta sale **solo** de lo que se dijo en el video.")

    selection = choose_video()
    st.sidebar.header("2. Configuración")
    mode = st.sidebar.radio("Configuración", list(MODES)[:1], format_func=MODES.get, label_visibility="collapsed")
    if selection is None:
        st.info("Elige una charla del dataset o sube un archivo en el panel izquierdo.")
        return

    video_id, media_path = selection
    if st.session_state.get("video_id") != video_id:  # al cambiar de video se olvida la respuesta anterior
        st.session_state.update(video_id=video_id, start=0, result=None)

    transcript, collection = prepare_video(video_id, media_path)
    player, chat_area = st.columns([1, 1])
    with player:
        st.video(str(media_path), start_time=int(st.session_state.start))
        with st.expander("Ver transcripción"):
            st.text("\n".join(f"[{format_timestamp(s['start'])}] {s['text']}" for s in transcript["segments"]))

    with chat_area:
        with st.form("pregunta"):
            question = st.text_input("Tu pregunta", placeholder="¿Qué dice el ponente sobre…?")
            submitted = st.form_submit_button("Preguntar", type="primary")
        if submitted and question.strip():
            with st.spinner("Pensando… puede tardar de 10 a 60 segundos."):
                try:
                    st.session_state.result = answer_question(question.strip(), mode, transcript, collection)
                except ConnectionError as error:
                    st.error(str(error))
        if st.session_state.get("result"):
            show_answer(st.session_state.result)


main()
