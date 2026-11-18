"""Comparación de modelos para la interfaz: lee data/analisis/respuestas_eval_<modelo>.csv y resume su comportamiento.

Las métricas salen de la evaluación automática (python -m videoqa.evaluate --model <modelo>):
    no_inventa         en preguntas trampa, ¿dijo "No encuentro esto en el video" en vez de inventar?
    responde_si_sabe   en preguntas normales, ¿respondió en vez de decir que no estaba?
    cita_correcta      en preguntas normales, ¿citó un minuto cercano al de la respuesta correcta?
    confiabilidad      promedio de las tres anteriores (0 a 100).
"""

import pandas as pd

from videoqa.config import project_path
from videoqa.evaluate import _as_bool

MODE_LABELS = {"rag": "Con búsqueda", "completo": "Texto completo"}
MODE_HELP = {
    "rag": "Busca los fragmentos del video que más se parecen a tu pregunta y responde solo con ellos.",
    "completo": "Lee la transcripción entera antes de responder, sin buscar fragmentos.",
}
# Nombre corto para las tarjetas y explicación para la ayuda (?) de cada una.
METRIC_SHORT = {
    "confiabilidad": ("Confiabilidad", "Promedio de las tres métricas siguientes."),
    "no_inventa": ("No inventa", "En preguntas cuya respuesta no está en el video, reconoce que no la encuentra."),
    "responde_si_sabe": ("Responde", "En preguntas cuya respuesta sí está en el video, responde en vez de rendirse."),
    "cita_correcta": ("Cita bien", "Señala un minuto cercano al lugar del video donde está la respuesta."),
}
METRIC_LABELS = {
    "confiabilidad": "Confiabilidad",
    "no_inventa": "No inventa respuestas",
    "responde_si_sabe": "Responde cuando sí sabe",
    "cita_correcta": "Cita el minuto correcto",
}


def load_results() -> pd.DataFrame:
    """Todas las respuestas evaluadas, de todos los modelos, en una sola tabla."""
    frames = []
    for path in sorted(project_path("reports").glob("respuestas_eval_*.csv")):
        frame = pd.read_csv(path, encoding="utf-8-sig", dtype=str).fillna("")
        if "modelo" not in frame.columns:  # archivos generados antes de guardar el modelo en cada fila
            summary = path.with_name(path.name.replace("respuestas_eval_", "resumen_eval_"))
            names = pd.read_csv(summary, encoding="utf-8-sig").get("modelo") if summary.exists() else None
            frame["modelo"] = names.iloc[0] if names is not None else path.stem.removeprefix("respuestas_eval_")
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    results = pd.concat(frames, ignore_index=True)
    results["latencia_s"] = results["latencia_s"].astype(float)
    return results


def _percent(values: pd.Series) -> float | None:
    flags = values.map(_as_bool).dropna()
    return round(100 * flags.astype(bool).mean()) if len(flags) else None


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    """Una fila por modelo y configuración con las métricas en porcentaje y la latencia típica."""
    rows = []
    for (model, mode), group in results.groupby(["modelo", "configuracion"]):
        normal, trap = group[group["tipo"] == "normal"], group[group["tipo"] == "trampa"]
        wrong_refusals = _percent(normal["rechazo_indebido"])
        row = {
            "modelo": model,
            "configuracion": mode,
            "no_inventa": _percent(trap["rechazo_correcto"]),
            "responde_si_sabe": None if wrong_refusals is None else 100 - wrong_refusals,
            "cita_correcta": _percent(normal["cita_cercana"]),
            "latencia_mediana_s": round(group["latencia_s"].median(), 1),
            "preguntas": len(group),
        }
        scores = [row[key] for key in ("no_inventa", "responde_si_sabe", "cita_correcta") if row[key] is not None]
        row["confiabilidad"] = round(sum(scores) / len(scores)) if scores else None
        rows.append(row)
    return pd.DataFrame(rows)


def outcome(row: pd.Series) -> str:
    """Resultado de una respuesta en palabras simples, para la tabla pregunta por pregunta."""
    if row["tipo"] == "trampa":
        return "No inventó" if _as_bool(row["rechazo_correcto"]) else "Inventó una respuesta"
    if _as_bool(row["rechazo_indebido"]):
        return "Dijo que no estaba"
    return "Respondió y citó bien" if _as_bool(row["cita_cercana"]) else "Respondió, cita lejana"
