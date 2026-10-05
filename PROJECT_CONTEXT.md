# Contexto del proyecto RAG

Para detalles de implementación, comandos, contratos de datos y estado técnico,
consultar [`DEVELOPMENT.md`](DEVELOPMENT.md).

## Objetivo

Construir un sistema de preguntas y respuestas sobre ponencias. El retriever
recuperará evidencia desde una base vectorial y el LLM redactará la respuesta
usando esa evidencia.

La unidad documental es la **ponencia**, no el archivo de transcripción completo.

```text
Evento
└── Ponencia                         ← unidad documental
    ├── Parent                       ← unidad de contexto (futuro)
    │   ├── Child                    ← unidad de retrieval (V1 implementado)
    │   └── Child
    └── Parent
```

## Alcance implementado

Esta primera etapa implementa solamente:

```text
RAW inmutable
    → parseo
    → limpieza conservadora
    → separación por ponencias
    → validación
    → talks.jsonl + talks/*.txt
```

Child V1 está congelado como unidad de retrieval. Ya existe un baseline local
de embeddings densos GTE y cosine similarity para inspección; todavía no se
implementan Parents, Qdrant, LLM ni thresholds de retrieval.

Como paso exploratorio previo al chunking, se analizó la longitud real de las
utterances con un tokenizer explícito. Ese análisis no creó chunks ni decidió
automáticamente tamaños u overlap; informó la decisión manual de Child V1. Sus resultados están en
`data/analysis/utterance_length_analysis.{json,md}`.

## Child V1

Child V1 usa utterances completas y consecutivas, nunca cruza ponencias y mide
el payload real serializado con `tiktoken==0.14.0` / `cl100k_base`. Su
configuración inicial es target aproximado de 500 tokens y overlap aproximado de
100 tokens. Cuando la siguiente utterance cruza el target se elige la opción más
cercana; el empate incluye la utterance. Cada Child contiene al menos una
utterance nueva y el último se emite sin fusionarlo.

Los Children están en `data/processed/chunks.jsonl`. Las validaciones y
estadísticas están separadas para poder revisar los resultados antes de diseñar
Parents o conectarlos a infraestructura de retrieval.

El baseline de embeddings usa `Alibaba-NLP/gte-multilingual-base` fijado en la
revisión `9bbca17d9273fd0d03d5725c7a4b0f6b45142062`. Genera un vector denso
normalizado de 768 dimensiones por `Child.text` y lo guarda como artefacto
derivado regenerable. La búsqueda local calcula cosine similarity directamente;
los scores no se interpretan como probabilidades y aún no hay thresholds.

## Fuente canónica

La fuente es:

`data/Transcripts_PlainText/Transcripts_Text/transcripts/Text_Transcript_original_AOKA-8157.txt`

El archivo original no se modifica. `Transcripts_Text` se eligió sobre
`Transcripts_PlainText` porque ambos contienen las mismas intervenciones, pero
el primero conserva timestamps.

## Salidas

- `data/processed/talks.jsonl`: una ponencia estructurada por línea.
- `data/processed/talks/*.txt`: versiones legibles, con timestamps.
- `data/processed/manifest.json`: procedencia, hashes y estadísticas.
- `data/processed/validation_report.json`: controles y advertencias de calidad.

`talks.jsonl` es la fuente canónica procesada. Cada registro incluye el texto
completo y `utterances`. `source_line` define el orden canónico del discurso y
`sequence_index` lo representa de forma consecutiva dentro de cada ponencia.
Los campos `start_time` y `start_seconds` se conservan exclusivamente como
metadata temporal. Esto permitirá generar chunks con rangos temporales sin
volver a interpretar el RAW.

## Decisiones de limpieza

- Normalizar texto a Unicode NFC.
- Retirar BOM y caracteres `FEFF` incrustados.
- Colapsar espacios dentro de cada intervención.
- Retirar las etiquetas técnicas del exportador.
- Preservar el orden del RAW mediante `source_line`.
- Asignar un `sequence_index` consecutivo después de seleccionar y limpiar.
- Conservar timestamps como metadata sin utilizarlos para reordenar el discurso.
- Detectar y reportar inversiones temporales sin eliminar ni reorganizar
  automáticamente los bloques solapados.
- Excluir bienvenida/presentaciones, receso, música y logística ajena a las
  ponencias.
- No reescribir el contenido con un LLM.
- No corregir términos ambiguos automáticamente.

Los límites se declaran en `config/talks.json`. Cada límite incluye un marcador
textual para que el proceso falle si cambia la fuente o se selecciona un corte
equivocado.

## Ponencias de JALMO 28

1. Mensaje de apertura — Ricardo Salinas Pliego.
2. La batalla cultural — Agustín Laje.
3. Liderazgo empresarial en la era de la inteligencia artificial — Adrián
   Villaseñor.
4. Introducción y taller de Claude — Luis Caro y Manuel Quijano.

## Representaciones acordadas

Las representaciones se mantienen separadas:

- `talks.jsonl`: ponencias limpias.
- `chunks.jsonl`: Children V1 ya generados para revisión y futuro retrieval.
- `data/derived/embeddings/*.npz`: embeddings regenerables asociados por
  `chunk_id`; no son datos canónicos.
- `parents.jsonl`: unidades futuras de contexto entregadas al LLM; todavía no
  existe.

La búsqueda se realizará posteriormente sobre Children y cada resultado podrá
resolver su futuro `parent_id`. Child V1 sigue siendo provisional hasta completar
la revisión humana. La selección de base de datos continúa pendiente.

## Ejecución

Desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe scripts\build_talks.py
.\.venv\Scripts\python.exe scripts\analyze_utterance_lengths.py
.\.venv\Scripts\python.exe scripts\build_child_chunks.py
.\.venv\Scripts\python.exe scripts\build_child_embeddings.py --local-files-only
.\.venv\Scripts\python.exe scripts\retrieve_local.py "consulta" --top-k 5 --local-files-only
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las dependencias se declaran en `pyproject.toml`. El pipeline RAW sigue usando
solo la biblioteca estándar; el análisis exploratorio utiliza
`tiktoken==0.14.0`. La versión mínima soportada es Python 3.10.

