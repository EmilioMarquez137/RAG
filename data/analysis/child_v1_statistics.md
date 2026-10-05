# Child V1: estadísticas y revisión

Este reporte describe Children reales. No se generaron Parents, embeddings ni índices vectoriales.

## Configuración

- Algoritmo: `child-v1-nearest-complete-utterance`.
- Target aproximado: 500 tokens.
- Overlap aproximado: 100 tokens.
- Tokenizer provisional: `tiktoken==0.14.0` / `cl100k_base`.
- Unidad atómica: utterance completa.
- Regla de cruce: opción más cercana; empate incluye la utterance.
- El target mide el payload completo, incluido el overlap.
- Serialización: textos unidos por `\n`.

## Validación

Estado: **passed**.

| Check | Resultado |
|---|---|
| `chunks_nonempty` | OK |
| `chunk_ids_unique` | OK |
| `talk_boundaries_respected` | OK |
| `chunk_indexes_consecutive` | OK |
| `utterances_consecutive` | OK |
| `text_reproducible` | OK |
| `token_counts_reproducible` | OK |
| `content_hashes_reproducible` | OK |
| `traceability_boundaries_match` | OK |
| `at_least_one_new_utterance` | OK |
| `overlap_matches_previous_suffix` | OK |
| `overlap_is_minimal_suffix_reaching_target` | OK |
| `closure_rule_respected` | OK |
| `new_utterance_coverage_exactly_once` | OK |
| `no_parent_fields` | OK |

## Resumen global

- Children: **140**.
- Tokens por Child: mínimo 158, mediana 501, media 494.44, P95 522.05, máximo 533.
- Desviación absoluta del target: mediana 8, P95 29.15, máxima 342.
- Debajo/igual/encima del target: 62/2/76.
- Overshoot máximo: 33 tokens.
- Overlap real: mediana 110.5, P95 153.75, máximo 183 tokens.
- Excluyendo los cuatro Children finales: mediana 502, P95 522.25, rango 471–533 tokens; desviación máxima 33.

## Resumen por ponencia

| Talk | Chunks | Tokens mín. | Mediana | Media | P95 | Máx. | Overlap mediano |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ricardo-salinas-mensaje-apertura` | 16 | 158 | 502 | 482.19 | 513.25 | 517 | 106 |
| `agustin-laje-batalla-cultural` | 39 | 275 | 502 | 495.64 | 519.6 | 527 | 111 |
| `adrian-villasenor-liderazgo-ia` | 30 | 309 | 499 | 496.4 | 529.75 | 532 | 110 |
| `luis-caro-manuel-quijano-taller-claude` | 55 | 231 | 501 | 496.09 | 521.3 | 533 | 113 |

## Último Child de cada ponencia

| Talk | Chunk | Tokens totales | Tokens nuevos | Utterances | Utterances nuevas |
|---|---|---:|---:|---:|---:|
| `ricardo-salinas-mensaje-apertura` | `ricardo-salinas-mensaje-apertura_c0015` | 158 | 20 | 9 | 2 |
| `agustin-laje-batalla-cultural` | `agustin-laje-batalla-cultural_c0038` | 275 | 128 | 11 | 7 |
| `adrian-villasenor-liderazgo-ia` | `adrian-villasenor-liderazgo-ia_c0029` | 309 | 205 | 12 | 7 |
| `luis-caro-manuel-quijano-taller-claude` | `luis-caro-manuel-quijano-taller-claude_c0054` | 231 | 111 | 12 | 7 |

## Inventario para revisión humana

| Chunk | Seq. total | Seq. nueva | Tokens | Overlap | Nuevas | Cierre | Preview |
|---|---|---|---:|---:|---:|---|---|
| `ricardo-salinas-mensaje-apertura_c0000` | 0–23 | 0–23 | 502 | 0 | 502 | `closest_after` | Y ya para para dar inicio a estas sesiones vamos a darle la bienvenida a mi papá Ricardo Salinas Pliego. Muy bien! Buen día! Qué gusto verl… |
| `ricardo-salinas-mensaje-apertura_c0001` | 18–47 | 24–47 | 499 | 125 | 374 | `closest_before` | Y ahí decimos que nace el Grupo Salinas, porque la fábrica se llama Salinas y Rocha, fábrica de Camas. Y hace 20 años aquí con Mario San Ro… |
| `ricardo-salinas-mensaje-apertura_c0002` | 40–69 | 48–69 | 502 | 104 | 398 | `tie_include` | Pero me quedé pensando qué barbaridad! Es que realmente el tiempo pasa demasiado rápido. Ya son 20 años de eso ya ni quien se acuerda de Ca… |
| `ricardo-salinas-mensaje-apertura_c0003` | 63–89 | 70–89 | 501 | 105 | 396 | `closest_after` | Y ahí podríamos extendernos a por qué esto y todo, pero nada más. Quiero que se graben, que eso hace 20 años era igual, ahora está peor, pe… |
| `ricardo-salinas-mensaje-apertura_c0004` | 86–109 | 90–109 | 502 | 102 | 400 | `closest_after` | Tú lo ves en el fútbol, este lo ves en la música hay distintos talentos, verdad? El vocalista y el baterista son hacen cosas distintas y el… |
| `ricardo-salinas-mensaje-apertura_c0005` | 103–126 | 110–126 | 517 | 102 | 415 | `closest_after` | Pero era el presidente de Venezuela y va y lo refunde y estaba dormido en su casa a las 00:00 de la. Noche y. Al día siguiente a las 00:00… |
| `ricardo-salinas-mensaje-apertura_c0006` | 122–148 | 127–148 | 504 | 142 | 362 | `closest_after` | Nos publicaron ayer en Estados Unidos una orden ejecutiva diciendo y los que están en Estados Unidos de forma ilegal, o sea los paisanos me… |
| `ricardo-salinas-mensaje-apertura_c0007` | 144–170 | 149–170 | 501 | 106 | 395 | `closest_after` | Tenemos buenas ideas, estamos bien posicionados en todo lo que hacemos en las tiendas, Neto, en en la telecomunicación, en la televisión. E… |
| `ricardo-salinas-mensaje-apertura_c0008` | 168–193 | 171–193 | 497 | 118 | 379 | `closest_before` | Ahorita, ahora, teniendo esa meta de largo aliento y articulándola, es interesante como primero tienes la idea y el sentimiento y luego com… |
| `ricardo-salinas-mensaje-apertura_c0009` | 189–228 | 194–228 | 509 | 105 | 404 | `closest_after` | Y la inteligencia artificial y el empleo Y el gobierno. Y fíjense que está muy triste la situación del empleo, no nada más en México, sino… |
| `ricardo-salinas-mensaje-apertura_c0010` | 221–253 | 229–253 | 512 | 110 | 402 | `closest_after` | Bueno, déjeme darles otro dato interesante México tiene una población de 130 millones. De personas, de los cuales hay 70 millones inactivos… |
| `ricardo-salinas-mensaje-apertura_c0011` | 244–274 | 254–274 | 508 | 112 | 396 | `closest_after` | Tenemos la necesidad de repeler ese ataque y defender lo nuestro. Y nos van a acusar de ilegales, no ilegales. Son ellos ilegales, inmorale… |
| `ricardo-salinas-mensaje-apertura_c0012` | 272–300 | 275–300 | 505 | 103 | 402 | `closest_after` | Hay que ver lo diferente. La gente que tenemos va a ser mucho más productiva y va a ganar mucho más dinero porque va a contribuir mucho más… |
| `ricardo-salinas-mensaje-apertura_c0013` | 290–327 | 301–327 | 494 | 138 | 356 | `closest_before` | Entonces en este Jalmo vamos a gastar mucho tiempo en eso y yo creo que es una herramienta poderosísima que tenemos que aprender a usar tod… |
| `ricardo-salinas-mensaje-apertura_c0014` | 319–354 | 328–354 | 504 | 103 | 401 | `closest_after` | Cuello No se puede hacer negocio con malas personas y por eso tenemos un sistema de honesto y de investigaciones. Y todo porque tenemos que… |
| `ricardo-salinas-mensaje-apertura_c0015` | 348–356 | 355–356 | 158 | 138 | 20 | `end_of_talk` | Frente a los abusos del gobierno en con el gasto, con la creación de dinero falso, con la depredación fiscal frente a la inestabilidad soci… |
| `agustin-laje-batalla-cultural_c0000` | 0–18 | 0–18 | 487 | 0 | 487 | `closest_before` | Y ahora nos toca escuchar a Agustín Laje con el tema La batalla Cultural. Vamos a darle la bienvenida, por favor, Maestro, Muchas gracias.… |
| `agustin-laje-batalla-cultural_c0001` | 15–36 | 19–36 | 494 | 116 | 378 | `closest_before` | Yo me dedico a impulsar las ideas de la libertad a nivel continental. De hecho, mañana me tengo que ir a Colombia, donde tenemos elecciones… |
| `agustin-laje-batalla-cultural_c0002` | 34–50 | 37–50 | 509 | 106 | 403 | `closest_after` | Cultura es tan difícil como concepto que hace algunos años a la Universidad de Oxford se le ocurrió publicar un libro donde compilaran todo… |
| `agustin-laje-batalla-cultural_c0003` | 49–58 | 51–58 | 506 | 112 | 394 | `closest_after` | Cuando decimos, por ejemplo, Juancito es muy culto y Pedrito es muy inculto, estamos pensando en términos de un concepto ilustrado de cultu… |
| `agustin-laje-batalla-cultural_c0004` | 57–73 | 59–73 | 504 | 152 | 352 | `closest_after` | En ese sentido evoca una serie de componentes que van a ver y estudiar tanto los antropólogos como los sociólogos, tales como el lenguaje,… |
| `agustin-laje-batalla-cultural_c0005` | 69–90 | 74–90 | 510 | 101 | 409 | `closest_after` | Decíamos el concepto ilustrado de cultura. Qué tipo de instituciones están en relación con este concepto? Bueno, la literatura, las escuela… |
| `agustin-laje-batalla-cultural_c0006` | 85–103 | 91–103 | 488 | 110 | 378 | `closest_before` | Me encantó cómo cerró Don Salinas cuando dijo La palabra mala es la igualdad. La palabra buena es la libertad. Claro, porque no se puede te… |
| `agustin-laje-batalla-cultural_c0007` | 102–116 | 104–116 | 505 | 110 | 395 | `closest_after` | Hace poco hicimos en Argentina desde la Fundación Faro una investigación que nos dio unos resultados maravillosos, precisamente pensando en… |
| `agustin-laje-batalla-cultural_c0008` | 112–129 | 117–129 | 495 | 104 | 391 | `closest_before` | Creo que la batalla de ideas, la cosa no está tan mal, La batalla por la historia más o menos tenemos conciencia de eso. Batalla por el len… |
| `agustin-laje-batalla-cultural_c0009` | 127–147 | 130–147 | 519 | 110 | 409 | `tie_include` | Al contrario, si uno tiene, por ejemplo, Batalla cultural pero no tiene batalla política, puede cambiar el entorno. Pero al final los candi… |
| `agustin-laje-batalla-cultural_c0010` | 145–159 | 148–159 | 482 | 140 | 342 | `closest_before` | Al contrario, la batalla cultural es un descubrimiento de la izquierda cuando cuando descubre la izquierda, la batalla cultural la descubre… |
| `agustin-laje-batalla-cultural_c0011` | 155–174 | 160–174 | 501 | 135 | 366 | `closest_after` | Para el marxismo clásico la cuestión era muy sencilla hacer una revolución armada, tomar el poder, expropiar al empresario, centralizar los… |
| `agustin-laje-batalla-cultural_c0012` | 171–190 | 175–190 | 519 | 104 | 415 | `closest_after` | En Italia hay un señor llamado Antonio Gramsci. No sé si alguien lo habrá escuchado alguna vez. Antonio Gramsci, líder del Partido Comunist… |
| `agustin-laje-batalla-cultural_c0013` | 186–209 | 191–209 | 474 | 130 | 344 | `closest_before` | Esto es una forma de decir lo que Ricardo dijo recién cuando dijo Primero hay que ganar la batalla cultural para poder ganar la batalla ele… |
| `agustin-laje-batalla-cultural_c0014` | 208–224 | 210–224 | 493 | 107 | 386 | `closest_before` | Es decir, los hábitos, los usos, las costumbres, el arte, la religión, la filosofía, constituyen en su entrelazamiento los factores dinámic… |
| `agustin-laje-batalla-cultural_c0015` | 221–232 | 225–232 | 498 | 134 | 364 | `closest_before` | En mayo de 1988, por primera vez no eran los obreros de izquierdas los que generaban una revuelta en las calles, sino que eran los estudian… |
| `agustin-laje-batalla-cultural_c0016` | 232–242 | 233–242 | 498 | 114 | 384 | `closest_before` | Fukuyama escribe en 1989 un paper muy citado, muy importante para su época, que lleva el título de The End of History y dice lo siguiente L… |
| `agustin-laje-batalla-cultural_c0017` | 237–256 | 243–256 | 497 | 121 | 376 | `closest_before` | Ya se había visto que en los 60, 70 y 80 la guerra de guerrillas, salvo en Cuba, no dio resultado en ningún otro lugar. No lo dio ni en Chi… |
| `agustin-laje-batalla-cultural_c0018` | 253–274 | 257–274 | 517 | 105 | 412 | `closest_after` | Hugo Chávez y su sucesor, Nicolás Maduro. Y ahora veremos qué pasa con Delcy, también del Foro de Sao Pablo. En Paraguay estuvo Lugo, que d… |
| `agustin-laje-batalla-cultural_c0019` | 272–295 | 275–295 | 516 | 109 | 407 | `closest_after` | Pero bueno, miren lo que es la hegemonía total y completa, incluyendo a Estados Unidos en manos del Partido Demócrata más radicalizado de l… |
| `agustin-laje-batalla-cultural_c0020` | 292–313 | 296–313 | 509 | 152 | 357 | `closest_after` | El woke, que es una expresión radical de la izquierda cultural, que tiene sus raíces más profundas en la Escuela de Frankfurt, supone que l… |
| `agustin-laje-batalla-cultural_c0021` | 309–329 | 314–329 | 505 | 100 | 405 | `closest_after` | Y aquí se puede ser cisgénero o transgénero. Ustedes miran qué cisgénero? Bueno, el transgénero es aquel que se autopercibe con una sexuali… |
| `agustin-laje-batalla-cultural_c0022` | 325–346 | 330–346 | 525 | 107 | 418 | `closest_after` | El sistema de opresión se llama fundamentalismo religioso. Tenemos una nacionalidad, el nacional del Estado en el que vive el opresor. Resp… |
| `agustin-laje-batalla-cultural_c0023` | 346–365 | 347–365 | 484 | 100 | 384 | `closest_before` | Fíjense ustedes que funcional que es esto Entonces para aquellos que tienen apetito de no recortar el gasto público, sino al contrario, inc… |
| `agustin-laje-batalla-cultural_c0024` | 360–379 | 366–379 | 502 | 112 | 390 | `closest_after` | El Partido Republicano, desde donde él dio batalla cultural durante muchos años empezó a crecer políticamente. Las elecciones del 2021 las… |
| `agustin-laje-batalla-cultural_c0025` | 375–393 | 380–393 | 527 | 126 | 401 | `closest_after` | Javier Milei surge por derecha porque lo que había funcionado como centro centro derecha en Argentina era una porquería, que era el macrism… |
| `agustin-laje-batalla-cultural_c0026` | 393–413 | 394–413 | 514 | 110 | 404 | `tie_include` | Esto es lo que llamamos nueva derecha, porque tiene nuevas estructuras políticas, porque tiene una nueva estrategia basada en la batalla cu… |
| `agustin-laje-batalla-cultural_c0027` | 410–434 | 414–434 | 483 | 103 | 380 | `closest_before` | Porque son dictaduras, o bien porque hicieron fraude o bien porque maniataron de tal manera el sistema electoral que nadie puede decir que… |
| `agustin-laje-batalla-cultural_c0028` | 427–448 | 435–448 | 493 | 105 | 388 | `closest_before` | Esto pasó en Chile con la experiencia de Piñera. Pasó en Colombia con la experiencia de Santos y de Iván Duque. También pasó en Argentina c… |
| `agustin-laje-batalla-cultural_c0029` | 445–467 | 449–467 | 508 | 117 | 391 | `closest_after` | Yo por mes les decía más o menos visitó tres países distintos impulsando estas ideas. Yo estoy en mi casa solo la mitad del mes, la otra mi… |
| `agustin-laje-batalla-cultural_c0030` | 462–484 | 468–484 | 508 | 136 | 372 | `closest_after` | Por eso es muy importante amigar a los libertarios con los conservadores y con el nacionalismo de derecha que en este país, por cierto, cas… |
| `agustin-laje-batalla-cultural_c0031` | 480–502 | 485–502 | 504 | 101 | 403 | `closest_after` | Uno con la frente en alta, diga Sí, claro. Después podemos discutir qué significa izquierda, qué significa derecha. Yo doy por hecho que má… |
| `agustin-laje-batalla-cultural_c0032` | 499–513 | 503–513 | 490 | 113 | 377 | `closest_before` | En el espacio de la libertad avanza, uno encuentra distintas derechas que han aprendido a convivir, pero todas tienen claro de que hay doct… |
| `agustin-laje-batalla-cultural_c0033` | 510–533 | 514–533 | 499 | 116 | 383 | `closest_before` | Cuando la casta política o los de siempre se vayan del poder, tu vida va a mejorar. Por qué? Porque voy a meter preso a los delincuentes, v… |
| `agustin-laje-batalla-cultural_c0034` | 531–549 | 534–549 | 506 | 111 | 395 | `closest_after` | En todos los casos tiene que haber un lenguaje popular y tiene que haber expresiones políticamente incorrectas que le diferencien a uno de… |
| `agustin-laje-batalla-cultural_c0035` | 548–565 | 550–565 | 487 | 104 | 383 | `closest_before` | Tomo dos dos minutos más acá ya me dice cero dos minutos más como para poder cerrar esto, por favor. Cuando Milei perdió el debate con Serg… |
| `agustin-laje-batalla-cultural_c0036` | 561–578 | 566–578 | 493 | 111 | 382 | `closest_before` | Esta es la parte que a veces se entiende menos, porque se piensa que los intelectuales llegan a muy poquita gente. Y es cierto, los intelec… |
| `agustin-laje-batalla-cultural_c0037` | 573–588 | 579–588 | 506 | 127 | 379 | `closest_after` | Y estas personas, a diferencia de las que trabajan sobre cosas tangibles, duras, reales, materiales, como puede ser un ingeniero, por ejemp… |
| `agustin-laje-batalla-cultural_c0038` | 585–595 | 589–595 | 275 | 147 | 128 | `end_of_talk` | Se los dejo como una inquietud tener una nueva escuela de pensamiento político mexicano y ser capaces de atraer y financiar, porque acá el… |
| `adrian-villasenor-liderazgo-ia_c0000` | 0–20 | 0–20 | 532 | 0 | 532 | `closest_after` | Y ahora vamos a recibir a Yasmina Q es el c o the big simple. I O como dice el señor Salinas, la cosa inteligente y lista que nos va a plat… |
| `adrian-villasenor-liderazgo-ia_c0001` | 19–37 | 21–37 | 502 | 127 | 375 | `closest_after` | Y cuando iba todos estos países redefiniendo las estrategias de estas empresas, me tocaba estar subido en los camiones para entender realme… |
| `adrian-villasenor-liderazgo-ia_c0002` | 33–47 | 38–47 | 488 | 103 | 385 | `closest_before` | Yo les decía y todo mundo les decían los teléfonos de chicles. Y cuando me dijeron pues pagos móviles, yo dije me están choreando. La verda… |
| `adrian-villasenor-liderazgo-ia_c0003` | 45–58 | 48–58 | 486 | 105 | 381 | `closest_before` | Quiero entender cómo puedo estar realmente en en el centro de cómo las tecnologías pueden generar valor, transformación y realmente hacer u… |
| `adrian-villasenor-liderazgo-ia_c0004` | 54–72 | 59–72 | 496 | 117 | 379 | `closest_before` | La primera es que era algo que todavía no estaban seguros de cuál iba a ser el impacto era algo experimental. Y la segunda es que se quiera… |
| `adrian-villasenor-liderazgo-ia_c0005` | 68–85 | 73–85 | 518 | 110 | 408 | `closest_after` | No queremos que vengas con nadie de tu familia porque tú eres alguien externo a todo este desmadre. Queremos que vengas abogados, nada más.… |
| `adrian-villasenor-liderazgo-ia_c0006` | 83–101 | 86–101 | 527 | 107 | 420 | `closest_after` | Y qué fue lo que hice? Pues me armé un hito dentro de Chatgpt todavía Cloud. Como que no escuchamos mucho de esto, lo alimenté, lo que habí… |
| `adrian-villasenor-liderazgo-ia_c0007` | 100–115 | 102–115 | 514 | 106 | 408 | `closest_after` | Preparar reportes para inversionistas, hacer análisis financiero, hacer tener conversaciones difíciles, construir cultura, tareas administr… |
| `adrian-villasenor-liderazgo-ia_c0008` | 112–126 | 116–126 | 514 | 151 | 363 | `closest_after` | Y en ese proceso, mientras yo estaba cambiando, que de hecho dejo la dirección general de esa empresa que que lideré por siete años para fu… |
| `adrian-villasenor-liderazgo-ia_c0009` | 123–136 | 127–136 | 492 | 173 | 319 | `closest_before` | Y aquí fue en una conversación que tuve con un director general que ahorita les voy a platicar, que llegamos a esta realización, que antes… |
| `adrian-villasenor-liderazgo-ia_c0010` | 133–143 | 137–143 | 510 | 121 | 389 | `closest_after` | Logramos identificar 5 millones de dólares a Levitt en un año, sin hacer un centavo adicional de inversión y estamos perfilando que sean ce… |
| `adrian-villasenor-liderazgo-ia_c0011` | 141–155 | 144–155 | 499 | 174 | 325 | `closest_before` | Y este CEO es un ingeniero químico sofisticado y le arroja una receta, se la pasa a sus ingenieros químicos, la revisan, la prueban y despu… |
| `adrian-villasenor-liderazgo-ia_c0012` | 153–168 | 156–168 | 496 | 128 | 368 | `closest_before` | Y ahorita les voy a explicar por qué este caso de uso es importante como reflexión general, pero si vemos esa gráfica, esa gráfica básicame… |
| `adrian-villasenor-liderazgo-ia_c0013` | 166–180 | 169–180 | 498 | 110 | 388 | `closest_before` | Hoy la IA cree ese puente y yo que al final soy emprendedor de tecnología, pero no soy técnico o desarrollo de software, una parte importan… |
| `adrian-villasenor-liderazgo-ia_c0014` | 179–190 | 181–190 | 501 | 141 | 360 | `closest_after` | Porque en el centro de cómo podemos como usuarios generar valor en el uso de la inteligencia artificial están las ideas, Está el entender u… |
| `adrian-villasenor-liderazgo-ia_c0015` | 186–201 | 191–201 | 491 | 107 | 384 | `closest_before` | Trabaja por ti, desarrolla por ti. Y aquí empezó a cambiar de nuevo otro paradigma el tema de cómo las organizaciones, personas, agentes e… |
| `adrian-villasenor-liderazgo-ia_c0016` | 199–215 | 202–215 | 501 | 151 | 350 | `closest_after` | Todavía no estamos llegando ahí, pero empieza a verse que el principal cuello de botella para generar estos resultados es un tema de lidera… |
| `adrian-villasenor-liderazgo-ia_c0017` | 211–234 | 216–234 | 491 | 125 | 366 | `closest_before` | Tú BAZ a seguir siendo responsable de esos resultados, pero si bien hay cosas que no cambian, hay cosas que sí cambian y cosas que sí están… |
| `adrian-villasenor-liderazgo-ia_c0018` | 232–251 | 235–251 | 492 | 103 | 389 | `closest_before` | Y quiero entonces platicarles el cómo se ve esto de forma específica. Primero, cómo pueden ustedes construir este liderazgo de personal com… |
| `adrian-villasenor-liderazgo-ia_c0019` | 248–267 | 252–267 | 515 | 104 | 411 | `closest_after` | Prompts, prompts, prompts no? Y la verdad que esa era la realidad. 2024 Estábamos en esta fase donde estábamos entendiendo que deconstruyen… |
| `adrian-villasenor-liderazgo-ia_c0020` | 265–281 | 268–281 | 502 | 100 | 402 | `closest_after` | Y te BAZ quitando tareas. Yo siempre digo que si recuerdan la película de Matrix en la imagen donde a Neo está tratando de aprender artes m… |
| `adrian-villasenor-liderazgo-ia_c0021` | 278–292 | 282–292 | 499 | 105 | 394 | `closest_before` | Estás escribiéndole directamente ahí a Cloud? No tienes que estar haciendo cosas en los diferentes sistemas y Cloud se vuelve ese sistema o… |
| `adrian-villasenor-liderazgo-ia_c0022` | 290–308 | 293–308 | 511 | 111 | 400 | `closest_after` | Si los agentes, pero al final va a transformar las organizaciones. Desde esta perspectiva. Y esto es la parte individual, Ese fue el centro… |
| `adrian-villasenor-liderazgo-ia_c0023` | 306–319 | 309–319 | 497 | 105 | 392 | `closest_before` | Y aquí es donde ya no podemos hablar nada más de lo que yo puedo hacer con la inteligencia artificial. Aquí sí tenemos que empezar a pensar… |
| `adrian-villasenor-liderazgo-ia_c0024` | 317–334 | 320–334 | 532 | 109 | 423 | `closest_after` | Porque si tienes la parte tres pero no tienes la uno y la dos, no sirve de mucho, y esta parte sí le toca a los departamentos de TI. Si es… |
| `adrian-villasenor-liderazgo-ia_c0025` | 332–350 | 335–350 | 471 | 107 | 364 | `closest_before` | Y la realidad es que el cambio organizacional, cuando un agente tiene un impacto y una persona lo usa, se crea un agente y tiene valor. La.… |
| `adrian-villasenor-liderazgo-ia_c0026` | 346–361 | 351–361 | 497 | 131 | 366 | `closest_before` | Un futuro donde realmente la productividad que podamos crear cree realmente estructuras que nos permitan tener un futuro increíble y alguna… |
| `adrian-villasenor-liderazgo-ia_c0027` | 357–371 | 362–371 | 518 | 183 | 335 | `closest_after` | Day es el fundador de Anthropic y yo personalmente la persona que más admiro en el mundo de inteligencia artificial Es el fundador de Crowd… |
| `adrian-villasenor-liderazgo-ia_c0028` | 370–383 | 372–383 | 493 | 104 | 389 | `closest_before` | No lo tengo completamente claro cómo, pero en el momento que tú quieras regresar a ser el CEO de tu empresa a ejercer y a generar valor, co… |
| `adrian-villasenor-liderazgo-ia_c0029` | 379–390 | 384–390 | 309 | 104 | 205 | `end_of_talk` | Pero regresemos al tema de que la IA es tan democrática que requiere de pensamiento crítico y todos podemos pensar bien para cambiar nuestr… |
| `luis-caro-manuel-quijano-taller-claude_c0000` | 0–32 | 0–32 | 491 | 0 | 491 | `closest_before` | Y ahora, eh, vamos a recibir a Luis Caro y a Manu Quijano para comenzar con el primer módulo del taller de Cloth. Bienvenidos. Por favor. H… |
| `luis-caro-manuel-quijano-taller-claude_c0001` | 29–45 | 33–45 | 517 | 125 | 392 | `closest_after` | Un estudio de una investigación científica que él leyó comparando la eficiencia locomotora de todas las especies del planeta Tierra. Cuánta… |
| `luis-caro-manuel-quijano-taller-claude_c0002` | 41–68 | 46–68 | 493 | 103 | 390 | `closest_before` | Entonces vamos a hablar hoy un poco. Voy a pasar ese video de Clot. Qué es? De las herramientas que vamos a ver hoy en día, vamos a aclarar… |
| `luis-caro-manuel-quijano-taller-claude_c0003` | 64–86 | 69–86 | 512 | 133 | 379 | `closest_after` | Tu podías a las primeras versiones de GPT pedirles que te ayudaran a crear una bomba y te daban el manual detalladito y podías hacer cosas… |
| `luis-caro-manuel-quijano-taller-claude_c0004` | 83–96 | 87–96 | 480 | 113 | 367 | `closest_before` | Llamaron al primer modelo Clod, lanzó una versión, salió una versión del modelo versión uno que se llamaba Solo Clod y ya el modelo va por… |
| `luis-caro-manuel-quijano-taller-claude_c0005` | 92–108 | 97–108 | 480 | 138 | 342 | `closest_before` | Entonces en ese momento antrópico, la versión 4.0 nos ofrece tres modelos diferentes HIGH, que es el más rápido Sonet, que es el intermedio… |
| `luis-caro-manuel-quijano-taller-claude_c0006` | 104–118 | 109–118 | 501 | 135 | 366 | `closest_after` | Ah, pero para calcular el interés compuesto yo voy a usar esta herramienta que es una calculadora y yo voy a multiplicar el rendimiento del… |
| `luis-caro-manuel-quijano-taller-claude_c0007` | 115–131 | 119–131 | 489 | 169 | 320 | `closest_before` | Hablamos de que hay empresas que usan esos modelos directamente desde su software, pero también antrópica lanzó sus propias aplicaciones, s… |
| `luis-caro-manuel-quijano-taller-claude_c0008` | 128–153 | 132–153 | 498 | 106 | 392 | `closest_before` | Como digo, de ambos chat es más para preguntas y respuestas cowork es para que nuestro computador sea ese agente personal y pueda hacer tar… |
| `luis-caro-manuel-quijano-taller-claude_c0009` | 145–171 | 154–171 | 506 | 130 | 376 | `tie_include` | Y Jensen Huang, CEO de Nvidia, dice que ahora a los desarrolladores de software hay que pagarles la mitad del salario en tokens, no? Qué es… |
| `luis-caro-manuel-quijano-taller-claude_c0010` | 168–188 | 172–188 | 504 | 100 | 404 | `closest_after` | Por ejemplo, aquí tenemos el caso de Made.com, que es una empresa que hoy en día gracias a estas tecnologías ha logrado ahorrar diez horas… |
| `luis-caro-manuel-quijano-taller-claude_c0011` | 185–205 | 189–205 | 500 | 167 | 333 | `exact_target` | Pero algo estamos viendo también que entre más implementamos ese cinco o 6% se va creciendo de manera exponencial, porque si genera ese efe… |
| `luis-caro-manuel-quijano-taller-claude_c0012` | 201–226 | 206–226 | 495 | 134 | 361 | `closest_before` | Y ahí nosotros, en colaboración con Anthropic, también hemos hecho un trabajo muy increíble de cómo utilizamos agentes de inteligencia arti… |
| `luis-caro-manuel-quijano-taller-claude_c0013` | 221–244 | 227–244 | 507 | 103 | 404 | `closest_after` | Clot Eh. Por qué no me muestras mi agenda para el día de hoy? Ok, Esto es lo primero que yo hago cuando uso Cloud. Cuando me despierto, yo… |
| `luis-caro-manuel-quijano-taller-claude_c0014` | 239–263 | 245–263 | 504 | 138 | 366 | `closest_after` | Entonces esto es lo que hago después en mi día y me hace un análisis y también es posible que me busque como las noticias más relevantes de… |
| `luis-caro-manuel-quijano-taller-claude_c0015` | 258–274 | 264–274 | 495 | 101 | 394 | `closest_before` | René, por favor. Yo soy René Roldán. Soy arquitecto de soluciones también en AWS. Yo soy especialista en la parte de datos. Tengo más de se… |
| `luis-caro-manuel-quijano-taller-claude_c0016` | 271–291 | 275–291 | 505 | 108 | 397 | `closest_after` | Cloud va a usar un agente por debajo que va a salir, se va a conectar con Expedia y me va a encontrar. Primero que nada, hoteles disponible… |
| `luis-caro-manuel-quijano-taller-claude_c0017` | 287–308 | 292–308 | 517 | 101 | 416 | `closest_after` | Todo lo que están viendo ustedes, la integración que yo tengo aquí de cloud en el navegador, es capaz de tomar control del navegador de man… |
| `luis-caro-manuel-quijano-taller-claude_c0018` | 305–325 | 309–325 | 493 | 105 | 388 | `closest_before` | Y finalmente, antes de que él haga el check, va a validar si este paquete está realmente disponible en mi casa. Entonces él sigue trabajand… |
| `luis-caro-manuel-quijano-taller-claude_c0019` | 322–336 | 326–336 | 513 | 116 | 397 | `closest_after` | Parece que no cuento con cobertura, desafortunadamente, pero bueno, no pasa nada, podemos intentar con otro paquete. Pero bueno, este es un… |
| `luis-caro-manuel-quijano-taller-claude_c0020` | 334–354 | 337–354 | 505 | 139 | 366 | `closest_after` | Nosotros cuando hemos desarrollado tal vez todas estas plataformas o estas páginas las hemos pensado directamente para que sea un humano el… |
| `luis-caro-manuel-quijano-taller-claude_c0021` | 350–369 | 355–369 | 496 | 110 | 386 | `closest_before` | Yo tengo que preparar un brief ejecutivo para este comité, pero no, realmente no tengo tiempo para leerme los cuatro documentos y llegar co… |
| `luis-caro-manuel-quijano-taller-claude_c0022` | 365–387 | 370–387 | 507 | 159 | 348 | `closest_after` | Entonces listo, he creado el proyecto, entonces ya tengo como mi proyecto dentro de cloud, ya les subí los cuatro documentos, ya puedo empe… |
| `luis-caro-manuel-quijano-taller-claude_c0023` | 383–401 | 388–401 | 517 | 108 | 409 | `tie_include` | Entonces, si seguimos un poco aquí, lo que me responde Cloud. También me da recomendaciones de lo que yo pueda llevar al comité. Entonces,… |
| `luis-caro-manuel-quijano-taller-claude_c0024` | 397–420 | 402–420 | 499 | 106 | 393 | `closest_before` | Que yo tengo que repetir esa tarea todos los lunes. Es una tarea esa tarea de yo prepararme ante el comité es algo que todos los lunes me t… |
| `luis-caro-manuel-quijano-taller-claude_c0025` | 414–438 | 421–438 | 502 | 101 | 401 | `closest_after` | Listo. Parece que hemos completado el primer comité, pero se acuerdan que mis pendientes. Mi segunda reunión del día era el Comité de finan… |
| `luis-caro-manuel-quijano-taller-claude_c0026` | 434–456 | 439–456 | 478 | 133 | 345 | `closest_before` | Quiero que me crees una nueva hoja que se llame el reporte ejecutivo y me hagas como un consolidado con KPIs, con gráficos de todas las hoj… |
| `luis-caro-manuel-quijano-taller-claude_c0027` | 451–470 | 457–470 | 510 | 110 | 400 | `closest_after` | Entonces, básicamente lo que hace Cloud es ayudarnos o asistirnos principalmente a ir construyendo la información a ya sé, ir construyendo… |
| `luis-caro-manuel-quijano-taller-claude_c0028` | 467–488 | 471–488 | 474 | 104 | 370 | `closest_before` | Y con nuestros datos, obviamente. Entonces lo que hace es principalmente poner estos semáforos que nos van a dar visibilidad. A nosotros ta… |
| `luis-caro-manuel-quijano-taller-claude_c0029` | 484–501 | 489–501 | 486 | 123 | 363 | `closest_before` | Y número tres, necesito generar imágenes para que yo las pueda poner en redes sociales, ponerlas en Instagram, ponerlas en Twitter, etcéter… |
| `luis-caro-manuel-quijano-taller-claude_c0030` | 497–517 | 502–517 | 484 | 135 | 349 | `closest_before` | Voy a decirle Cloth, me podrías hacer un análisis competitivo y investigar un poquito a mis competidores, sobre todo si yo estoy lanzando c… |
| `luis-caro-manuel-quijano-taller-claude_c0031` | 510–544 | 518–544 | 503 | 108 | 395 | `closest_after` | También va a buscar información sobre Mercado Pago. Ok, y finalmente sobre Story. Y lo que está haciendo aquí no es ningún secreto. Está ar… |
| `luis-caro-manuel-quijano-taller-claude_c0032` | 539–556 | 545–556 | 500 | 176 | 324 | `exact_target` | Entonces como el paso final, como vieron ya va tachando como el paso a paso y como paso final me va a generar este brief ejecutivo y de est… |
| `luis-caro-manuel-quijano-taller-claude_c0033` | 553–572 | 557–572 | 502 | 116 | 386 | `closest_after` | El arco narrativo tiene que tener la siguiente forma Tiene que tener un teaser, un lanzamiento, un refuerzo y una conversión. También estam… |
| `luis-caro-manuel-quijano-taller-claude_c0034` | 568–587 | 573–587 | 492 | 106 | 386 | `closest_before` | Y por último, vamos a tener el calendario editorial de 60 piezas que básicamente nos va a decir qué vamos a construir, qué día, cuándo lo p… |
| `luis-caro-manuel-quijano-taller-claude_c0035` | 583–606 | 588–606 | 533 | 115 | 418 | `closest_after` | A veces nos gusta ser como perezosos, pero si nos están ahorrando esta cantidad de tiempo, por favor tómense. Tómense más de cinco minutos… |
| `luis-caro-manuel-quijano-taller-claude_c0036` | 603–625 | 607–625 | 498 | 107 | 391 | `closest_before` | Para realmente ver el poder que les puede dar. Entonces nada más para recapitular aquí qué fue lo que hicimos? Instalamos el plugin de mark… |
| `luis-caro-manuel-quijano-taller-claude_c0037` | 621–646 | 626–646 | 489 | 106 | 383 | `closest_before` | Ellos dos los van a estar apoyando en las mesas. Entonces cualquier tipo de asistencia que requieran durante este ejercicio, por favor alce… |
| `luis-caro-manuel-quijano-taller-claude_c0038` | 641–662 | 647–662 | 523 | 115 | 408 | `closest_after` | Ustedes no se preocupen, todos los documentos se los vamos a dar nosotros. Ustedes no tienen que meter sus propios documentos. Entonces el… |
| `luis-caro-manuel-quijano-taller-claude_c0039` | 661–684 | 663–684 | 521 | 106 | 415 | `closest_after` | Ok, solo vamos a usar un documento para lo que es este primer laboratorio, entonces ubíquense ahí un poquito, vean los documentos y aquí le… |
| `luis-caro-manuel-quijano-taller-claude_c0040` | 682–702 | 685–702 | 514 | 124 | 390 | `closest_after` | Lo que vamos a hacer a continuación es que vamos a usar Clot Chat para que me ayude de nuevo para prepararme para el comité. Ok, entonces,… |
| `luis-caro-manuel-quijano-taller-claude_c0041` | 699–718 | 703–718 | 494 | 105 | 389 | `closest_before` | Y finalmente, aunque no se preocupen por esto, también tenemos Clock Code, que está más enfocado a lo que es el desarrollo de software. Par… |
| `luis-caro-manuel-quijano-taller-claude_c0042` | 713–738 | 719–738 | 503 | 130 | 373 | `closest_after` | Si ustedes ponen Cloud chat en lo que es Opus 4.7, probablemente se van a quemar sus tokens súper rápido y no van a. No lo va a ameritar po… |
| `luis-caro-manuel-quijano-taller-claude_c0043` | 734–755 | 739–755 | 508 | 111 | 397 | `closest_after` | Este es como el el overview general de cómo está la interfaz gráfica de Cloud. Les voy a dar aquí unos unos segundos menos de un minuto tam… |
| `luis-caro-manuel-quijano-taller-claude_c0044` | 752–778 | 756–778 | 511 | 134 | 377 | `closest_after` | Yo dije soy el director de producto de Banco Azteca como parte de Grupo Salinas y mi principal sector son jóvenes de 18 a 25 años que están… |
| `luis-caro-manuel-quijano-taller-claude_c0045` | 773–800 | 779–800 | 489 | 101 | 388 | `closest_before` | En qué te atoraste? Qué necesitas? Podría ser que esté esperando también un input de ustedes para continuar con el análisis. Si aquí le dam… |
| `luis-caro-manuel-quijano-taller-claude_c0046` | 795–818 | 801–818 | 522 | 105 | 417 | `closest_after` | Si te regresas un poquito René, le vamos a dar clic al símbolo de más. Se acuerdan que les había dicho que ahí podemos cambiar el modo en q… |
| `luis-caro-manuel-quijano-taller-claude_c0047` | 815–839 | 819–839 | 514 | 110 | 404 | `closest_after` | Por favor desactiven el modo explicativo que fue el que activamos en el paso anterior. Entonces vamos a quitar el modo explicativo y vamos… |
| `luis-caro-manuel-quijano-taller-claude_c0048` | 834–856 | 840–856 | 501 | 113 | 388 | `closest_after` | Cloud lo va a tratar de resolver de la mejor forma y pueden siempre analizar cómo está razonando, cómo está tratando de resolver este probl… |
| `luis-caro-manuel-quijano-taller-claude_c0049` | 853–876 | 857–876 | 507 | 102 | 405 | `closest_after` | Lo vamos a ver ahí. Se llama Lab uno Cloud Chat y este documento se llama Dashboard Experiencia de Cliente Q4 2025. Vale, vamos a subirselo… |
| `luis-caro-manuel-quijano-taller-claude_c0050` | 871–894 | 877–894 | 475 | 101 | 374 | `closest_before` | Ahora es su turno en esa misma carpeta que ustedes descargaron hay del laboratorio uno, hay una carpeta que se llama Materiales. Si no las… |
| `luis-caro-manuel-quijano-taller-claude_c0051` | 891–912 | 895–912 | 509 | 120 | 389 | `closest_after` | Si fuera un análisis muy complicado, entonces ahí hace mucho sentido que cambiemos, utilicemos un modelo mucho más poderoso mientras ustede… |
| `luis-caro-manuel-quijano-taller-claude_c0052` | 907–925 | 913–925 | 489 | 134 | 355 | `closest_before` | Pueden traer los colores que ustedes necesiten y pueden decirle que construya basado en lo que necesiten o en o en los estilos, colores e m… |
| `luis-caro-manuel-quijano-taller-claude_c0053` | 923–949 | 926–949 | 499 | 124 | 375 | `closest_before` | A mí me encanta escribir blogs y básicamente lo que le dije a Cloud es que me generara una página web con esta foto y me escribiera este bl… |
| `luis-caro-manuel-quijano-taller-claude_c0054` | 945–956 | 950–956 | 231 | 120 | 111 | `end_of_talk` | Todo esto lo hizo como en el fondo, entendiendo un poquito la audiencia, escribiendo. Ojo, esto no, esto no está real, no lo voy a publicar… |
