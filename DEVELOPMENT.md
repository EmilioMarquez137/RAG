# Guía técnica y seguimiento del desarrollo

Este documento permite que una persona o asistente continúe el desarrollo sin
tener que reconstruir las decisiones técnicas desde la conversación. El contexto
funcional y la arquitectura objetivo están en [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md).

## Estado actual

Implementado:

- Lectura inmutable de la transcripción con timestamps.
- Parseo de intervenciones.
- Limpieza conservadora.
- Separación declarativa de cuatro ponencias.
- Generación de `talks.jsonl`.
- Generación de un TXT legible por ponencia.
- Manifiesto de procedencia y hashes.
- Reporte de validación.
- Pruebas de integración.
- Análisis reproducible de longitud de las 2,301 utterances con `tiktoken` y
  `cl100k_base`.
- Child V1 por utterances completas, con target aproximado de 500 tokens y
  overlap aproximado de 100.
- Validación de cobertura, continuidad, trazabilidad, overlap y conteos.
- Estadísticas e inventario de los 140 Children para revisión humana.
- Baseline Dense con GTE, embeddings normalizados y cosine similarity.
- Organización reproducible del retrieval en experimentos independientes.
- Índice y retriever BM25 lexical sobre exactamente los mismos 140 Children.

No implementado:

- Parents.
- Base de datos vectorial.
- Comparación automática Dense vs BM25.
- Fusión de rankings o RRF.
- Reranking.
- Integración con un LLM.
- API o interfaz de usuario.

## Requisitos de ejecución

- Python 3.10 o posterior.
- Dependencias declaradas en `pyproject.toml`.
- `tiktoken==0.14.0` para el análisis exploratorio de tokens.

`pyproject.toml` es la fuente de dependencias; no debe duplicarse en un
`requirements.txt` mantenido manualmente.

Preparación recomendada en Windows con el entorno Conda del proyecto:

```powershell
conda activate rag
conda install pytorch-cpu=2.8.0
python -m pip install -e ".[sentence-transformers]" --no-build-isolation
```

Todos los comandos siguientes presuponen que `rag` está activado. `.venv` no
es el entorno de ejecución del baseline de embeddings.

## Estructura relevante

```text
.
├── PROJECT_CONTEXT.md
├── DEVELOPMENT.md
├── pyproject.toml
├── config/
│   ├── talks.json
│   ├── child_v1.json
│   └── gte_embedding_baseline.json
├── experiments/retrieval/
│   ├── exp_001_dense_gte/
│   │   ├── README.md
│   │   ├── config.json
│   │   └── results/artifact_registry.json
│   └── exp_002_dense_gte_bm25/
│       ├── README.md
│       ├── config.json
│       └── results/
│           ├── bm25_index.json
│           └── bm25_validation.json
├── scripts/
│   ├── build_talks.py
│   ├── analyze_utterance_lengths.py
│   ├── build_child_chunks.py
│   ├── gte_embedding_common.py
│   ├── build_child_embeddings.py
│   ├── retrieve_local.py
│   ├── bm25_common.py
│   ├── build_bm25_index.py
│   └── retrieve_bm25.py
├── tests/
│   ├── test_build_talks.py
│   ├── test_analyze_utterance_lengths.py
│   └── test_build_child_chunks.py
└── data/
    ├── Transcripts_PlainText/
    │   └── Transcripts_Text/transcripts/
    │       └── Text_Transcript_original_AOKA-8157.txt
    ├── processed/
    │   ├── talks.jsonl
    │   ├── manifest.json
    │   ├── validation_report.json
    │   ├── chunks.jsonl
    │   ├── chunks_validation.json
    │   ├── chunks_manifest.json
    │   └── talks/
    │       └── *.txt
    └── analysis/
        ├── utterance_length_analysis.json
        ├── utterance_length_analysis.md
        ├── child_v1_statistics.json
        └── child_v1_statistics.md
```

## Pipeline implementado

```text
Text_Transcript_original_AOKA-8157.txt
    │
    ├── decodificación UTF-8 con soporte para BOM
    ├── parseo de timestamp, etiqueta y texto
    ├── normalización Unicode NFC
    ├── eliminación de FEFF y espacios redundantes
    ├── selección por límites declarados en config/talks.json
    ├── verificación de marcadores iniciales y finales
    └── preservación del orden canónico por source_line
            │
            ├── talks.jsonl
            ├── talks/*.txt
            ├── validation_report.json
            └── manifest.json
```

El script no modifica ni mueve la fuente original.

## Configuración de las ponencias

Los límites se mantienen en `config/talks.json`. Cada ponencia declara:

- `talk_id`: identificador estable.
- `title`: título documental.
- `primary_speaker`: ponente principal.
- `speakers`: lista de ponentes conocidos.
- `start_time` y `end_time`: límites inclusivos.
- `start_marker` y `end_marker`: texto esperado en los límites.

Los marcadores evitan generar documentos silenciosamente incorrectos si la
transcripción cambia. Si un marcador deja de coincidir, el pipeline falla antes
de sobrescribir las salidas.

## Contrato de `talks.jsonl`

Cada línea contiene una ponencia completa. Campos principales:

```json
{
  "schema_version": "1.1",
  "event_id": "jalmo-28",
  "talk_id": "agustin-laje-batalla-cultural",
  "title": "La batalla cultural",
  "primary_speaker": "Agustín Laje",
  "speakers": ["Agustín Laje"],
  "start_time": "01:48:51",
  "end_time": "02:56:03",
  "start_seconds": 6531,
  "end_seconds": 10563,
  "utterance_count": 596,
  "text": "...",
  "content_sha256": "...",
  "source_file": "Text_Transcript_original_AOKA-8157.txt",
  "utterances": [
    {
      "sequence_index": 0,
      "start_time": "01:48:51",
      "start_seconds": 6531,
      "text": "Y ahora nos toca escuchar a Agustín Laje con el tema La batalla Cultural.",
      "source_line": 488,
      "source_label": "J"
    }
  ]
}
```

`text` facilita el consumo de la ponencia completa. `utterances` preserva la
trazabilidad necesaria para asignar timestamps y líneas de origen a futuros
parents y children. `source_line` es el orden canónico y `sequence_index` es su
posición consecutiva dentro de la ponencia. `start_time` y `start_seconds` son
metadata temporal y no gobiernan el orden discursivo.

## Limpieza y decisiones de datos

- `BAZ` es correcto y debe preservarse.
- No se corrigen automáticamente errores semánticos de la transcripción.
- No se utiliza un LLM para reescribir el contenido.
- Las etiquetas del exportador no representan diarización fiable.
- Las ponencias registran ponentes conocidos mediante configuración manual.
- Se detectaron tres inversiones locales de timestamp en el archivo original.
  Se mantienen en el reporte de validación, pero no reordenan el texto.
- Los bloques solapados se preservan en orden de `source_line`. No se eliminan ni
  reorganizan automáticamente hasta definir una política posterior y auditable.
- La bienvenida, el receso, la música y la logística final se conservan en el
  RAW, pero no forman parte de las unidades documentales.

## Archivos de control

### `manifest.json`

Registra:

- Ruta y SHA-256 de la fuente.
- Ruta y SHA-256 de la configuración.
- Estadísticas del procesamiento.
- SHA-256 y tamaño de cada salida.

Sirve para demostrar la procedencia y detectar cambios.

### `validation_report.json`

Verifica:

- Parseo exitoso.
- Identificadores únicos.
- Rangos sin solapamiento.
- Coincidencia de marcadores.
- Ponencias no vacías.
- Eliminación de `FEFF`.
- Preservación de `BAZ`.
- Orden canónico por `source_line`.
- Índices `sequence_index` consecutivos.

Las anomalías del RAW se reportan como diagnósticos y no se ocultan.

## Comandos

Regenerar las salidas:

```powershell
python scripts/build_talks.py
```

Regenerar el análisis exploratorio de tokens:

```powershell
python scripts\analyze_utterance_lengths.py
```

Regenerar exclusivamente Child V1, su validación y estadísticas:

```powershell
python scripts\build_child_chunks.py
```

Ejecutar las pruebas:

```powershell
python -m unittest discover -s tests -v
```

Generar el baseline local de embeddings GTE una vez descargado el modelo:

```powershell
python scripts\build_child_embeddings.py --local-files-only
```

Ejecutar retrieval local por cosine similarity, sin Qdrant ni thresholds:

```powershell
python scripts\retrieve_local.py "¿Qué significa la batalla cultural?" --top-k 5 --local-files-only
```

Para inspeccionar el contenido íntegro de cada resultado en vez del preview:

```powershell
python scripts\retrieve_local.py "¿Qué significa la batalla cultural?" --top-k 5 --full-text --local-files-only
```

Regenerar exclusivamente el índice BM25 de `exp_002` y su validación:

```powershell
python scripts\build_bm25_index.py
```

Ejecutar la señal BM25 de forma independiente, sin compararla ni fusionarla con
Dense:

```powershell
python scripts\retrieve_bm25.py "batalla cultural" --top-k 5
```

El pipeline debe ejecutarse de nuevo cuando cambie:

- la transcripción fuente;
- `config/talks.json`;
- la lógica de limpieza o serialización.

No es necesario ejecutarlo para consultar los archivos ya generados.

## Análisis exploratorio de tokens

El análisis usa `tiktoken==0.14.0` con el encoding `cl100k_base`. Es una medida
exploratoria explícita y reproducible, no una elección definitiva del tokenizer
del futuro modelo de embeddings.

Se cuenta solamente `utterance.text`; timestamps, metadata y separadores quedan
fuera. El artefacto contiene estadísticas globales y por ponencia, distribuciones,
outliers mediante la cerca exterior de Tukey y ventanas consecutivas para los
umbrales exploratorios de 250, 500, 750 y 1000 tokens.

La metodología de ventanas parte de cada posición posible, acumula utterances en
orden canónico sin cruzar ponencias y se detiene cuando alcanza por primera vez
el umbral. Las colas que no lo alcanzan se reportan y se excluyen de los
percentiles. No se ha seleccionado `target_tokens` ni `overlap_tokens`.

## Child V1 implementado

El chunker consume exclusivamente `talks.jsonl`. La utterance es su unidad
atómica y `sequence_index` gobierna el orden. El target cuenta el texto completo
del Child, incluido el overlap, usando `\n` como separador canónico.

Cada registro de `chunks.jsonl` conserva límites de secuencia y líneas fuente,
conteos totales y nuevos, overlap con el Child anterior, motivo de cierre, texto
y referencias completas de sus utterances. No contiene `parent_id` porque los
Parents aún no existen.

La regla de cierre compara la distancia al target antes y después de agregar la
utterance que lo cruza. Se elige la opción más cercana y el empate incluye la
utterance. Cada Child avanza al menos una utterance nueva y los últimos Children
se emiten sin fusionar aunque sean pequeños.

## Baseline de embeddings GTE

Child V1 permanece congelado. El baseline consume exactamente `Child.text` y
usa `Alibaba-NLP/gte-multilingual-base` en la revisión
`9bbca17d9273fd0d03d5725c7a4b0f6b45142062`. El código remoto requerido por el
modelo se fija por separado en `Alibaba-NLP/new-impl` revisión
`40ced75c3017eb27626c9d4ea981bde21a2662f4`.

La inferencia implementada usa PyTorch y Transformers, pooling CLS según
`1_Pooling/config.json`, normalización L2, CPU/float32 y batch size 4. El
artefacto NPZ contiene dos arrays sin pickle: `chunk_ids` y `embeddings`. El
manifiesto conserva el mapeo de fila a `chunk_id`, hashes, revisiones y runtime.

Archivos principales:

- `config/gte_embedding_baseline.json`;
- `scripts/build_child_embeddings.py`;
- `scripts/retrieve_local.py`;
- `data/derived/embeddings/gte_multilingual_base_child_v1.npz`;
- `data/derived/embeddings/gte_multilingual_base_child_v1_manifest.json`;
- `data/analysis/gte_embedding_validation.{json,md}`.

Cosine similarity se usa solo como score de ranking. No es una probabilidad, no
se aplican thresholds y los smoke tests no constituyen una evaluación formal.
Qdrant, Parents y LLM continúan fuera de alcance.

Este baseline queda congelado como
`experiments/retrieval/exp_001_dense_gte`. Su `config.json` fija el contrato y
`results/artifact_registry.json` referencia por ruta, tamaño y SHA-256 los
artefactos históricos sin moverlos ni duplicar el NPZ.

## Experimento BM25

`experiments/retrieval/exp_002_dense_gte_bm25` conserva exactamente el Dense de
`exp_001` y añade una señal lexical independiente. Ambos consumen los mismos 140
Children; no existe todavía comparación ni fusión entre sus rankings.

BM25 V1 usa una implementación local y auditable de Okapi con `k1=1.5`,
`b=0.75` e IDF positiva
`ln(1 + (N-df+0.5)/(df+0.5))`. Documentos y consultas usan NFC, minúsculas y
tokens Unicode alfanuméricos. La puntuación se descarta como separador; se
preservan acentos y stopwords, sin stemming ni lemmatization.

El índice JSON es derivado y regenerable desde `chunks.jsonl`. Conserva el
array de `chunk_ids`, longitudes, frecuencias documentales, IDF y postings. Su
validación exige exactamente 140 IDs únicos, correspondencia 1:1 en orden de
fuente y ningún documento vacío. Los detalles completos viven en el README y
la configuración del experimento.

## Próxima decisión técnica

La etapa actual se detiene después de BM25. Antes de implementar comparación,
fusión o infraestructura se deben revisar el índice, su preprocessing y
resultados manuales. Después, mediante una decisión explícita, podrá diseñarse
una evaluación controlada y posteriormente considerar:

- filtros por metadata;
- búsqueda vectorial e híbrida;
- almacenamiento o resolución de parents;
- soporte para índices separados o tipos de registro;
- operación local frente a servicio administrado;
- costos y observabilidad.

Después se podrá diseñar y evaluar:

```text
talks.jsonl
    → chunks.jsonl                  (implementado)
    → parents.jsonl                 (pendiente)
    → embeddings
    → índice
    → retrieval de child
    → resolución de parent
    → contexto para el LLM
```

No se deben generar Parents o Children directamente desde el RAW. Child V1 se
regenera siempre desde `talks.jsonl`; los Parents se construirán posteriormente
a partir de la estructura validada de Children.

## Regla para mantener este documento

Actualizar esta guía cuando cambie alguno de estos elementos:

- estructura de carpetas;
- contratos JSON;
- comandos de ejecución;
- dependencias;
- decisiones de limpieza;
- estado de las fases;
- arquitectura de retrieval.

