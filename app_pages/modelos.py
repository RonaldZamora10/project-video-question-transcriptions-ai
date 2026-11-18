"""Pestaña de comparación: cómo se comportan los modelos con el banco de preguntas, para elegir el más conveniente."""

import altair as alt
import pandas as pd
import streamlit as st

from videoqa.report import METRIC_LABELS, METRIC_SHORT, MODE_HELP, MODE_LABELS, load_results, outcome, summarize


@st.cache_data(ttl=60)
def get_results() -> pd.DataFrame:
    return load_results()


def choose(model: str) -> None:
    st.session_state.modelo = model
    st.switch_page("app_pages/preguntar.py")


results = get_results()
if results.empty:
    st.info(
        "Todavía no hay modelos evaluados. Con Ollama abierto, ejecuta en la terminal "
        "`python -m videoqa.evaluate --model llama3.2:1b` (y lo mismo con cada modelo que quieras comparar). "
        "Los resultados aparecerán aquí.",
        icon=":material/insights:",
    )
    st.stop()

questions = results.drop_duplicates("id")
n_normal, n_trap = (questions["tipo"] == "normal").sum(), (questions["tipo"] == "trampa").sum()

with st.container(horizontal=True, vertical_alignment="bottom"):
    st.markdown(
        f"Cada modelo respondió las mismas **{len(questions)} preguntas** sobre "
        f"{questions['video'].nunique()} charlas: {n_normal} cuya respuesta está en el video y "
        f"{n_trap} trampa, cuya respuesta **no** está y el modelo debería reconocerlo.",
        width="stretch",
    )
    mode = st.segmented_control(
        "Forma de responder",
        list(MODE_LABELS),
        format_func=MODE_LABELS.get,
        default="rag",
        required=True,
        key="modo_dashboard",
        help=" · ".join(f"{MODE_LABELS[k]}: {v}" for k, v in MODE_HELP.items()),
    )

summary = summarize(results)
summary = summary[summary["configuracion"] == mode].sort_values(
    ["confiabilidad", "latencia_mediana_s"], ascending=[False, True]
)
if summary.empty:
    st.info("No hay resultados para esta forma de responder.", icon=":material/info:")
    st.stop()

best = summary.iloc[0]
fastest = summary.sort_values("latencia_mediana_s").iloc[0]

# ---------------------------------------------------------------- recomendación y tarjetas por modelo
with st.container(border=True):
    with st.container(horizontal=True, vertical_alignment="center"):
        st.markdown(
            f":material/recommend: **Recomendado: {best.modelo}.** Es el más confiable ({best.confiabilidad:.0f} %)"
            + (
                f" y además el más rápido (~{best.latencia_mediana_s:.0f} s por respuesta)."
                if best.modelo == fastest.modelo
                else f". Si prefieres rapidez, {fastest.modelo} responde en ~{fastest.latencia_mediana_s:.0f} s "
                f"frente a ~{best.latencia_mediana_s:.0f} s."
            ),
            width="stretch",
        )
        st.button(f"Usar {best.modelo}", type="primary", icon=":material/check:", on_click=choose, args=(best.modelo,))

for row in summary.itertuples():
    with st.container(border=True):
        name, *cells, action = st.columns([1.3, 1, 1, 1, 1, 1, 0.7], vertical_alignment="center")
        name.markdown(f"**{row.modelo}**")
        for cell, (key, (label, explanation)) in zip(cells, METRIC_SHORT.items(), strict=False):
            value = getattr(row, key)
            cell.metric(label, "—" if pd.isna(value) else f"{value:.0f} %", help=explanation)
        cells[-1].metric("Tiempo típico", f"{row.latencia_mediana_s:.0f} s", help="Mediana de segundos por respuesta.")
        if row.modelo != best.modelo:
            action.button("Usar", key=f"usar_{row.modelo}", on_click=choose, args=(row.modelo,))

# ---------------------------------------------------------------- gráficas
models = list(summary["modelo"])
color = alt.Color("modelo:N", title="Modelo", sort=models, legend=alt.Legend(orient="bottom", title=None))
quality, speed = st.columns(2, gap="large")

with quality:
    st.markdown("**¿Qué tan bien responde?**")
    long = summary.melt(id_vars="modelo", value_vars=list(METRIC_LABELS)[1:], var_name="metrica", value_name="valor")
    long["metrica"] = long["metrica"].map(METRIC_LABELS)
    chart = (
        alt.Chart(long.dropna())
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            y=alt.Y(
                "metrica:N",
                title=None,
                sort=list(METRIC_LABELS.values())[1:],
                axis=alt.Axis(labelLimit=220, labelOverlap=False),
            ),
            yOffset=alt.YOffset("modelo:N", sort=models),
            x=alt.X("valor:Q", title="% de preguntas", scale=alt.Scale(domain=[0, 100])),
            color=color,
            tooltip=[
                alt.Tooltip("modelo:N", title="Modelo"),
                alt.Tooltip("metrica:N", title="Métrica"),
                alt.Tooltip("valor:Q", title="%"),
            ],
        )
        .properties(height=200)
    )
    st.altair_chart(chart, alt="Porcentaje de aciertos de cada modelo en cada métrica")
    worst_trap = summary.sort_values("no_inventa").iloc[0]
    st.caption(
        f"Más alto es mejor. Lo más importante es **no inventar**: {worst_trap.modelo} inventó respuestas en "
        f"{100 - worst_trap.no_inventa:.0f} % de las preguntas trampa."
        if len(summary) > 1 and pd.notna(worst_trap.no_inventa)
        else "Más alto es mejor. Lo más importante es no inventar respuestas que no están en el video."
    )

with speed:
    st.markdown("**¿Cuánto tarda en responder?**")
    timing = results[results["configuracion"] == mode]
    chart = (
        alt.Chart(timing)
        .mark_boxplot(size=28, median={"color": "white"})
        .encode(
            y=alt.Y("modelo:N", title=None, sort=models),
            x=alt.X("latencia_s:Q", title="segundos por respuesta"),
            color=alt.Color("modelo:N", sort=models, legend=None),
        )
        .properties(height=200)
    )
    st.altair_chart(chart, alt="Distribución del tiempo de respuesta de cada modelo")
    st.caption(
        f"La línea blanca es el tiempo típico. {fastest.modelo} es el más rápido "
        f"(~{fastest.latencia_mediana_s:.0f} s). "
        "Las cajas más anchas indican tiempos menos predecibles."
    )

# ---------------------------------------------------------------- pregunta por pregunta
with st.expander("Ver pregunta por pregunta", icon=":material/table_rows:"):
    detail = results[results["configuracion"] == mode].copy()
    detail["resultado"] = detail.apply(outcome, axis=1)
    table = detail.pivot_table(
        index=["pregunta", "tipo"], columns="modelo", values="resultado", aggfunc="first"
    ).reset_index()
    table["tipo"] = table["tipo"].map({"normal": "Está en el video", "trampa": "Trampa"})
    st.dataframe(table, hide_index=True, height=300, column_config={"pregunta": "Pregunta", "tipo": "Tipo"})
    st.caption("“Inventó una respuesta” en una trampa es el error más grave: el modelo afirmó algo que nadie dijo.")
