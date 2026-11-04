import json

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")
from pathlib import Path
OUT = str(Path(__file__).resolve().parent / "out")
r = json.load(open(f"{OUT}/resultados.json", encoding="utf-8"))
seg = pd.read_csv(f"{OUT}/segmentos.csv")
ch = pd.read_csv(f"{OUT}/chunks.csv")

BG, INK, SOFT, GRID = "#F6F4EE", "#14213D", "#4A5568", "#DDD8CC"
ORANGE, BLUE = "#D9682B", "#3A6EA5"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 20, "axes.facecolor": BG, "figure.facecolor": BG,
                     "axes.edgecolor": GRID, "axes.labelcolor": SOFT, "xtick.color": SOFT, "ytick.color": SOFT,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 22,
                     "axes.titlecolor": INK, "axes.titleweight": "bold", "axes.titlelocation": "left"})
SHORT = {"01_matematicas": "01 Matemáticas", "02_privacidad": "02 Privacidad", "03_cocina": "03 Cocina",
         "04_musica": "04 Música", "05_alta_mar": "05 Alta mar"}


def save(fig, name):
    fig.savefig(f"{OUT}/{name}.png", dpi=100, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)


# 1. Palabras reales vs estimadas por video
pv = pd.DataFrame(r["por_video"])
est = dict(zip(pv.id, (pv.minutos * 150).round()))
fig, ax = plt.subplots(figsize=(13, 7))
x = np.arange(len(pv))
ax.bar(x - 0.2, pv.palabras, 0.4, color=INK, label="Palabras reales (Whisper)")
ax.bar(x + 0.2, [est[i] for i in pv.id], 0.4, color=GRID, label="Estimadas a 150 ppm (Entregable 1)")
for xi, (w, ppm) in enumerate(zip(pv.palabras, pv.palabras_por_minuto)):
    ax.text(xi - 0.2, w + 40, f"{w:,}".replace(",", "."), ha="center", color=INK, fontsize=17, fontweight="bold")
    ax.text(xi - 0.2, 90, f"{ppm}\nppm", ha="center", color="#F6C9A8" if ppm < 120 else "#E9E4D8", fontsize=15, fontweight="bold")
ax.set_xticks(x, [SHORT[i].replace(" ", "\n", 1) for i in pv.id])
ax.set_ylim(0, 3250)
ax.yaxis.grid(True, color=GRID)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper right", fontsize=17)
ax.set_ylabel("Palabras")
save(fig, "g1_palabras")

# 2. Distribución de palabras por segmento y por fragmento
fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 6.5))
a1.hist(seg.palabras, bins=range(0, 27), color=INK, edgecolor=BG)
a1.axvline(seg.palabras.median(), color=ORANGE, lw=3)
a1.text(seg.palabras.median() + 2.6, a1.get_ylim()[1] * 0.92, f"mediana {seg.palabras.median():.0f}", color=ORANGE, fontsize=17)
a1.set_title("Segmentos de Whisper (n = 938)")
a1.set_xlabel("Palabras por segmento")
a1.set_ylabel("Frecuencia")
a2.hist(ch.palabras, bins=range(40, 141, 5), color=BLUE, edgecolor=BG)
a2.axvline(120, color=ORANGE, lw=3, ls="--")
a2.text(72, a2.get_ylim()[1] * 0.92, "objetivo 120", color=ORANGE, fontsize=17)
a2.set_title("Fragmentos para el RAG (n = 104)")
a2.set_xlabel("Palabras por fragmento")
for a in (a1, a2):
    a.yaxis.grid(True, color=GRID)
    a.set_axisbelow(True)
save(fig, "g2_longitudes")

# 3. Boxplot duración de segmentos por video (atípicos)
fig, ax = plt.subplots(figsize=(13, 7))
order = list(SHORT)
data = [seg[seg.video == v].dur for v in order]
bp = ax.boxplot(data, orientation="horizontal", patch_artist=True, widths=0.55,
                medianprops={"color": ORANGE, "lw": 3}, flierprops={"marker": "o", "markerfacecolor": ORANGE,
                                                                    "markeredgecolor": ORANGE, "markersize": 7, "alpha": .7})
for b in bp["boxes"]:
    b.set(facecolor="#E9E4D8", edgecolor=INK, lw=1.5)
for k in ("whiskers", "caps"):
    for line in bp[k]:
        line.set(color=INK, lw=1.5)
lim = r["atipicos"]["duracion_seg"]["lim"][1]
ax.axvline(lim, color=BLUE, ls="--", lw=2)
ax.text(lim + 0.3, 5.45, f"límite IQR global {lim:.1f} s", color=BLUE, fontsize=17)
ax.set_yticks(range(1, 6), [SHORT[v] for v in order])
ax.invert_yaxis()
ax.set_xlabel("Duración del segmento (s)")
ax.xaxis.grid(True, color=GRID)
ax.set_axisbelow(True)
save(fig, "g3_atipicos")

# 4. Matriz de correlación
labels = {"minutos": "Minutos", "palabras": "Palabras", "palabras_por_minuto": "Palabras/min", "segmentos": "Segmentos",
          "vocabulario": "Vocabulario", "ttr": "Riqueza léxica", "chunks": "Fragmentos"}
c = pd.DataFrame(r["correlacion"]).loc[list(labels), list(labels)]
fig, ax = plt.subplots(figsize=(11, 9))
im = ax.imshow(c.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(7), labels.values(), rotation=40, ha="right")
ax.set_yticks(range(7), labels.values())
for i in range(7):
    for j in range(7):
        v = c.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=16, color="white" if abs(v) > .6 else INK)
ax.spines[:].set_visible(False)
cb = fig.colorbar(im, fraction=0.04)
cb.outline.set_visible(False)
save(fig, "g4_correlacion")

# 5. Similitud TF-IDF entre videos
s = np.array(r["similitud_tfidf"]["matriz"])
fig, ax = plt.subplots(figsize=(10, 8.5))
mask = s.copy()
np.fill_diagonal(mask, np.nan)
im = ax.imshow(mask, cmap="Oranges", vmin=0, vmax=0.15)
names = [SHORT[v] for v in r["similitud_tfidf"]["videos"]]
ax.set_xticks(range(5), names, rotation=35, ha="right")
ax.set_yticks(range(5), names)
for i in range(5):
    for j in range(5):
        ax.text(j, i, "—" if i == j else f"{s[i, j]:.2f}", ha="center", va="center", fontsize=18, color=INK)
ax.spines[:].set_visible(False)
cb = fig.colorbar(im, fraction=0.045)
cb.outline.set_visible(False)
save(fig, "g5_similitud")

# 6. Posición de las respuestas dentro del video
qpos = r["preguntas"]["posicion_relativa"]
fig, ax = plt.subplots(figsize=(14, 3.6))
ax.axvspan(0, 1 / 3, color="#ECE7DC")
ax.axvspan(2 / 3, 1, color="#ECE7DC")
ax.scatter(qpos, np.random.RandomState(1).uniform(-.3, .3, len(qpos)), s=220, color=INK, zorder=3)
for x0, t in [(1 / 6, "Inicio: 7"), (.5, "Medio: 7"), (5 / 6, "Final: 6")]:
    ax.text(x0, .55, t, ha="center", fontsize=19, color=INK, fontweight="bold")
ax.set_xlim(-.02, 1.02)
ax.set_ylim(-.6, .8)
ax.set_yticks([])
ax.set_xticks([0, .25, .5, .75, 1], ["0 %", "25 %", "50 %", "75 %", "100 %"])
ax.set_xlabel("Posición de la respuesta dentro del video")
ax.spines["left"].set_visible(False)
save(fig, "g6_posiciones")
print("ok")
