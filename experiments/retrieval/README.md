# Experimentos de retrieval

Esta carpeta registra experimentos independientes, reproducibles y comparables.
Los datos canónicos permanecen en `data/processed/`; ningún experimento puede
modificar `talks.jsonl` ni `chunks.jsonl`.

Los scripts reutilizables viven en `scripts/`. Cada experimento fija su propia
configuración y registra sus artefactos derivados en `results/` o, cuando ya
existían antes de esta organización, los referencia mediante ruta y SHA-256.

| Experimento | Estado | Señales |
|---|---|---|
| `exp_001_dense_gte` | congelado | GTE + cosine similarity |
| `exp_002_dense_gte_bm25` | implementado hasta BM25 | Dense sin cambios y BM25 independiente |

No existe todavía comparación automática de rankings, fusión, RRF, thresholds,
reranking, Parents, Qdrant ni LLM.
