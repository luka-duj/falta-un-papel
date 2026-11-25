# Editor local de PDF

El [editor](../scripts/pdf_form.py) trabaja con una copia del impreso público en blanco. Usa Python 3.11 o posterior y las [dependencias](../scripts/requirements.txt). Si el cliente puede ejecutar Python pero falta una dependencia, usa un entorno ya habilitado o conserva la entrega en texto en ese turno.

```sh
python -B skills/falta-un-papel/scripts/pdf_form.py inspect "original.pdf"
python -B skills/falta-un-papel/scripts/pdf_form.py fill "original.pdf" "borrador.pdf"
```

`inspect` devuelve el SHA-256 como `fingerprint`, el formato y los campos. Cada campo tiene `id`, etiqueta, origen de la etiqueta, tipo, opciones y posiciones. Los números de página empiezan en 1 y las coordenadas PDF se expresan desde la esquina inferior izquierda. Si `label_source` es `id`, el nombre puede ser técnico. Confirma el significado con su posición en la página, el texto visible o las instrucciones oficiales antes de asociar un valor. Si hay nombres de campo repetidos en secciones distintas, conserva el identificador completo y la sección.

`fill` lee un objeto por la entrada estándar. Pon en `values` solo los valores confirmados y, en `required`, los IDs que la fuente establece como obligatorios para la variante y que el editor ha podido identificar.

```json
{
  "fingerprint": "<fingerprint devuelto por inspect>",
  "values": {"Texto4": "Solicito información sobre la reserva de una sala municipal."},
  "required": ["Nombre", "apellido", "Texto4"]
}
```

El editor devuelve `draft`, `filled`, `missing` y `unresolved`. Si el SHA-256 cambia, vuelve a inspeccionar. Nunca copies un ID de una revisión anterior. El editor conserva las páginas y verifica valores, apariencias y cambios visibles por campo. Revisa el aspecto del borrador si el cliente permite previsualizarlo. Ante campos dudosos, conserva el subconjunto verificado y explica qué falta. Los impresos planos requieren una ficha local revisada con `kind: "flat"`, SHA-256 y campos con `label`, `kind` (`text` o `checkbox`), `page` y `rect`. Reserva la firma, el registro y los campos de la Administración.

Para pruebas con identidades inventadas, añade `--sample`. Para datos privados, usa una entrada estándar que el cliente pueda pasar sin incluir valores en argumentos, el historial o archivos auxiliares. La persona también puede ejecutar `fill ... --private` en su propio terminal y elegir una carpeta privada para el borrador. Para limitar la pregunta, añade `--field ID` una vez por campo pendiente. Para un PDF cifrado, firmado, dependiente de XFA o plano sin ficha, entrega el enlace al impreso y las respuestas que puedas preparar.
