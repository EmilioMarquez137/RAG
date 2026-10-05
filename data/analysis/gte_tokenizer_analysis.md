# Validación del tokenizer de GTE sobre Child V1

Este análisis no modifica `chunks.jsonl` ni genera embeddings, Parents o índices.

## Tokenizer y método

- Modelo: `Alibaba-NLP/gte-multilingual-base`.
- Revisión resuelta: `9bbca17d9273fd0d03d5725c7a4b0f6b45142062`.
- Implementación: `XLMRobertaTokenizerFast` (`transformers.models.xlm_roberta.tokenization_xlm_roberta_fast`).
- `tokenizer.model_max_length`: 32768 tokens.
- `config.max_position_embeddings`: 8192 tokens.
- Contexto efectivo conservador usado: 8192 tokens.
- Existe una discrepancia de metadata entre tokenizer y modelo; para seguridad prevalece el límite del modelo.
- Se tokeniza exactamente `Child.text`, sin prefijos ni metadata.
- Conteo principal: `input_ids` con tokens especiales del modelo, sin padding y sin truncación.
- `trust_remote_code=False`: el tokenizer usa la implementación estándar XLM-R de `transformers`.
- El código personalizado del repositorio aplica al cargar `AutoModel`; no se ejecutó en este análisis.

## Resultado global

| Children | Mín. | Media | Mediana | P75 | P90 | P95 | P99 | Máx. |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 140 | 149 | 441.4900 | 446 | 459.2500 | 465 | 471.2000 | 489.1000 | 495 |

## Comparación con `cl100k_base`

- Tokens GTE totales: **61808**.
- Tokens `cl100k_base` totales: **69222**.
- Ratio agregado `GTE / cl100k`: **0.8929**.
- Ratio mediano por Child: **0.8943**.

## Distribución por ponencia

| Ponencia | Children | Mín. | Media | Mediana | P75 | P90 | P95 | P99 | Máx. | Ratio agregado |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `adrian-villasenor-liderazgo-ia` | 30 | 267 | 444.53 | 448.5 | 464.5 | 468.2 | 474.95 | 481.84 | 483 | 0.8955 |
| `agustin-laje-batalla-cultural` | 39 | 237 | 435.67 | 440 | 451 | 457.6 | 462.2 | 464.62 | 465 | 0.8790 |
| `luis-caro-manuel-quijano-taller-claude` | 55 | 218 | 447.85 | 449 | 460.5 | 471 | 480.2 | 493.92 | 495 | 0.9028 |
| `ricardo-salinas-mensaje-apertura` | 16 | 149 | 428.06 | 444.5 | 454.75 | 461 | 462.5 | 463.7 | 464 | 0.8878 |

## Uso del contexto

- Children que superarían el contexto: **0 de 140 (0.0000%)**.
- El Child más largo utiliza aproximadamente **6.04%** del contexto máximo.
- Child más largo: `luis-caro-manuel-quijano-taller-claude_c0035` de `luis-caro-manuel-quijano-taller-claude`, con **495 tokens GTE** frente a 533 tokens `cl100k_base`.
- Preview: A veces nos gusta ser como perezosos, pero si nos están ahorrando esta cantidad de tiempo, por favor tómense. Tómense más de cinco minutos en elaborar un buen prompt y se van a da…

## Distribución global por rangos

| Tokens GTE | Children | Porcentaje |
|---:|---:|---:|
| 0-255 | 3 | 2.14% |
| 256-383 | 1 | 0.71% |
| 384-511 | 136 | 97.14% |
| 512-639 | 0 | 0.00% |
| 640-767 | 0 | 0.00% |
| 768-1023 | 0 | 0.00% |
| 1024+ | 0 | 0.00% |

## Conclusión automática

- No existe riesgo de truncación si ningún Child supera el contexto declarado.
- Las diferencias frente a `cl100k_base` son esperables porque se trata de vocabularios, segmentación y tokens especiales distintos.
- Los límites de Child V1 permanecen congelados; este análisis no propone resegmentación.
