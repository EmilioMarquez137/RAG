# Validación de embeddings GTE para Child V1

Este artefacto valida embeddings densos locales. No usa Qdrant, Parents, LLM ni thresholds.

## Configuración reproducible

- Modelo: `Alibaba-NLP/gte-multilingual-base`.
- Revisión de pesos: `9bbca17d9273fd0d03d5725c7a4b0f6b45142062`.
- Código remoto: `Alibaba-NLP/new-impl@40ced75c3017eb27626c9d4ea981bde21a2662f4`.
- Backend efectivo: `PyTorch + Transformers AutoModel; official CLS pooling reproduced explicitly`.
- `transformers==4.57.3`.
- `sentence-transformers==5.1.2` instalado, no usado por la anomalía documentada.
- `torch==2.8.0+cpu`; dispositivo `cpu`; dtype `float32`.
- Batch size: 4.
- Pooling: `cls`; dimensión: 768; normalización L2: sí.
- Se codifica exactamente `Child.text`, sin prefijos, metadata ni truncación.

## Validación

- Estado: **passed**.
- Embeddings: **140**.
- Shape: `[140, 768]`; dtype almacenado: `float32`.
- NaN: 0; Inf: 0; IDs duplicados: 0.
- Normas L2: mínimo 0.99999988, media 1.00000000, mediana 1.00000000, máximo 1.00000012.
- Máxima desviación absoluta respecto de 1: 0.00000012.

## Tiempos

- Carga del modelo: 2.5483 s.
- Inferencia de 140 Children: 115.6809 s.
- Rendimiento: 1.2102 Children/s.
- Smoke queries, inferencia conjunta: 0.2490 s.
- Tiempo total: 124.0297 s.

## Anomalías y decisiones

- `sentence-transformers==5.1.2` was installed but its top-level import requires Pillow; Windows denied reads from the installed PIL package. Pillow was removed because this text-only pipeline does not need it. Inference therefore uses Transformers directly with the model's official CLS pooling configuration.
- The model requires `trust_remote_code=True`; both the model revision and the external `Alibaba-NLP/new-impl` code revision are pinned and their two Python files were reviewed.
- Transformers reported that `classifier.weight` and `classifier.bias` were unused when initializing `NewModel`. This is expected for embedding inference because the base encoder is loaded without the checkpoint's task-specific classifier head.

## Smoke tests de retrieval

Son inspecciones técnicas; los scores son similitudes coseno, no probabilidades. No se aplican thresholds ni se evalúa todavía la calidad.

### ¿Cuál es el origen y la historia de Grupo Salinas?

| Rank | Cosine | Chunk | Ponencia | Secuencias |
|---:|---:|---|---|---|
| 1 | 0.807278 | `ricardo-salinas-mensaje-apertura_c0000` | `ricardo-salinas-mensaje-apertura` | 0–23 |
| 2 | 0.671381 | `ricardo-salinas-mensaje-apertura_c0001` | `ricardo-salinas-mensaje-apertura` | 18–47 |
| 3 | 0.641036 | `adrian-villasenor-liderazgo-ia_c0017` | `adrian-villasenor-liderazgo-ia` | 211–234 |
| 4 | 0.550914 | `adrian-villasenor-liderazgo-ia_c0010` | `adrian-villasenor-liderazgo-ia` | 133–143 |
| 5 | 0.541832 | `luis-caro-manuel-quijano-taller-claude_c0039` | `luis-caro-manuel-quijano-taller-claude` | 661–684 |

### ¿Qué significa la batalla cultural y por qué es importante?

| Rank | Cosine | Chunk | Ponencia | Secuencias |
|---:|---:|---|---|---|
| 1 | 0.891807 | `agustin-laje-batalla-cultural_c0001` | `agustin-laje-batalla-cultural` | 15–36 |
| 2 | 0.853096 | `agustin-laje-batalla-cultural_c0004` | `agustin-laje-batalla-cultural` | 57–73 |
| 3 | 0.825031 | `agustin-laje-batalla-cultural_c0005` | `agustin-laje-batalla-cultural` | 69–90 |
| 4 | 0.771028 | `agustin-laje-batalla-cultural_c0009` | `agustin-laje-batalla-cultural` | 127–147 |
| 5 | 0.746602 | `agustin-laje-batalla-cultural_c0002` | `agustin-laje-batalla-cultural` | 34–50 |

### ¿Qué retos plantea la inteligencia artificial para el liderazgo empresarial?

| Rank | Cosine | Chunk | Ponencia | Secuencias |
|---:|---:|---|---|---|
| 1 | 0.796247 | `adrian-villasenor-liderazgo-ia_c0007` | `adrian-villasenor-liderazgo-ia` | 100–115 |
| 2 | 0.779187 | `adrian-villasenor-liderazgo-ia_c0022` | `adrian-villasenor-liderazgo-ia` | 290–308 |
| 3 | 0.769815 | `adrian-villasenor-liderazgo-ia_c0016` | `adrian-villasenor-liderazgo-ia` | 199–215 |
| 4 | 0.758773 | `adrian-villasenor-liderazgo-ia_c0017` | `adrian-villasenor-liderazgo-ia` | 211–234 |
| 5 | 0.747513 | `adrian-villasenor-liderazgo-ia_c0023` | `adrian-villasenor-liderazgo-ia` | 306–319 |

### ¿Cómo puede Claude ayudar a trabajar con documentos y presentaciones?

| Rank | Cosine | Chunk | Ponencia | Secuencias |
|---:|---:|---|---|---|
| 1 | 0.686247 | `luis-caro-manuel-quijano-taller-claude_c0023` | `luis-caro-manuel-quijano-taller-claude` | 383–401 |
| 2 | 0.666472 | `luis-caro-manuel-quijano-taller-claude_c0054` | `luis-caro-manuel-quijano-taller-claude` | 945–956 |
| 3 | 0.655773 | `luis-caro-manuel-quijano-taller-claude_c0040` | `luis-caro-manuel-quijano-taller-claude` | 682–702 |
| 4 | 0.654205 | `luis-caro-manuel-quijano-taller-claude_c0052` | `luis-caro-manuel-quijano-taller-claude` | 907–925 |
| 5 | 0.640285 | `luis-caro-manuel-quijano-taller-claude_c0024` | `luis-caro-manuel-quijano-taller-claude` | 397–420 |
