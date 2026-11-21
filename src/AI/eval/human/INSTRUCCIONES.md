# Validación humana del juez: instrucciones

Abre `hoja_calificacion.csv` (Excel o Numbers). Son 30 respuestas del conjunto
de prueba, mezcladas: no dice qué sistema produjo cada una, y así debe ser.
Tiempo estimado: ~1 hora.

Para cada fila, lee la **consulta**, el **artículo oficial** (la respuesta
correcta está ahí) y la **respuesta**. Luego llena tres columnas con un entero
del 1 al 5, usando exactamente la misma rúbrica que el juez:

- **fidelidad:** 5 = todo lo que afirma coincide con el artículo oficial;
  1 = contiene datos inventados o contradictorios (montos, plazos, requisitos).
  Una negativa honesta sin datos falsos ("no encontré esa información") recibe 3.
- **relevancia:** 5 = responde directamente lo que se preguntó; 1 = no responde
  la consulta.
- **claridad:** 5 = muy clara para un ciudadano sin formación jurídica;
  1 = confusa.

Reglas: califica cada fila por separado, sin volver a cambiar las anteriores.
No abras `clave.json` hasta terminar.

Al terminar, guarda el CSV con el mismo nombre y corre:

    cd Prototipo/AI && .venv/bin/python -m eval.human_eval score

Eso calcula la concordancia con el juez (kappa ponderada, Spearman y acuerdo
exacto o a ±1 punto) en `results/exp/human_agreement.json`.
