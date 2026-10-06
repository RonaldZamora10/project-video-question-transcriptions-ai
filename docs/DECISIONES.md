# Decisiones técnicas vigentes (fuente de verdad)

Última actualización de este archivo: al armar el paquete de contexto. Si cambias algo, actualiza este archivo y avisa al usuario
para ajustar el Word/PDF/presentación correspondientes.

| Tema | Decisión vigente | Origen / nota |
|---|---|---|
| Alcance | Q&A sobre el contenido de un video (el usuario pregunta; NO se generan preguntas automáticamente) | Cambio de enfoque acordado al inicio |
| Idioma | Solo español | |
| Dataset | 8 videos reales, ≤ 25 min, temas distintos (lista en `CLAUDE.md`) | `docs/ENTREGABLE-1.md` §5 |
| LLM | Llama 3.2 3B Instruct vía Ollama (prioridad: bajo consumo de máquina) | `docs/DECISIONES-TECNICAS.txt` §5.1.1. Alternativa: Qwen2.5 3B Instruct |
| Interfaz | **Streamlit.** Angular descartado (suma trabajo sin mejorar lo evaluable) | Decisión del usuario |
| Backend | Python. Si conviene, exponer el pipeline como funciones limpias para poder envolverlo en una API más adelante, sin construir la API ahora | |
| Embeddings | `intfloat/multilingual-e5-base` (prefijos `query:` / `passage:`) | PDF §5.3 |
| Transcripción | **Solo Whisper** con `language="es"` (no se usan subtítulos de YouTube como fuente); tamaño por decidir con medición | PDF dice large-v3; objetivo de bajo consumo sugiere small/medium. Decisión del usuario: todos los videos pasan por el mismo proceso |
| Referencia de calidad ASR | Subtítulos humanos de TED, cuando existan, **solo** para calcular el error (WER) de Whisper por video; se declara aproximado (los subtítulos editados no son transcripción literal) | Decisión del usuario |
| Limpieza y calidad (Paso 2) | Módulo de limpieza del texto + análisis de calidad: WER vs. referencia, muletillas, conteo real de palabras vs. ~15.500 estimadas | Cubre objetivo específico 1 y Etapa 4 del Entregable 1 |
| Hardware de desarrollo | 16 GB RAM, Intel Core i5-1135G7 (4 núcleos / 8 hilos), **sin GPU dedicada** (Iris Xe). Todo corre en CPU | Detectado en el equipo; confirmar que es donde se ejecuta el proyecto |
| Vector store | ChromaDB o FAISS persistido; por decidir | Word dice ChromaDB, repo base usa FAISS |
| Comparación obligatoria | Config A: RAG · Config B: transcripción completa sin recuperación | Entregable 1 §6.2 |
| Métricas | correctitud, relevancia, fidelidad, alucinaciones, latencia | Entregable 1 §6.3 |

## Inconsistencias conocidas entre documentos y plan (resolver con el usuario, no en silencio)
1. Whisper: PDF = large-v3 vs objetivo de bajo consumo.
2. Vector store: Word = ChromaDB vs repo base = FAISS.
3. Word (Entregable 1) dice "modelo de lenguaje de uso abierto" sin nombrarlo; el PDF de decisiones ya nombra Llama 3.2 3B. Pendiente alinear el Word y la presentación.
4. Las cifras de tamaño de corpus (~15.500 palabras) son una estimación a 150 palabras/min; reemplazar por el conteo real cuando existan las transcripciones.
5. Entregable 1 §5 dice que si el video ya tiene subtítulos "se aprovechan directamente"; la decisión vigente es usar solo Whisper (los subtítulos solo sirven de referencia para medir el error). Ajustar esa frase en el Word.
