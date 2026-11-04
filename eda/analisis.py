"""EDA del Entregable 2. Uso, desde la raíz del proyecto: python eda/analisis.py && python eda/graficos.py

 sobre las transcripciones reales del proyecto (usa las funciones del propio proyecto)."""
import json
import re
import sys
import types
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jiwer

ROOT = Path(__file__).resolve().parent.parent  # carpeta raíz del proyecto
OUT = ROOT / "eda" / "out"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT))
try:
    import chromadb  # noqa: F401
    import sentence_transformers  # noqa: F401
except ImportError:
    # index.py importa chromadb y sentence-transformers solo para indexar; build_chunks no los usa.
    for name in ["chromadb", "chromadb.api", "chromadb.api.models", "chromadb.api.models.Collection",
                 "chromadb.config", "sentence_transformers"]:
        sys.modules[name] = types.SimpleNamespace(Collection=object, Settings=object, SentenceTransformer=object,
                                                  ClientAPI=object)
from videoqa.clean import count_fillers, count_words  # noqa: E402
from videoqa.index import build_chunks  # noqa: E402
from videoqa.quality import normalize_for_wer, read_vtt  # noqa: E402

cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
catalog = yaml.safe_load((ROOT / "data/videos.yaml").read_text(encoding="utf-8"))
questions = yaml.safe_load((ROOT / "data/eval/preguntas.yaml").read_text(encoding="utf-8"))
quality = pd.read_csv(ROOT / "data/analisis/calidad_small.csv", encoding="utf-8-sig")
SIZES_MB = {p.stem: round(p.stat().st_size / 1e6, 1) for p in (ROOT / "data/videos").glob("*.mp4")}

res = {}

# ---- Catálogo (8 videos) ----
def mmss(s):
    m, x = s.split(":")
    return int(m) + int(x) / 60

cat = pd.DataFrame([{**v, "duracion_min": round(mmss(v["duration"]), 2), "tamano_mb": SIZES_MB.get(v["id"], float("nan")),
                     "fuente": "TED" if "ted.com" in v["url"] else "YouTube (TEDx)"} for v in catalog])
trans = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "data/transcripts/small").glob("*.json"))}
cat["transcrito"] = cat["id"].isin(trans)
cat["referencia_ted"] = cat["id"].apply(lambda i: (ROOT / f"data/referencias/{i}.es.vtt").exists())
res["catalogo"] = cat.drop(columns=["url"]).to_dict("records")
res["catalogo_resumen"] = {
    "videos": len(cat), "minutos_total": round(cat.duracion_min.sum(), 1), "gb_total": round(cat.tamano_mb.sum() / 1000, 2),
    "duracion": cat.duracion_min.describe().round(2).to_dict(),
    "transcritos": int(cat.transcrito.sum()), "faltantes": cat.loc[~cat.transcrito, "id"].tolist(),
    "pct_faltantes": round(100 * (~cat.transcrito).mean(), 1),
    "con_referencia": int(cat.referencia_ted.sum()),
}

# ---- Segmentos (unidad de registro del dataset) ----
rows = []
for vid, t in trans.items():
    for i, s in enumerate(t["segments"]):
        rows.append({"video": vid, "i": i, "start": s["start"], "end": s["end"], "dur": round(s["end"] - s["start"], 2),
                     "text": s["text"], "raw": s["raw"], "palabras": count_words(s["text"]),
                     "palabras_raw": count_words(s["raw"]), "caracteres": len(s["text"])})
seg = pd.DataFrame(rows)
seg["gap"] = seg.groupby("video")["start"].shift(-1) - seg["end"]
res["segmentos"] = {
    "total": len(seg), "variables": ["video", "start", "end", "text", "raw"],
    "por_video": seg.groupby("video").size().to_dict(),
    "palabras": seg.palabras.describe().round(2).to_dict(),
    "duracion_s": seg.dur.describe().round(2).to_dict(),
    "caracteres": seg.caracteres.describe().round(2).to_dict(),
}

# Calidad: faltantes / vacíos
res["faltantes"] = {
    "texto_vacio": int((seg.text.str.strip() == "").sum()),
    "raw_vacio": int((seg.raw.str.strip() == "").sum()),
    "nulos_por_campo": seg[["start", "end", "text", "raw"]].isna().sum().to_dict(),
    "segmentos_menos_3_palabras": int((seg.palabras < 3).sum()),
    "ejemplos_cortos": seg.loc[seg.palabras < 3, ["video", "start", "text"]].head(8).to_dict("records"),
}

# Duplicados
norm = seg.text.str.lower().str.replace(r"[^\w\s]", "", regex=True).str.strip()
dup_mask = norm.duplicated(keep=False)
res["duplicados"] = {
    "segmentos_texto_identico": int(norm.duplicated().sum()),
    "pct": round(100 * norm.duplicated().mean(), 2),
    "ejemplos": seg.loc[dup_mask, ["video", "start", "text"]].head(10).to_dict("records"),
    "repeticiones_palabra_quitadas": int((seg.palabras_raw - seg.palabras).sum()),
}

# Atípicos (IQR sobre palabras y duración del segmento; z-score sobre palabras/min por video)
def iqr(s):
    q1, q3 = s.quantile([.25, .75])
    lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    return round(lo, 2), round(hi, 2), s[(s < lo) | (s > hi)]

lo, hi, out_w = iqr(seg.palabras)
lo2, hi2, out_d = iqr(seg.dur)
q = quality.set_index("id")
z = ((q.palabras_por_minuto - q.palabras_por_minuto.mean()) / q.palabras_por_minuto.std(ddof=0)).round(2)
res["atipicos"] = {
    "palabras_seg": {"lim": [lo, hi], "n": len(out_w), "pct": round(100 * len(out_w) / len(seg), 1),
                     "max_ejemplos": seg.loc[out_w.index].nlargest(3, "palabras")[["video", "start", "palabras", "dur"]].to_dict("records")},
    "duracion_seg": {"lim": [lo2, hi2], "n": len(out_d), "pct": round(100 * len(out_d) / len(seg), 1),
                     "max_ejemplos": seg.loc[out_d.index].nlargest(3, "dur")[["video", "start", "palabras", "dur", "text"]].to_dict("records")},
    "z_ppm": z.to_dict(),
    "pausas_mayores_10s": seg.loc[seg.gap > 10, ["video", "end", "gap"]].round(1).to_dict("records"),
}

# Consistencia
allowed = re.compile(r"[\wáéíóúüñÁÉÍÓÚÜÑ\s.,;:!?¡¿'\"()%$/-]")
weird = Counter(c for t in seg.text for c in t if not allowed.match(c))
res["consistencia"] = {
    "fin_menor_inicio": int((seg.end < seg.start).sum()),
    "solapes_tiempo": int((seg.gap < 0).sum()),
    "caracteres_raros": dict(weird.most_common(10)),
    "idioma": {v: (t["language"], t["language_probability"]) for v, t in trans.items()},
    "duracion_whisper_vs_catalogo_s": {v: round(t["duration_seconds"] - mmss(cat.set_index("id").loc[v, "duration"]) * 60, 1)
                                       for v, t in trans.items()},
    "numeros_en_digitos": int(seg.text.str.count(r"\d+").sum()),
    "segmentos_con_numero_en_letras": int(seg.text.str.contains(r"\b(?:mil|millones|cien|cincuenta|treinta|veinte)\b", case=False).sum()),
    "fin_sin_puntuacion": round(100 * (~seg.text.str.strip().str[-1].isin(list(".?!"))).mean(), 1),
}
# Alucinaciones típicas de Whisper (frases de cierre de subtítulos)
hallu = seg.text.str.contains(r"subt[ií]tulos|amara|suscr[ií]bete|gracias por ver", case=False)
res["consistencia"]["frases_tipicas_alucinacion"] = seg.loc[hallu, ["video", "start", "text"]].to_dict("records")

# ---- Por video (univariado) ----
pv = quality[["id", "minutos", "palabras", "palabras_por_minuto", "muletillas_cada_100", "wer_aprox_vs_ted",
              "segundos_transcripcion", "veces_tiempo_real", "palabras_quitadas_limpieza"]].copy()
pv["segmentos"] = pv.id.map(seg.groupby("video").size())
pv["vocabulario"] = pv.id.map(lambda v: len(set(re.findall(r"\w+", " ".join(seg[seg.video == v].text).lower()))))
pv["ttr"] = (pv.vocabulario / pv.palabras).round(3)
pv["tokens_aprox"] = (pv.palabras * 1.6).round()  # shortcut: ~1,6 tokens por palabra en español para Llama; medir con el tokenizer en la Etapa 3
chunks = {v: build_chunks(t["segments"], cfg["chunking"]["words_per_chunk"], cfg["chunking"]["overlap_words"]) for v, t in trans.items()}
ch = pd.DataFrame([{"video": v, "palabras": count_words(c["text"]), "dur": c["end"] - c["start"], "start": c["start"]}
                   for v, cs in chunks.items() for c in cs])
pv["chunks"] = pv.id.map(ch.groupby("video").size())
res["por_video"] = pv.to_dict("records")
res["totales_5"] = {"palabras": int(pv.palabras.sum()), "minutos": round(pv.minutos.sum(), 1),
                    "estimadas_150": int(quality.palabras_estimadas_150ppm.sum()), "chunks": int(len(ch)),
                    "vocab_global": len(set(re.findall(r"\w+", " ".join(seg.text).lower())))}
res["chunks"] = {"palabras": ch.palabras.describe().round(1).to_dict(), "dur_s": ch.dur.describe().round(1).to_dict(),
                 "duplicados": int(pd.Series([c["text"] for cs in chunks.values() for c in cs]).duplicated().sum())}

# Top palabras sin stopwords
STOP = set("""de la que el en y a los se del las un por con no una su para es al lo como más mas pero sus le ya o este sí si
porque esta entre cuando muy sin sobre también me hasta hay donde quien desde todo nos durante todos uno les ni contra otros
ese eso ante ellos e esto mí antes algunos qué unos yo otro otras otra él tanto esa estos mucho quienes nada muchos cual poco
ella estar estas algunas algo nosotros mi mis tú te ti tu tus ellas era fue ser son han ha había hace hacer puede pueden tiene
tienen va vamos así aquí ahí entonces bueno pues cada cómo lo los dos tres vez creo decir dice porque eran esos esas años
""".split())
top = {}
for v in trans:
    words = [w for w in re.findall(r"[a-záéíóúñü]+", " ".join(seg[seg.video == v].text).lower()) if w not in STOP and len(w) > 3]
    top[v] = Counter(words).most_common(8)
res["top_palabras"] = top

# Relaciones: correlaciones entre variables por video
corr_cols = ["minutos", "palabras", "palabras_por_minuto", "segmentos", "vocabulario", "ttr", "chunks"]
res["correlacion"] = pv[corr_cols].corr().round(2).to_dict()
wer = pv.dropna(subset=["wer_aprox_vs_ted"])
res["wer_vs_ppm"] = wer[["id", "wer_aprox_vs_ted", "palabras_por_minuto"]].to_dict("records")

# Similitud temática TF-IDF entre videos
docs = [" ".join(seg[seg.video == v].text) for v in trans]
X = TfidfVectorizer(stop_words=list(STOP), min_df=1).fit_transform(docs)
sim = cosine_similarity(X)
res["similitud_tfidf"] = {"videos": list(trans), "matriz": sim.round(3).tolist(),
                          "media_fuera_diagonal": round(float(sim[~np.eye(len(sim), dtype=bool)].mean()), 3)}

# ---- Variable objetivo (banco de preguntas) ----
qdf = pd.DataFrame(questions)
qdf["seg"] = qdf.minute.dropna().map(lambda m: int(m.split(":")[0]) * 60 + int(m.split(":")[1]))
qdf["pos_rel"] = qdf.apply(lambda r: r.seg / trans[r.video]["duration_seconds"] if pd.notna(r.seg) else np.nan, axis=1)
qdf["palabras_pregunta"] = qdf.question.map(count_words)
qdf["palabras_ref"] = qdf.reference.fillna("").map(count_words)
res["preguntas"] = {"total": len(qdf), "por_tipo": qdf.type.value_counts().to_dict(),
                    "por_video": qdf.video.value_counts().sort_index().to_dict(),
                    "palabras_pregunta": qdf.palabras_pregunta.describe().round(1).to_dict(),
                    "palabras_ref": qdf.loc[qdf.type == "normal", "palabras_ref"].describe().round(1).to_dict(),
                    "posicion_relativa": qdf.pos_rel.dropna().round(2).tolist(),
                    "tercios": pd.cut(qdf.pos_rel.dropna(), [0, 1 / 3, 2 / 3, 1.01], labels=["inicio", "medio", "final"],
                                      include_lowest=True).value_counts().to_dict()}

# Separación: estratificada por video y tipo, random_state=42 -> 1 normal por video a desarrollo
rng = np.random.RandomState(42)
dev_ids = []
for v, g in qdf[qdf.type == "normal"].groupby("video"):
    dev_ids.append(g.id.iloc[rng.randint(len(g))])
qdf["conjunto"] = np.where(qdf.id.isin(dev_ids), "desarrollo", "prueba")
res["split"] = {"desarrollo": dev_ids, "n_dev": len(dev_ids), "n_test": int((qdf.conjunto == "prueba").sum()),
                "test_por_tipo": qdf[qdf.conjunto == "prueba"].type.value_counts().to_dict()}
qdf[["id", "video", "type", "conjunto", "question"]].to_csv(OUT / "split_preguntas.csv", index=False, encoding="utf-8-sig")

# Ejemplo de entrada / salida esperada y fragmento recuperable
ex = qdf[qdf.id == "02-2"].iloc[0]
res["ejemplo"] = {"pregunta": ex.question, "referencia": ex.reference, "minuto": ex.minute,
                  "chunk": next(c for c in chunks["02_privacidad"] if c["start"] - 15 <= ex.seg <= c["end"] + 15)}

# WER recomputado como verificación del CSV del proyecto
res["wer_check"] = {}
for v in wer.id:
    ref = read_vtt(ROOT / f"data/referencias/{v}.es.vtt")
    hyp = " ".join(s["raw"] for s in trans[v]["segments"])
    res["wer_check"][v] = round(jiwer.wer(normalize_for_wer(ref), normalize_for_wer(hyp)), 3)

# Datos para gráficos
seg[["video", "palabras", "dur"]].to_csv(OUT / "segmentos.csv", index=False)
ch.to_csv(OUT / "chunks.csv", index=False)
(OUT / "resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print(f"Resultados en {OUT}")
