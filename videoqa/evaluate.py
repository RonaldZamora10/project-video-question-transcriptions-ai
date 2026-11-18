"""Evaluación de las configuraciones A (con RAG) y B (sin RAG), según el Entregable 1 §6.2 y §6.3.

Uso:
    python -m videoqa.evaluate              # responde todas las preguntas de data/eval/preguntas.yaml en A y B
    python -m videoqa.evaluate --summary    # solo recalcula el resumen (por ejemplo, después de calificar a mano)
    python -m videoqa.evaluate --model qwen2.5:1.5b   # evalúa otro modelo de Ollama (por defecto, el de config.yaml)

Salidas en data/analisis/ (una pareja de archivos por modelo, p. ej. respuestas_eval_llama3.2_1b.csv):
    respuestas_eval_<modelo>.csv   una fila por pregunta y configuración. Trae columnas vacías para la rúbrica humana
                          (correctitud y fidelidad de 0 a 2, alucinación sí/no) que el equipo llena en Excel.
    resumen_eval_<modelo>.csv      métricas por configuración.

Métricas automáticas (no dependen de la opinión de nadie):
    - rechazo_correcto: en preguntas trampa, ¿respondió "No encuentro esto en el video"?
    - rechazo_indebido: en preguntas normales, ¿dijo que no estaba cuando sí estaba?
    - recuperacion_acierta (solo A): ¿algún fragmento recuperado contiene el minuto de la respuesta?
    - cita_cercana: ¿alguna cita [mm:ss] está cerca del minuto de la respuesta de referencia?
    - latencia y tokens de entrada.
"""

import argparse
import csv
import re
import statistics

import yaml

from videoqa.answer import MODES, answer_question
from videoqa.config import load_config, project_path
from videoqa.index import ensure_index
from videoqa.quality import save_csv
from videoqa.transcribe import load_transcript

HUMAN_COLUMNS = ["correctitud_0a2", "fidelidad_0a2", "alucinacion_si_no", "observaciones"]
_NON_WORD = re.compile(r"[^\w\s]")


def to_seconds(timestamp: str) -> int:
    minutes, seconds = timestamp.split(":")
    return int(minutes) * 60 + int(seconds)


def is_refusal(answer_text: str, not_found: str) -> bool:
    """¿La respuesta dice que la información no está en el video? (ignora mayúsculas y puntuación)."""

    def simplify(text: str) -> str:
        return " ".join(_NON_WORD.sub(" ", text.lower()).split())

    return simplify(not_found) in simplify(answer_text)


def retrieval_hit(sources: list[dict], target: int, tolerance: int) -> bool:
    return any(chunk["start"] - tolerance <= target <= chunk["end"] + tolerance for chunk in sources)


def citation_hit(citations: list[float], target: int, tolerance: int) -> bool:
    return any(abs(citation - target) <= tolerance for citation in citations)


def load_questions() -> list[dict]:
    with open(project_path("eval_questions"), encoding="utf-8") as file:
        return yaml.safe_load(file)


def evaluate_question(question: dict, mode: str, transcript: dict, collection) -> dict:
    settings = load_config()
    result = answer_question(question["question"], mode, transcript, collection)
    refused = is_refusal(result.text, settings["llm"]["not_found_answer"])
    is_trap = question["type"] == "trampa"
    target = None if is_trap else to_seconds(question["minute"])
    tolerance = settings["evaluation"]
    return {
        "id": question["id"],
        "video": question["video"],
        "tipo": question["type"],
        "configuracion": mode,
        "pregunta": question["question"],
        "respuesta_referencia": question.get("reference", ""),
        "minuto_referencia": question.get("minute", ""),
        "respuesta": result.text,
        "citas": " ".join(f"{int(c) // 60:02d}:{int(c) % 60:02d}" for c in result.citations),
        "rechazo_correcto": refused if is_trap else "",
        "rechazo_indebido": "" if is_trap else refused,
        "recuperacion_acierta": (
            retrieval_hit(result.sources, target, tolerance["retrieval_tolerance_seconds"])
            if mode == "rag" and not is_trap
            else ""
        ),
        "cita_cercana": ""
        if is_trap
        else citation_hit(result.citations, target, tolerance["citation_tolerance_seconds"]),
        "latencia_s": result.latency_seconds,
        "tokens_entrada": result.prompt_tokens,
        **dict.fromkeys(HUMAN_COLUMNS, ""),
    }


def _as_bool(value) -> bool | None:
    """Interpreta True/False del script y sí/no escritos a mano en Excel. Vacío = sin dato."""
    text = str(value).strip().lower()
    if text in ("true", "si", "sí"):
        return True
    if text in ("false", "no"):
        return False
    return None


def _rate(rows: list[dict], column: str) -> str:
    values = [flag for flag in (_as_bool(row[column]) for row in rows) if flag is not None]
    return f"{100 * sum(values) / len(values):.0f}% (n={len(values)})" if values else ""


def _mean(rows: list[dict], column: str) -> str:
    values = [float(row[column]) for row in rows if str(row[column]).strip()]
    return f"{statistics.mean(values):.2f} (n={len(values)})" if values else ""


def summarize(rows: list[dict]) -> list[dict]:
    summary = []
    for mode in MODES:
        subset = [row for row in rows if row["configuracion"] == mode]
        if not subset:
            continue
        latencies = [float(row["latencia_s"]) for row in subset]
        summary.append(
            {
                "configuracion": MODES[mode],
                "respuestas": len(subset),
                "latencia_media_s": round(statistics.mean(latencies), 1),
                "latencia_mediana_s": round(statistics.median(latencies), 1),
                "rechazo_correcto_trampas": _rate(subset, "rechazo_correcto"),
                "rechazo_indebido_normales": _rate(subset, "rechazo_indebido"),
                "recuperacion_acierta": _rate(subset, "recuperacion_acierta"),
                "cita_cercana": _rate(subset, "cita_cercana"),
                "correctitud_media_0a2": _mean(subset, "correctitud_0a2"),
                "fidelidad_media_0a2": _mean(subset, "fidelidad_0a2"),
                "alucinaciones": _rate(subset, "alucinacion_si_no"),
            }
        )
    return summary


def run_all() -> list[dict]:
    rows = []
    questions = load_questions()
    for position, question in enumerate(questions, start=1):
        transcript = load_transcript(question["video"])
        if transcript is None:
            print(f"{question['id']}: falta la transcripción de {question['video']}, se omite")
            continue
        collection = ensure_index(question["video"], transcript)
        for mode in MODES:
            row = evaluate_question(question, mode, transcript, collection)
            rows.append(row)
            progress = f"[{position}/{len(questions)}] {question['id']} {mode}"
            print(f"{progress}: {row['latencia_s']} s · {row['respuesta'][:80]}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalúa las configuraciones A y B con el banco de preguntas.")
    parser.add_argument("--summary", action="store_true", help="solo recalcular el resumen del modelo")
    parser.add_argument("--model", help="modelo de Ollama a evaluar (por defecto, el de config.yaml)")
    args = parser.parse_args()

    if args.model:
        load_config()["llm"]["model"] = args.model  # load_config está en caché: answer_question lee este mismo dict
    model = load_config()["llm"]["model"]
    name = re.sub(r"[^\w.-]", "_", model)  # "llama3.2:1b" -> "llama3.2_1b" (":" no es válido en Windows)
    answers_path = project_path("reports") / f"respuestas_eval_{name}.csv"
    if args.summary:
        with open(answers_path, encoding="utf-8-sig") as file:
            rows = list(csv.DictReader(file))
    else:
        rows = [{**row, "modelo": model} for row in run_all()]
        save_csv(rows, answers_path)
    summary = summarize(rows)
    for row in summary:
        row["modelo"] = model
    save_csv(summary, project_path("reports") / f"resumen_eval_{name}.csv")
    for row in summary:
        print(row)


if __name__ == "__main__":
    main()
