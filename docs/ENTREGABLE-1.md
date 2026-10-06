**ENTREGABLE 1 – PROYECTO DE SISTEMAS INTELIGENTES**

*Sistema de preguntas y respuestas sobre el contenido de un video mediante modelos de lenguaje (LLM)*

1\. Definición del problema

1.1 Contexto del problema

El video se ha consolidado como uno de los formatos de comunicación de conocimiento más utilizados en la actualidad, tanto en contextos educativos como corporativos y de divulgación general. Clases grabadas, conferencias, tutoriales técnicos y capacitaciones internas de las organizaciones se producen y almacenan en grandes volúmenes, con duraciones que frecuentemente superan la hora de contenido.

A diferencia de un documento de texto, el contenido de un video no es directamente consultable: para ubicar un dato puntual dentro de una grabación, la persona debe reproducir el video completo o desplazarse manualmente por la línea de tiempo, sin ninguna garantía de encontrar rápidamente la información que necesita.

1.2 Población, organización o sector afectado

El problema afecta principalmente a estudiantes y autodidactas que consultan clases grabadas o video-tutoriales, así como a colaboradores de organizaciones que reciben capacitaciones o participan en reuniones grabadas y necesitan retomar puntos específicos discutidos sin volver a ver la grabación completa.

1.3 Situación actual

Actualmente, la forma más común de resolver una duda sobre el contenido de un video es reproducirlo de nuevo, apoyarse en la barra de progreso para adivinar en qué minuto se trató un tema, o —cuando existen— revisar subtítulos generados automáticamente, los cuales no están organizados de forma consultable y no permiten hacer preguntas directas sobre el contenido.

1.4 Necesidad identificada

Existe la necesidad de una herramienta que permita a un usuario formular preguntas en lenguaje natural sobre el contenido de un video y recibir una respuesta concreta, fundamentada en lo que efectivamente se dijo en la grabación, sin tener que revisarla manualmente.

1.5 Consecuencias del problema

- Pérdida de tiempo al tener que revisar minuto a minuto un video para ubicar información puntual.

- Abandono de la consulta cuando el video es muy extenso, lo que puede llevar a decisiones o respuestas incompletas.

- Subutilización del contenido audiovisual generado por instituciones educativas y organizaciones, que queda almacenado pero poco explotado.

1.6 Posible aporte de un sistema inteligente

Un sistema basado en modelos de lenguaje (LLM), combinado con transcripción automática y recuperación de información, podría convertir el contenido hablado de un video en una fuente consultable mediante lenguaje natural, entregando respuestas concretas y trazables al fragmento del video donde se originan.

1.7 Pregunta problema

**Pregunta problema:** ¿Es posible construir un sistema basado en modelos de lenguaje (LLM) que, a partir de la transcripción automática de un video, responda con precisión y fidelidad al contenido las preguntas en lenguaje natural formuladas por un usuario?

2\. Justificación

Resolver este problema es importante porque el tiempo que una persona invierte en encontrar información dentro de un video suele ser mucho mayor que el tiempo que tomaría leer la respuesta a una pregunta puntual. Esta ineficiencia se agrava en videos largos (clases, conferencias, capacitaciones), donde la información relevante puede estar concentrada en unos pocos minutos dentro de una grabación de una o varias horas.

Se beneficiarían directamente estudiantes que repasan contenido de clases grabadas, profesionales que consultan capacitaciones o reuniones grabadas, y, en general, cualquier persona que use el video como fuente de aprendizaje o consulta.

Los procesos actuales presentan limitaciones claras: los buscadores de video solo indexan metadatos (título, descripción, etiquetas) y no el contenido hablado; los subtítulos automáticos, cuando existen, no son consultables mediante preguntas; y revisar manualmente un video es lento y poco escalable cuando se maneja un volumen alto de contenido.

El uso de Machine Learning y modelos de lenguaje resulta pertinente porque estas técnicas permiten dos cosas que los métodos tradicionales de búsqueda por palabra clave no logran: comprender el significado de una pregunta más allá de las palabras exactas que la componen, y generar una respuesta redactada en lenguaje natural en lugar de simplemente devolver fragmentos de texto sin procesar. La automatización simple de una tarea de búsqueda no sería suficiente por sí sola; lo que aporta valor real es la capacidad del LLM de interpretar la intención de la pregunta y sintetizar una respuesta coherente a partir del contenido recuperado.

Entre las ventajas de la solución propuesta se encuentran: no depender de subtítulos preexistentes (se puede generar la transcripción de cualquier video), permitir preguntas formuladas de forma libre por el usuario, y ofrecer una respuesta fundamentada en el contenido real de la fuente en lugar de una respuesta genérica. Una implementación exitosa permitiría transformar cualquier repositorio de video en una base de conocimiento consultable, reduciendo el tiempo de búsqueda de información y aumentando el aprovechamiento del contenido ya existente.

3\. Objetivos

3.1 Objetivo general

Desarrollar un sistema basado en modelos de lenguaje (LLM) que, a partir de la transcripción automática de un video, permita a un usuario formular preguntas en lenguaje natural y obtener respuestas fundamentadas en el contenido de dicho video.

3.2 Objetivos específicos

- Analizar las características del audio y de las transcripciones obtenidas de los videos de prueba, identificando su calidad, ruido y necesidades de limpieza.

- Diseñar la estrategia de fragmentación (chunking) y de recuperación de información que permita ubicar los pasajes más relevantes de la transcripción frente a una pregunta dada.

- Implementar el flujo completo del sistema: transcripción del video, indexación vectorial del contenido y generación de respuestas mediante recuperación aumentada (RAG).

- Evaluar la fidelidad, relevancia y presencia de alucinaciones en las respuestas generadas, contrastándolas con el contenido real de la transcripción.

- Comparar el desempeño del sistema con recuperación (RAG) frente a una configuración sin recuperación (transcripción completa como contexto), utilizando las métricas definidas.

4\. Antecedentes y estado del arte

A continuación se presentan cinco trabajos académicos recientes relacionados con la generación de respuestas sobre contenido de video y transcripciones mediante modelos de lenguaje y recuperación aumentada (RAG), consultados en bases académicas como arXiv, Springer y ACL Anthology.

| **Referencia**                                                                                                 | **Problema**                                                                                             | **Datos**                                                                                                      | **Técnica**                                                                                                                      | **Evaluación**                                                                               | **Resultado / Limitación**                                                                                                                                                |
|----------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Tanner, Marfurt & Oğul (2024) — Enhancing Question Answering in Lecture Videos with a Multimodal RAG Framework | Dificultad para buscar y localizar información puntual dentro de videos de clase extensos.               | Videos de conferencias universitarias: audio narrado y texto extraído de diapositivas.                         | Framework de recuperación aumentada (RAG) multimodal, con base vectorial para indexar el contenido.                              | Métricas automáticas de evaluación de sistemas RAG (fidelidad y relevancia de la respuesta). | Resultado: combinar audio y diapositivas mejora la localización de segmentos relevantes. Limitación: depende de la calidad de la extracción de texto de las diapositivas. |
| Kang et al. (2025) — Leveraging RAG to Answer Questions based on Meeting Transcripts                           | Responder preguntas específicas a partir de transcripciones extensas de reuniones.                       | Transcripciones completas de reuniones de trabajo.                                                             | RAG combinado con representaciones semánticas adicionales del texto para mejorar la recuperación.                                | Comparación de la calidad de respuesta según el tipo de pregunta formulada.                  | Resultado: mejoras notables en preguntas sobre participantes y roles. Limitación: la mejora no es uniforme para todos los tipos de pregunta.                              |
| Gia et al. (2025) — VRAG: Retrieval-Augmented Video Question Answering for Long-Form Videos                    | Responder preguntas sobre videos largos sin necesidad de procesar todo el contenido a la vez.            | Videos de larga duración (benchmarks de comprensión de video).                                                 | Recuperación de los segmentos más relevantes del video antes de generar la respuesta.                                            | Comparación frente a modelos que procesan el video completo sin recuperación previa.         | Resultado: mayor precisión en videos largos. Limitación: puede perder continuidad temporal fina entre segmentos recuperados.                                              |
| VideoRAG (2025) — Retrieval-Augmented Generation over Video Corpus                                             | Generar respuestas fundamentadas cuando la información relevante está distribuida en varios videos.      | Colecciones o corpus de múltiples videos.                                                                      | Recuperación aumentada aplicada a colecciones de video, no solo a un único documento.                                            | Comparación frente a otros métodos de comprensión de video de larga duración.                | Resultado: mejora la comprensión al indexar corpus completos. Limitación: alto costo computacional al escalar a corpus grandes.                                           |
| Es et al. (2023) — RAGAS: Automated Evaluation of Retrieval Augmented Generation                               | Falta de métricas automáticas confiables para evaluar sistemas de generación aumentada por recuperación. | Aplicable a cualquier conjunto de preguntas y respuestas con contexto recuperado (no requiere dataset propio). | Métricas automáticas basadas en modelos de lenguaje: fidelidad, relevancia de la respuesta y relevancia del contexto recuperado. | Correlación de las métricas propuestas con el juicio humano.                                 | Resultado: permite evaluar sistemas RAG sin depender de respuestas de referencia escritas a mano. Limitación: las métricas heredan los sesgos del modelo evaluador.       |

4.1 Análisis comparativo

Los trabajos revisados coinciden en un mismo patrón: para responder preguntas sobre contenido extenso (videos, transcripciones de reuniones, corpus documentales), no es eficiente ni preciso enviar todo el contenido al modelo de lenguaje de una sola vez; en su lugar, recuperar primero los fragmentos más relevantes mejora tanto la precisión como la escalabilidad del sistema. Al mismo tiempo, varios de estos trabajos señalan una limitación compartida: las métricas automáticas tradicionales (basadas en solapamiento de palabras) no logran capturar adecuadamente si una respuesta es fiel al contenido fuente o si el modelo está generando información no sustentada (alucinaciones), lo que ha impulsado el uso de métricas específicas para sistemas RAG.

El proyecto propuesto se relaciona con estos antecedentes al adoptar la misma arquitectura general de recuperación aumentada aplicada a contenido transcrito, pero se diferencia en que su evaluación no se limita a medir si el sistema responde, sino que compara explícitamente dos configuraciones (con y sin recuperación) para determinar en qué escenarios la recuperación aporta una mejora real en fidelidad y relevancia, en lugar de asumirla de antemano.

5\. Datos

Este es un proyecto basado en LLM, por lo que la información de entrada corresponde a documentos de texto derivados de video, y no a un dataset tabular tradicional.

- Fuente de los documentos: 8 videos reales, disponibles públicamente, de temáticas distintas entre sí, a partir de los cuales se genera la transcripción. El detalle de cada uno se presenta en la tabla siguiente.

- Número de documentos: 8 videos, todos de hasta 25 minutos de duración, seleccionados deliberadamente de temas variados para evaluar el sistema en dominios distintos y no solo en un tipo de contenido.

- Tipos de documentos: transcripciones generadas automáticamente a partir del audio; en los casos donde el video ya cuenta con subtítulos, se aprovechan directamente.

- Idioma: español.

- Tamaño aproximado del corpus: se estima un total de varios miles de palabras transcritas, considerando el conjunto completo de los 8 videos.

- Características de la información: texto hablado, con posibles muletillas, repeticiones y errores propios de la transcripción automática, lo que exige una etapa de limpieza previa.

- Formato de almacenamiento: archivos de texto plano (.txt) por video para las transcripciones, y una base de datos vectorial local para los fragmentos indexados.

- Modelo LLM que se planea utilizar: un modelo de lenguaje de uso abierto y ejecutable localmente, para no depender de servicios de pago y mantener el sistema replicable.

5.1 Videos que conforman el dataset

A continuación se listan los 8 videos reales, en español, que conforman el conjunto de prueba del proyecto. Se seleccionaron de temáticas distintas (ciencia, tecnología, gastronomía, música, medioambiente, desarrollo personal, educación y emprendimiento) para evaluar el sistema en dominios variados y no solo en un tipo de contenido.

| **\#** | **Título del video**                                                         | **Tema**                | **Duración** | **Fuente**                                                                         |
|--------|------------------------------------------------------------------------------|-------------------------|--------------|------------------------------------------------------------------------------------|
| 1      | Las matemáticas son para siempre — Eduardo Sáenz de Cabezón (TED)            | Ciencia / matemáticas   | ≈ 9 min      | youtube.com/watch?v=lmFUp4K8fFc                                                    |
| 2      | El futuro de la privacidad — Sebastián Bortnik (TEDxSanIsidro)               | Tecnología / privacidad | ≈ 13 min     | youtube.com/watch?v=TjsCyfkKPk0                                                    |
| 3      | ¿Puede la cocina cambiar el mundo? — Gastón Acurio (TED)                     | Gastronomía             | 13:15        | ted.com/talks/gaston_acurio_can_home_cooking_change_the_world                      |
| 4      | ¿Por qué nos emociona la música? — Paolo Bortolameolli (TED)                 | Música                  | 15:48        | ted.com/talks/paolo_bortolameolli_por_que_nos_emociona_la_musica                   |
| 5      | Por qué necesitamos proteger el alta mar — Enric Sala (TED)                  | Medioambiente           | 12:42        | ted.com/talks/enric_sala_por_que_necesitamos_proteger_el_alta_mar                  |
| 6      | El valor de nuestra diversidad interna — Rebeca Hwang (TED)                  | Desarrollo personal     | 12:05        | ted.com/talks/rebeca_hwang_el_valor_de_nuestra_diversidad_interna                  |
| 7      | La selección latinoamericana de cerebros — Juan Enriquez (TED)               | Educación / tecnología  | 12:38        | ted.com/talks/juan_enriquez_la_seleccion_latinoamericana_de_cerebros               |
| 8      | Una nueva manera de hablar del fracaso en los negocios — Leticia Gasca (TED) | Emprendimiento          | ≈ 15 min     | ted.com/talks/leticia_gasca_una_nueva_manera_de_hablar_del_fracaso_en_los_negocios |

5.2 Estrategia de recuperación (RAG)

- Estrategia de fragmentación: división del texto en fragmentos de tamaño moderado, con solapamiento entre fragmentos consecutivos para no perder contexto en los límites de cada corte.

- Embeddings: modelo de representación semántica liviano, capaz de ejecutarse sin necesidad de hardware especializado.

- Base de datos vectorial: motor de almacenamiento vectorial local, sin dependencia de servicios en la nube de pago.

- Estrategia de recuperación: búsqueda por similitud semántica, seleccionando los fragmentos más cercanos a la pregunta del usuario antes de generar la respuesta.

6\. Metodología

El desarrollo del proyecto seguirá el flujo que se presenta en el siguiente diagrama, correspondiente a un sistema LLM con recuperación aumentada (RAG) aplicado a contenido de video.

<img src="media/65f7ecb22b73492e61c5ea362e9360b1d51ad043.png" style="width:3.95833in;height:5.83333in" />

6.1 Descripción de las etapas

**Etapa 1. Video de entrada.** Se recibe el archivo de video o el enlace correspondiente, que constituye la fuente original de información.

**Etapa 2. Extracción de audio.** Se separa la pista de audio del video para poder procesarla de forma independiente.

**Etapa 3. Transcripción automática.** El audio se convierte en texto mediante un modelo de reconocimiento de voz, obteniendo la transcripción completa del video.

**Etapa 4. Preprocesamiento del texto.** Se limpia el texto transcrito: eliminación de ruido propio de la transcripción, normalización y, cuando aplica, segmentación por oraciones o por marcas de tiempo.

**Etapa 5. Fragmentación del texto (chunking).** El texto se divide en fragmentos de tamaño manejable, con solapamiento, de forma que cada fragmento conserve suficiente contexto por sí mismo.

**Etapa 6. Generación de embeddings.** Cada fragmento se convierte en una representación vectorial que captura su significado semántico.

**Etapa 7. Almacenamiento vectorial.** Los fragmentos y sus representaciones vectoriales se almacenan en una base de datos vectorial para su posterior consulta.

**Etapa 8. Pregunta del usuario.** El usuario formula una pregunta en lenguaje natural sobre el contenido del video.

**Etapa 9. Recuperación de fragmentos relevantes.** Se calcula la similitud semántica entre la pregunta y los fragmentos almacenados, seleccionando los más relevantes.

**Etapa 10. Generación de la respuesta.** El modelo de lenguaje recibe la pregunta junto con los fragmentos recuperados como contexto, y genera una respuesta fundamentada en dicho contexto.

**Etapa 11. Evaluación de la respuesta.** Se evalúa la respuesta generada frente al contenido real de la transcripción, verificando su fidelidad, relevancia y la eventual presencia de alucinaciones.

6.2 Configuraciones a comparar

De acuerdo con lo exigido para proyectos basados en LLM, se compararán como mínimo dos configuraciones del sistema, con el fin de determinar el aporte real de la recuperación de información frente a una alternativa más simple:

| **Aspecto**            | **Configuración A — Con recuperación (RAG)**                          | **Configuración B — Sin recuperación (transcripción completa)**                                         |
|------------------------|-----------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| Entrada al LLM         | Solo los fragmentos recuperados como más relevantes para la pregunta. | La transcripción completa del video como contexto.                                                      |
| Ventaja esperada       | Menor cantidad de texto irrelevante; escalable a videos largos.       | Simplicidad; evita errores de recuperación en videos cortos.                                            |
| Riesgo esperado        | Puede omitir información relevante si la recuperación falla.          | Puede exceder el límite de contexto del modelo en videos largos; mayor riesgo de respuestas imprecisas. |
| Métrica de comparación | Fidelidad, relevancia y tiempo de respuesta (latencia).               | Fidelidad, relevancia y tiempo de respuesta (latencia).                                                 |

6.3 Aspectos de evaluación

La evaluación del sistema considerará los siguientes aspectos, en línea con lo identificado en el estado del arte:

- Correctitud: si la respuesta generada es correcta frente al contenido del video.

- Relevancia: si la respuesta se ajusta realmente a lo que el usuario preguntó.

- Fidelidad a las fuentes: si la respuesta se sustenta únicamente en lo dicho en el video, sin agregar información externa.

- Alucinaciones: identificación de afirmaciones generadas por el modelo que no tienen respaldo en la transcripción.

- Latencia: tiempo que toma el sistema en generar una respuesta, comparando ambas configuraciones.

Resultado esperado

Al finalizar este primer entregable, el proyecto cuenta con el problema, la justificación, los objetivos, el estado del arte, la descripción de los datos y la metodología claramente definidos. Aunque en esta etapa no se exige tener el sistema final implementado, se ha establecido una metodología clara y viable —basada en herramientas de transcripción automática, recuperación de información y modelos de lenguaje de uso abierto— para su posterior desarrollo.
