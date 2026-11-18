"""Pestaña principal: elegir o agregar un video, elegir el modelo y hacer preguntas."""

import threading

import pandas as pd
import streamlit as st

from videoqa.answer import answer_question, installed_models
from videoqa.config import VIDEO_EXTENSIONS, find_video_file, load_catalog, load_config
from videoqa.index import ensure_index
from videoqa.library import VideoError, download_youtube, list_user_videos, save_upload
from videoqa.report import MODE_HELP, MODE_LABELS, load_results, summarize
from videoqa.transcribe import ensure_transcript, format_timestamp, load_transcript, load_whisper

MAX_UPLOAD_MB = 500  # el video más pesado del dataset ocupa ~340 MB
AUDIO_FORMATS = {".m4a": "audio/mp4", ".mp3": "audio/mpeg", ".wav": "audio/wav"}
SUGGESTIONS = {  # botón corto → pregunta completa que se envía
    "Resumen": "¿De qué trata la charla?",
    "Idea principal": "¿Cuál es la idea principal de la charla?",
    "Ejemplos": "¿Qué ejemplos usa el ponente?",
    "Conclusión": "¿Cómo termina la charla?",
}


# st.cache_resource carga Whisper una sola vez por servidor.
# Fuente: https://docs.streamlit.io/develop/concepts/architecture/caching
@st.cache_resource(show_spinner="Cargando Whisper…")
def get_whisper():
    return load_whisper()


@st.cache_resource
def transcription_jobs() -> dict:
    """Transcripciones en curso, compartidas por todo el servidor: siguen aunque el usuario cambie de pestaña."""
    return {}


def start_transcription(video_id: str, media_path) -> dict:
    """Lanza la transcripción en un hilo aparte (solo una vez por video) y devuelve su estado."""
    jobs = transcription_jobs()
    if video_id not in jobs:
        job = jobs[video_id] = {"progress": 0.0, "done": False, "error": None}
        model = get_whisper()  # se carga aquí: el hilo no puede mostrar mensajes de Streamlit

        def run() -> None:
            try:
                ensure_transcript(video_id, media_path, model, on_progress=lambda value: job.update(progress=value))
            except Exception as error:  # cualquier fallo se muestra al usuario con opción de reintentar
                job["error"] = str(error)
            job["done"] = True

        threading.Thread(target=run, daemon=True).start()
    return jobs[video_id]


@st.fragment(run_every=2)
def transcription_progress(video_id: str) -> None:
    job = transcription_jobs()[video_id]
    if job["done"]:
        st.rerun()
    st.progress(job["progress"], text=f"Transcribiendo el video por primera vez… {job['progress']:.0%}")
    st.caption(
        ":material/info: Solo pasa una vez por video y en este equipo toma unos minutos. "
        "Puedes cambiar de pestaña o de video: la transcripción sigue avanzando."
    )


@st.cache_data(ttl=60)
def model_scores(mode: str) -> dict:
    """Confiabilidad y tiempo típico de cada modelo evaluado, para mostrarlos junto al selector."""
    results = load_results()
    if results.empty:
        return {}
    summary = summarize(results)
    return {row["modelo"]: row for row in summary[summary["configuracion"] == mode].to_dict("records")}


def keep(key: str) -> None:
    """Copia el valor del widget a una clave propia: así sobrevive al cambiar de pestaña."""
    st.session_state[key] = st.session_state[f"_{key}"]


def video_list() -> list[dict]:
    mine = [{**video, "mine": True} for video in list_user_videos() if find_video_file(video["id"])]
    catalog = [
        {"id": video["id"], "title": video["title"], "speaker": video["speaker"], "url": None, "mine": False}
        for video in load_catalog()
        if find_video_file(video["id"])
    ]
    return mine + catalog


@st.dialog("Agregar un video", width="medium")
def add_video() -> None:
    link_tab, file_tab = st.tabs([":material/link: Enlace de YouTube", ":material/upload_file: Archivo de tu equipo"])
    with link_tab:
        url = st.text_input("Pega el enlace del video", placeholder="https://www.youtube.com/watch?v=…")
        if st.button("Agregar", type="primary", icon=":material/add:", key="add_link"):
            with st.spinner("Descargando el audio del video…"):
                try:
                    video = download_youtube(url)
                except VideoError as error:
                    st.error(str(error), icon=":material/error:")
                    return
            st.session_state.pending_video = video["id"]
            st.rerun()
    with file_tab:
        uploaded = st.file_uploader(
            "Video o audio en español",
            type=[extension.lstrip(".") for extension in VIDEO_EXTENSIONS],
            max_upload_size=MAX_UPLOAD_MB,
        )
        st.caption(f"Formatos: MP4, WEBM, MKV, M4A, MP3 o WAV. Máximo {MAX_UPLOAD_MB} MB.")
        if st.button("Agregar", type="primary", icon=":material/add:", key="add_file"):
            if uploaded is None:
                st.error("Primero elige un archivo.", icon=":material/error:")
                return
            st.session_state.pending_video = save_upload(uploaded.name, uploaded.getvalue())["id"]
            st.rerun()
    st.caption(
        ":material/schedule: La primera vez que abras un video se transcribe; en este equipo toma unos minutos. "
        "Después queda guardado."
    )


def ask(question: str) -> None:
    with st.spinner("Buscando en el video y redactando la respuesta…"):
        try:
            st.session_state.result = answer_question(
                question,
                st.session_state.modo,
                st.session_state.transcript,
                st.session_state.collection,
                st.session_state.modelo,
            )
            st.session_state.result_model = st.session_state.modelo
        except ConnectionError as error:
            st.error(str(error), icon=":material/cloud_off:")


def use_suggestion() -> None:
    st.session_state.pending_question = SUGGESTIONS[st.session_state._sugerencia]
    st.session_state._sugerencia = None


def show_answer(result) -> None:
    with st.container(border=True):
        st.markdown(result.text)
        with st.container(horizontal=True, gap="small"):
            st.badge(st.session_state.get("result_model", ""), icon=":material/neurology:", color="gray")
            st.badge(MODE_LABELS[result.mode], icon=":material/tune:", color="gray")
            st.badge(f"{result.latency_seconds} s", icon=":material/timer:", color="gray")
        if result.citations:
            with st.container(horizontal=True, gap="small", vertical_alignment="center"):
                st.caption("Ir al minuto:")
                for seconds in result.citations:
                    st.button(
                        format_timestamp(seconds),
                        key=f"cita_{seconds}",
                        icon=":material/play_circle:",
                        type="tertiary",
                        on_click=st.session_state.update,
                        args=({"start": seconds},),
                    )
        if result.sources:
            with st.expander("Partes del video que usó", icon=":material/segment:"):
                for chunk in result.sources:
                    st.markdown(
                        f"**{format_timestamp(chunk['start'])} – {format_timestamp(chunk['end'])}**  \n{chunk['text']}"
                    )


# ---------------------------------------------------------------- barra lateral: video, modelo y forma de responder
videos = video_list()
by_id = {video["id"]: video for video in videos}
if "pending_video" in st.session_state:  # video recién agregado desde el diálogo
    st.session_state.video = st.session_state.pop("pending_video")
    videos, by_id = video_list(), {video["id"]: video for video in video_list()}
if st.session_state.get("video") not in by_id and videos:
    st.session_state.video = videos[0]["id"]

with st.sidebar:
    st.subheader("Video", icon=":material/smart_display:")
    if videos:
        st.selectbox(
            "Video",
            list(by_id),
            index=list(by_id).index(st.session_state.video),
            format_func=lambda key: ("Mi video: " if by_id[key]["mine"] else "") + by_id[key]["title"],
            key="_video",
            on_change=keep,
            args=("video",),
            label_visibility="collapsed",
        )
    if st.button("Agregar video", icon=":material/add:", width="stretch"):
        add_video()

    st.subheader("Forma de responder", icon=":material/tune:")
    st.session_state.setdefault("modo", "rag")
    st.segmented_control(
        "Forma de responder",
        list(MODE_LABELS),
        format_func=MODE_LABELS.get,
        default=st.session_state.modo,
        required=True,
        key="_modo",
        on_change=keep,
        args=("modo",),
        label_visibility="collapsed",
    )
    st.caption(MODE_HELP[st.session_state.modo])

    st.subheader("Modelo", icon=":material/neurology:")
    models = installed_models()
    scores = model_scores(st.session_state.modo)
    if models:
        configured = load_config()["llm"]["model"]
        if st.session_state.get("modelo") not in models:
            best = max((m for m in models if m in scores), key=lambda m: scores[m]["confiabilidad"] or 0, default=None)
            st.session_state.modelo = best or (configured if configured in models else models[0])

        def describe(model: str) -> str:
            score = scores.get(model)
            if score is None or pd.isna(score["confiabilidad"]):
                return "Sin evaluar"
            return f"{score['confiabilidad']:.0f} % confiable · ~{score['latencia_mediana_s']:.0f} s por respuesta"

        # Radio y no selectbox: con pocos modelos se ven todos a la vez y no hay un campo de texto editable.
        st.radio(
            "Modelo",
            models,
            index=models.index(st.session_state.modelo),
            captions=[describe(model) for model in models],
            key="_modelo",
            on_change=keep,
            args=("modelo",),
            label_visibility="collapsed",
        )
        st.page_link("app_pages/modelos.py", label="¿Cuál me conviene? Ver comparación", icon=":material/insights:")
    else:
        st.warning(
            "Ollama no está abierto o no tiene modelos. Ábrelo y descarga uno, por ejemplo: `ollama pull llama3.2:1b`",
            icon=":material/cloud_off:",
        )

# ---------------------------------------------------------------- contenido principal
if not videos:
    st.info("Todavía no hay videos. Agrega uno desde YouTube o desde tu equipo.", icon=":material/video_library:")
    if st.button("Agregar video", type="primary", icon=":material/add:", key="add_empty"):
        add_video()
    st.stop()

video = by_id[st.session_state.video]
if st.session_state.get("loaded_video") != video["id"]:  # al cambiar de video se olvida la respuesta anterior
    transcript = load_transcript(video["id"])
    if transcript is None:
        job = start_transcription(video["id"], find_video_file(video["id"]))
        if job["error"]:
            st.error(f"No se pudo transcribir el video: {job['error']}", icon=":material/error:")
            if st.button("Reintentar", icon=":material/refresh:"):
                transcription_jobs().pop(video["id"], None)
                st.rerun()
        else:
            transcription_progress(video["id"])
        st.stop()
    with st.spinner("Preparando la búsqueda en el video…"):
        st.session_state.collection = ensure_index(video["id"], transcript)
    st.session_state.update(transcript=transcript, loaded_video=video["id"], start=0, result=None)

player, chat_area = st.columns([6, 5], gap="large")
with player:
    st.markdown(f"**{video['title']}**" + (f"  \n:gray[{video['speaker']}]" if video.get("speaker") else ""))
    media_path = find_video_file(video["id"])
    start = int(st.session_state.start)
    if video.get("url"):
        st.video(video["url"], start_time=start, alt=f"Video: {video['title']}")
    elif media_path.suffix in AUDIO_FORMATS:
        st.audio(str(media_path), AUDIO_FORMATS[media_path.suffix], start_time=start, alt=f"Audio: {video['title']}")
    else:
        st.video(str(media_path), start_time=start, alt=f"Video: {video['title']}")
    with st.expander("Leer la transcripción", icon=":material/description:"):
        st.text(
            "\n".join(f"[{format_timestamp(s['start'])}] {s['text']}" for s in st.session_state.transcript["segments"])
        )

with chat_area:
    with st.form("pregunta", border=False, clear_on_submit=False):
        question = st.text_area(
            "Tu pregunta",
            placeholder="Escribe lo que quieras saber del video…",
            height=80,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Preguntar", type="primary", icon=":material/send:", disabled=not models)
    st.pills(
        "Ideas",
        SUGGESTIONS,
        key="_sugerencia",
        on_change=use_suggestion,
        label_visibility="collapsed",
        disabled=not models,
    )
    pending = st.session_state.pop("pending_question", None)
    if submitted and not question.strip():
        st.caption("Escribe una pregunta antes de enviar.")
    elif submitted or pending:
        ask(pending or question.strip())
    if st.session_state.get("result"):
        show_answer(st.session_state.result)
    else:
        st.caption(
            ":material/info: La respuesta sale solo de lo que se dice en el video y trae el minuto exacto. "
            "Si no está en el video, te lo dirá."
        )
