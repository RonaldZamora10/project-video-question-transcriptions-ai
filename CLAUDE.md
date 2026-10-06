# CLAUDE.md — Sistema de preguntas y respuestas sobre video (LLM + RAG)

Proyecto universitario de **Sistemas Inteligentes** (Universidad ECCI), equipo de 4 estudiantes. Este archivo le da contexto
a Claude Code. Si algo aquí contradice lo que el usuario pida en el chat, manda el chat.

## 0. Antes de escribir código: lee esto, en este orden
1. Este archivo.
2. `docs/DECISIONES.md` — decisiones vigentes y contradicciones conocidas (fuente de verdad técnica).
3. `docs/ENTREGABLE-1.md` — el Entregable 1 ya redactado (problema, justificación, objetivos, estado del arte, datos, metodología).
   **Es el contrato**: lo que se implemente debe cumplirlo, o hay que avisar para actualizar el documento.
4. `docs/REQUISITOS-ENTREGABLE-1.md` — contra qué se evalúa el trabajo.
5. `docs/DECISIONES-TECNICAS.txt` — comparación de LLM, transcripción, embeddings y vector store, con fuentes.
6. `docs/referencia/` — los archivos originales (Word y PDF).

Cuando termines de leer, **resume en pocas líneas lo que entendiste y qué dudas tienes**, antes de proponer nada.

## 1. Qué se está construyendo
Un sistema que transcribe un video en **español**, lo indexa y responde preguntas del usuario en lenguaje natural
**solo con base en lo dicho en el video**, citando el minuto. No genera preguntas automáticamente.
Todo corre **local y gratis** (sin APIs de pago) y con **bajo consumo de máquina**.

Pregunta problema: ¿es posible construir un sistema basado en LLM que, a partir de la transcripción automática de un video,
responda con precisión y fidelidad las preguntas en lenguaje natural de un usuario?

Aporte diferencial del proyecto (lo que lo hace evaluable): no solo construir el sistema, sino **medir con criterio** si las
respuestas son fieles al video y comparar **RAG vs. sin RAG**. Los pasos de evaluación pesan tanto como los de construcción.

## 2. Qué se entrega
- **Entregable 1 (ya hecho):** plan completo en `docs/ENTREGABLE-1.md`.
- **Siguientes entregables:** sistema funcionando + evaluación + informe/sustentación. **No conozco sus requisitos exactos.**
  No inventes rúbricas: pídele al usuario la guía del docente de cada entregable y guárdala en `docs/`.
- Evidencia que el informe va a necesitar y que el repo debe poder producir: tablas y gráficas de la comparación A vs. B,
  ejemplos de respuestas buenas y malas (incluidas alucinaciones), latencias, y el conteo real de palabras de las transcripciones
  (para contrastarlo con la estimación del Entregable 1).

## 3. Decisiones vigentes (resumen; el detalle está en `docs/DECISIONES.md`)
| Componente | Decisión |
|---|---|
| LLM | Llama 3.2 3B Instruct vía **Ollama**, por API HTTP (`http://localhost:11434`), no `subprocess` |
| Interfaz | **Streamlit.** Angular fue evaluado y descartado: no lo propongas de nuevo salvo que el usuario lo pida |
| Embeddings | `intfloat/multilingual-e5-base` (prefijos `query: ` y `passage: `) |
| Transcripción | **Solo Whisper** con `language="es"` (sin subtítulos de YouTube; los de TED solo como referencia para medir el error). Tamaño por decidir midiendo `small`/`medium` (faster-whisper, int8) vs `large-v3` |
| Vector store | ChromaDB o FAISS persistido en disco; por decidir con el usuario |
| Idioma / duración | Solo español, videos de hasta 25 min |

## 4. Dataset: 8 videos reales (TED en español)
| # | Tema | Video | URL |
|---|---|---|---|
| 1 | Ciencia | Las matemáticas son para siempre — E. Sáenz de Cabezón | https://www.youtube.com/watch?v=lmFUp4K8fFc |
| 2 | Tecnología | El futuro de la privacidad — S. Bortnik (TEDxSanIsidro) | https://www.youtube.com/watch?v=TjsCyfkKPk0 |
| 3 | Gastronomía | ¿Puede la cocina cambiar el mundo? — G. Acurio | https://www.ted.com/talks/gaston_acurio_can_home_cooking_change_the_world |
| 4 | Música | ¿Por qué nos emociona la música? — P. Bortolameolli | https://www.ted.com/talks/paolo_bortolameolli_por_que_nos_emociona_la_musica |
| 5 | Medioambiente | Por qué necesitamos proteger el alta mar — E. Sala | https://www.ted.com/talks/enric_sala_por_que_necesitamos_proteger_el_alta_mar |
| 6 | Desarrollo personal | El valor de nuestra diversidad interna — R. Hwang | https://www.ted.com/talks/rebeca_hwang_el_valor_de_nuestra_diversidad_interna |
| 7 | Educación | La selección latinoamericana de cerebros — J. Enriquez | https://www.ted.com/talks/juan_enriquez_la_seleccion_latinoamericana_de_cerebros |
| 8 | Emprendimiento | Una nueva manera de hablar del fracaso en los negocios — L. Gasca | https://www.ted.com/talks/leticia_gasca_una_nueva_manera_de_hablar_del_fracaso_en_los_negocios |

Guardar en `data/videos.yaml` (id, tema, título, url, duración). Verificar disponibilidad y duración ≤ 25 min antes de procesar.
Hasta ahora **nadie ha verificado** que `yt-dlp` pueda bajar los de ted.com; compruébalo en el Paso 2.

## 5. Entorno y repositorio
- Sistema del usuario: **Windows**, terminal Git Bash en VS Code. Carpeta de trabajo: `D:\proyecto universidad`.
  Usa rutas y comandos compatibles con Windows (venv: `.venv/Scripts/activate`).
- Remotos: `origin` = `https://github.com/RonaldZamora10/project-video-question-transcriptions-ai.git` (HTTPS; SSH daba error de clave);
  `upstream` = `https://github.com/vaibhav07772/multi-agent-rag-local-ai.git` (código base).
- Si `git status` o `git log` muestran que el push inicial o el merge con el historial del repo remoto aún no se hicieron, ayuda al
  usuario a resolverlo **antes** del Paso 1, sin `--force`.
- Hardware: 16 GB RAM, Intel i5-1135G7, **sin GPU dedicada** (todo corre en CPU). Elegir modelos y `num_ctx` con eso en mente.
- Requiere instalados: Python 3.11, ffmpeg, Ollama (con `ollama pull llama3.2:3b`).

## 6. Código base y licencia
Partimos de `vaibhav07772/multi-agent-rag-local-ai` (**MIT**, ~160 líneas: Streamlit + Whisper + FAISS + Ollama).
- Conservar `LICENSE` original y el copyright del autor. README con sección "Créditos": de dónde parte y qué se cambió.
- No copiar código de repos sin licencia declarada (p. ej. AskTube).
- Problemas ya identificados en el base: prompt y embeddings en inglés, Whisper sin idioma fijo, sin tiempos ni citas, índice
  reconstruido en cada pregunta, modelo fijo `llama3` por `subprocess`, `audio.*` en el directorio actual, sin caché, sin pruebas,
  `audio.webm` de ~15 MB versionado en el repo (quitarlo). El "multi-agent" son dos funciones: no presentarlo como tal en el informe.
- Prueba manual del código base antes de tocarlo: `streamlit run app.py` con el video `lmFUp4K8fFc`, preguntando algo del video y
  luego "¿Cuál es la capital de Francia?". Si responde "París", el sistema contesta con conocimiento propio y no con el video:
  guarda ese resultado como evidencia del "antes".

## 7. Hoja de ruta (un paso = una rama = un PR)
1. **Base y configuración** (`feat/01-base`): paquete `src/videoqa/`, `config.yaml`, UI Streamlit en español, `.gitignore`, README con créditos, `requirements.txt` fijado, quitar `audio.webm`.
2. **Transcripción en español** (`feat/02-transcripcion`): Whisper `es` con tiempos; `.txt` + `.json` por video en `data/transcripts/`; caché; `python -m videoqa.transcribe --all`; medir tamaños de Whisper. Además (objetivo específico 1 + Etapa 4): módulo de limpieza del texto y análisis de calidad de las transcripciones (error WER vs. subtítulos humanos de TED cuando existan, declarado aproximado; muletillas; conteo real de palabras vs. ~15.500 estimadas).
3. **Indexación** (`feat/03-indexacion`): chunks con `start`/`end`, embeddings e5, índice persistente por video; reiniciar no reconstruye.
4. **Generación con citas** (`feat/04-generacion`): cliente HTTP de Ollama, prompt en español "solo con el contexto; si no está, 'No encuentro esto en el video'", citas `mm:ss`.
5. **Config B sin RAG** (`feat/05-sin-rag`): transcripción completa como contexto; cuidar `num_ctx`; medir latencia.
6. **Evaluación** (`feat/06-evaluacion`): `data/eval/preguntas.yaml` (~5 por video, ≈40, con respuesta de referencia escrita por el equipo; incluir preguntas trampa cuya respuesta NO está en el video); métricas de `docs/DECISIONES.md`; juez LLM local y/o tipo RAGAS; CSV + gráficas; comparar A vs. B y reportar también los fallos.
7. **Calidad y cierre** (`feat/07-calidad`): pruebas, GitHub Actions (lint + pruebas con mocks), README final con resultados y limitaciones.

## 8. Reglas de trabajo
- Nunca trabajar directo en `main`. Commits pequeños en español, estilo `tipo: mensaje` (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
- **No hacer `git push` ni abrir PR sin confirmación del usuario.** No usar `--force`.
- Antes de cada PR: correr pruebas y explicar qué cambió y cómo probarlo, **en lenguaje simple**: el usuario es estudiante y no
  domina estos temas; explica el "por qué" de cada decisión, porque tendrá que sustentarla.
- Pruebas sin red ni modelos pesados (mocks); las de integración, marcadas aparte.
- No subir: audios, modelos, `.env`, índices vectoriales. Los transcritos `.txt`/`.json` sí (son el dataset).
- Python 3.11, dependencias fijadas, configuración en `config.yaml` (sin valores mágicos en el código).
- **Honestidad con los resultados:** si el sistema falla o la mejora es pequeña, se reporta tal cual. No ajustes preguntas o métricas
  para que los números salgan bonitos.
- Si un cambio contradice `docs/ENTREGABLE-1.md` o `docs/DECISIONES.md`, dilo explícitamente para que se actualicen los documentos.

## 9. Decisiones abiertas (pregúntale al usuario cuando toque)
1. Tamaño de Whisper (medir `small`/`medium` vs `large-v3` en los 8 videos).
2. ChromaDB vs FAISS persistido (si cambia respecto al Word, avisar).
3. Requisitos de los siguientes entregables (pedir la guía del docente).
4. Nombres del equipo para el README (no incluir códigos estudiantiles en un repo que pueda ser público).
