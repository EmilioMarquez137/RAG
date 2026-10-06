# exp_001_dense_gte

Baseline Dense congelado sobre los 140 Children de Child V1. Consume
exactamente `Child.text`, genera un vector normalizado de 768 dimensiones por
Child con `Alibaba-NLP/gte-multilingual-base` y ordena por cosine similarity.

## Contrato congelado

- fuente: `data/processed/chunks.jsonl`;
- SHA-256 de la fuente: `89856512f48863eb889817884199d318c9285b024cbe7eadc7e67200f29f2d1d`;
- 140 Children, sin Parents;
- modelo y revisiones fijados en `config.json`;
- CPU, `float32`, batch size 4, pooling CLS y normalización L2;
- consulta sin prefijo y documentos sin prefijo;
- cosine similarity sólo como score de ranking, no como probabilidad;
- sin thresholds, Qdrant, LLM ni evaluación formal.

Los componentes comunes siguen en `scripts/build_child_embeddings.py`,
`scripts/gte_embedding_common.py` y `scripts/retrieve_local.py`. No se movieron
para conservar las rutas existentes.

## Artefactos preservados

Los archivos binarios y reportes existentes permanecen en `data/derived/` y
`data/analysis/`. `results/artifact_registry.json` congela sus rutas, tamaños y
hashes sin duplicar el NPZ. Los smoke tests históricos forman parte del reporte
de validación referenciado; no constituyen una batería formal de evaluación.

## Ejecución

```powershell
python scripts/build_child_embeddings.py --local-files-only
python scripts/retrieve_local.py "consulta" --top-k 5 --local-files-only
```

Regenerar los embeddings reemplaza un artefacto derivado, pero no forma parte de
la creación de esta estructura experimental: el snapshot registrado corresponde
al baseline ya existente.
