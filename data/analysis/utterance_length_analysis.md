# Análisis exploratorio de longitud de utterances

Este artefacto analiza la fuente canónica sin generar chunks, parents, embeddings ni índices.
No selecciona `target_tokens` ni `overlap_tokens`.

## Tokenizer y metodología

- Biblioteca: `tiktoken==0.14.0`.
- Encoding exploratorio: `cl100k_base`.
- El encoding no se considera todavía el tokenizer definitivo del modelo de embeddings.
- Se tokeniza únicamente `utterance.text`; no se cuentan timestamps, metadata ni separadores.
- Percentiles: Hyndman-Fan tipo 7 con interpolación lineal.
- Una utterance extremadamente larga supera `P75 + 3×IQR` global.
- Las ventanas consecutivas parten de cada utterance, no cruzan ponencias y se detienen al alcanzar por primera vez cada umbral.
- Los inicios al final de una ponencia que no alcanzan el umbral se reportan, pero no entran en los percentiles.

## Estadísticas de longitud

| Ámbito | N | Mín. | Máx. | Media | Mediana | P25 | P75 | P90 | P95 | P99 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Global | 2301 | 1 | 150 | 23.08 | 18 | 10 | 31 | 45 | 59 | 86 |
| `ricardo-salinas-mensaje-apertura` | 357 | 1 | 81 | 16.78 | 12 | 7 | 23 | 36 | 43.20 | 55.20 |
| `agustin-laje-batalla-cultural` | 596 | 2 | 128 | 25.02 | 19 | 11 | 33 | 53 | 65 | 100.15 |
| `adrian-villasenor-liderazgo-ia` | 391 | 2 | 150 | 29.07 | 23 | 13 | 39.50 | 59 | 75 | 104.10 |
| `luis-caro-manuel-quijano-taller-claude` | 957 | 2 | 97 | 21.77 | 19 | 10 | 30 | 42 | 51.20 | 75 |

## Distribución global

| Tokens | Utterances | Porcentaje |
|---:|---:|---:|
| 0 | 0 | 0.00% |
| 1-5 | 210 | 9.13% |
| 6-10 | 398 | 17.30% |
| 11-20 | 661 | 28.73% |
| 21-40 | 712 | 30.94% |
| 41-80 | 288 | 12.52% |
| 81-120 | 29 | 1.26% |
| 121-160 | 3 | 0.13% |
| 161-250 | 0 | 0.00% |
| 251+ | 0 | 0.00% |

### Distribución por ponencia

#### `ricardo-salinas-mensaje-apertura`

| Tokens | Utterances | Porcentaje |
|---:|---:|---:|
| 0 | 0 | 0.00% |
| 1-5 | 61 | 17.09% |
| 6-10 | 92 | 25.77% |
| 11-20 | 95 | 26.61% |
| 21-40 | 85 | 23.81% |
| 41-80 | 23 | 6.44% |
| 81-120 | 1 | 0.28% |
| 121-160 | 0 | 0.00% |
| 161-250 | 0 | 0.00% |
| 251+ | 0 | 0.00% |

#### `agustin-laje-batalla-cultural`

| Tokens | Utterances | Porcentaje |
|---:|---:|---:|
| 0 | 0 | 0.00% |
| 1-5 | 34 | 5.70% |
| 6-10 | 95 | 15.94% |
| 11-20 | 182 | 30.54% |
| 21-40 | 194 | 32.55% |
| 41-80 | 79 | 13.26% |
| 81-120 | 11 | 1.85% |
| 121-160 | 1 | 0.17% |
| 161-250 | 0 | 0.00% |
| 251+ | 0 | 0.00% |

#### `adrian-villasenor-liderazgo-ia`

| Tokens | Utterances | Porcentaje |
|---:|---:|---:|
| 0 | 0 | 0.00% |
| 1-5 | 13 | 3.32% |
| 6-10 | 59 | 15.09% |
| 11-20 | 105 | 26.85% |
| 21-40 | 121 | 30.95% |
| 41-80 | 78 | 19.95% |
| 81-120 | 13 | 3.32% |
| 121-160 | 2 | 0.51% |
| 161-250 | 0 | 0.00% |
| 251+ | 0 | 0.00% |

#### `luis-caro-manuel-quijano-taller-claude`

| Tokens | Utterances | Porcentaje |
|---:|---:|---:|
| 0 | 0 | 0.00% |
| 1-5 | 102 | 10.66% |
| 6-10 | 152 | 15.88% |
| 11-20 | 279 | 29.15% |
| 21-40 | 312 | 32.60% |
| 41-80 | 108 | 11.29% |
| 81-120 | 4 | 0.42% |
| 121-160 | 0 | 0.00% |
| 161-250 | 0 | 0.00% |
| 251+ | 0 | 0.00% |

## Utterances extremadamente largas

Criterio: más de **94 tokens** (`P75 + 3×IQR`). 
Se identificaron **18**.

| Talk | Seq. | Línea | Tokens | Preview |
|---|---:|---:|---:|---|
| `adrian-villasenor-liderazgo-ia` | 185 | 1292 | 150 | El año de los agentes y otro punto de quiebre, que es el último que voy a mencionar hoy, se dio en febrero de 2026 con el lanzamiento de este agente que ven allá abajo esta langos… |
| `adrian-villasenor-liderazgo-ia` | 314 | 1421 | 131 | Y si tenemos contexto incompleto y data incompleta, ese es el alimento realmente ya para que la implementación es a nivel escala de IA en las empresas se puedan hacer, pero inclus… |
| `agustin-laje-batalla-cultural` | 53 | 541 | 128 | Claro, estamos pensando en términos de cultura como concepto ilustrado, pero luego, en el siglo 19, aparecieron unos sujetos llamados antropólogos y muy poquito después sociólogos… |
| `adrian-villasenor-liderazgo-ia` | 283 | 1390 | 115 | Y siempre digo que si una empresa tiene a una persona, una que logra llegar a este nivel, es una empresa que tiene la posibilidad de generar un valor exponencial brutal y esta per… |
| `adrian-villasenor-liderazgo-ia` | 50 | 1157 | 114 | Ese es el número de personas que ya utilizan aplicaciones de inteligencia artificial de forma semanal, no que la bajaron una vez para preguntar algo random, no que la bajaron una… |
| `agustin-laje-batalla-cultural` | 232 | 720 | 114 | Fukuyama escribe en 1989 un paper muy citado, muy importante para su época, que lleva el título de The End of History y dice lo siguiente Lo que podríamos estar presenciando no es… |
| `agustin-laje-batalla-cultural` | 393 | 881 | 110 | Esto es lo que llamamos nueva derecha, porque tiene nuevas estructuras políticas, porque tiene una nueva estrategia basada en la batalla cultural y porque articula tres posiciones… |
| `agustin-laje-batalla-cultural` | 236 | 724 | 104 | Esta es la primera reunión del Foro de Sao Pablo, una un grupo internacional, un foro internacional creado por Fidel Castro y un ignoto para esa época, el señor Lula da Silva, hoy… |
| `adrian-villasenor-liderazgo-ia` | 377 | 1484 | 103 | Think Big Start simple, Think Big en el mundo de la inteligencia artificial es entender que estamos al inicio de una década de una coyuntura que muchos de los retos más difíciles… |
| `agustin-laje-batalla-cultural` | 581 | 1069 | 103 | Son muy pocas las personas que quieren comprar un libro de historia, pero estas son las personas que moldean nuestra cultura los historiadores, los filósofos, los sociólogos, los… |
| `agustin-laje-batalla-cultural` | 585 | 1073 | 103 | Se los dejo como una inquietud tener una nueva escuela de pensamiento político mexicano y ser capaces de atraer y financiar, porque acá el asunto del financiamiento es clave, como… |
| `adrian-villasenor-liderazgo-ia` | 81 | 1188 | 102 | Y 4.º problema tampoco era un negociador experto, pero más o menos en lo incipiente que estaba el mundo de la inteligencia artificial hacia finales del 2023 2024 ya había empezado… |
| `adrian-villasenor-liderazgo-ia` | 141 | 1248 | 102 | Y este CEO es un ingeniero químico sofisticado y le arroja una receta, se la pasa a sus ingenieros químicos, la revisan, la prueban y después de seis años que estaban tratando de… |
| `agustin-laje-batalla-cultural` | 346 | 834 | 100 | Fíjense ustedes que funcional que es esto Entonces para aquellos que tienen apetito de no recortar el gasto público, sino al contrario, incrementarlo cada vez más, entonces la izq… |
| `adrian-villasenor-liderazgo-ia` | 357 | 1464 | 98 | Day es el fundador de Anthropic y yo personalmente la persona que más admiro en el mundo de inteligencia artificial Es el fundador de Crowd y Dario dice El miedo es un motivador y… |
| `agustin-laje-batalla-cultural` | 262 | 750 | 98 | Porque advirtieron rápido la crisis y crearon algo distinto llamado Grupo de Puebla y reorganizaron a la izquierda continental en Puebla, a partir del año 2019 y a partir del año… |
| `luis-caro-manuel-quijano-taller-claude` | 185 | 1692 | 97 | Pero algo estamos viendo también que entre más implementamos ese cinco o 6% se va creciendo de manera exponencial, porque si genera ese efecto compuesto tal cual como a veces yo v… |
| `adrian-villasenor-liderazgo-ia` | 152 | 1259 | 96 | Y también regresando a esta historia, porque estamos todavía en 2025, en 2025 fue donde ya en el ecosistema grande general de Inteligencia Artificial, surge un caso de uso como el… |

## Utterances consecutivas para alcanzar cada umbral

Los valores son conteos de utterances, no tamaños de chunks elegidos.

### Global

| Umbral | Ventanas | Colas incompletas | Mín. | Mediana | P25 | P75 | P90 | P95 | P99 | Máx. |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 250 | 2257 | 44 | 4 | 12 | 10 | 14 | 16 | 19 | 24 | 26 |
| 500 | 2202 | 99 | 9 | 22 | 19 | 26 | 30 | 34 | 40 | 46 |
| 750 | 2162 | 139 | 16 | 33 | 29 | 38 | 43 | 46.95 | 57 | 61 |
| 1000 | 2112 | 189 | 26 | 44 | 39 | 49 | 55 | 62 | 71 | 77 |

### Por ponencia

| Talk | Umbral | Ventanas | Colas incompletas | Mediana | P25 | P75 | P90 | P95 | P99 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `ricardo-salinas-mensaje-apertura` | 250 | 344 | 13 | 15.5 | 13 | 18 | 22 | 24 | 25 |
| `ricardo-salinas-mensaje-apertura` | 500 | 320 | 37 | 30 | 26 | 35 | 39 | 40 | 44.81 |
| `ricardo-salinas-mensaje-apertura` | 750 | 305 | 52 | 45 | 41 | 52 | 56 | 57 | 59.96 |
| `ricardo-salinas-mensaje-apertura` | 1000 | 284 | 73 | 60 | 54 | 66 | 71 | 72 | 75 |
| `agustin-laje-batalla-cultural` | 250 | 586 | 10 | 11 | 9 | 13 | 14 | 15 | 16 |
| `agustin-laje-batalla-cultural` | 500 | 580 | 16 | 21 | 19 | 23 | 25 | 26.05 | 28 |
| `agustin-laje-batalla-cultural` | 750 | 570 | 26 | 32 | 28 | 34 | 36 | 38 | 39.31 |
| `agustin-laje-batalla-cultural` | 1000 | 562 | 34 | 42 | 38 | 45 | 47 | 48 | 50 |
| `adrian-villasenor-liderazgo-ia` | 250 | 382 | 9 | 9 | 7 | 11 | 13 | 13 | 16 |
| `adrian-villasenor-liderazgo-ia` | 500 | 376 | 15 | 17 | 15 | 20 | 22 | 24 | 26 |
| `adrian-villasenor-liderazgo-ia` | 750 | 370 | 21 | 26 | 23 | 29 | 32 | 34 | 37.31 |
| `adrian-villasenor-liderazgo-ia` | 1000 | 359 | 32 | 34 | 31 | 38 | 41 | 46 | 48 |
| `luis-caro-manuel-quijano-taller-claude` | 250 | 945 | 12 | 12 | 10 | 14 | 16 | 18 | 23.56 |
| `luis-caro-manuel-quijano-taller-claude` | 500 | 926 | 31 | 23 | 21 | 26 | 28 | 30 | 34.75 |
| `luis-caro-manuel-quijano-taller-claude` | 750 | 917 | 40 | 35 | 32 | 38 | 41 | 42 | 45 |
| `luis-caro-manuel-quijano-taller-claude` | 1000 | 907 | 50 | 47 | 42 | 50 | 53 | 54 | 56 |

## Observaciones

- La utterance mediana tiene 18 tokens; P75 es 31 y P95 es 59.
- El máximo observado es 150 tokens.
- 18 utterances superan la cerca exterior estadística de 94 tokens; se reportan sin modificarlas.
- La cantidad de utterances necesaria varía por ponencia y por punto de inicio; el JSON conserva el detalle completo.
- Estos resultados son insumos para una decisión manual posterior. No constituyen una elección de tamaño ni overlap.
