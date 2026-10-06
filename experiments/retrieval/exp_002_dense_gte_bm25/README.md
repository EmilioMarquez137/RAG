# exp_002_dense_gte_bm25

Este experimento conserva sin cambios el componente Dense de
`exp_001_dense_gte` y añade BM25 como señal lexical independiente sobre los
mismos 140 valores `Child.text`.

```text
Query
├── Dense: GTE -> cosine similarity -> ranking
└── Lexical: BM25 Okapi -> ranking
```

Los rankings no se comparan ni fusionan en esta etapa. No existe RRF.

## Implementación BM25 elegida

Se utiliza una implementación local y explícita de BM25 Okapi en
`scripts/bm25_common.py`, sin una librería BM25 externa. La implementación es
pequeña, determinista, queda cubierta por pruebas y permite guardar un índice
JSON seguro y auditable sin `pickle`. La fórmula de IDF es la variante positiva:

```text
idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
```

El score suma, para cada término de la consulta:

```text
qtf * idf(t) * tf*(k1+1) / (tf + k1*(1-b+b*dl/avgdl))
```

Parámetros efectivos:

- `k1 = 1.5`;
- `b = 0.75`;
- no existe `epsilon` porque la variante de IDF elegida siempre es positiva;
- la multiplicidad de términos de la query se conserva mediante `qtf`;
- no se aplica normalización posterior ni threshold.

## Preprocessing lexical V1

Se aplica exactamente el mismo proceso a documentos y consultas:

1. normalización Unicode NFC;
2. conversión a minúsculas con `str.lower()`;
3. tokenización Unicode con la expresión `[^\W_]+`: secuencias
   alfanuméricas, excluyendo `_`;
4. la puntuación actúa como separador y no se conserva;
5. no se eliminan stopwords;
6. los acentos se conservan;
7. no hay stemming ni lemmatization.

No se modifica ningún Child. El índice registra tokens, longitudes, IDF y
postings por posición documental, con un array paralelo de `chunk_ids`.

## Artefactos y ejecución

```powershell
python scripts/build_bm25_index.py
python scripts/retrieve_bm25.py "batalla cultural" --top-k 5
python scripts/retrieve_bm25.py "batalla cultural" --top-k 5 --full-text
```

Salidas regenerables:

- `results/bm25_index.json`;
- `results/bm25_validation.json`.

Fuera de alcance: comparación Dense/BM25, fusión, RRF, nuevas queries de
evaluación, thresholds, reranking, Parents, Qdrant y LLM.
