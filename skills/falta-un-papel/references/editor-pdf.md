# Editor local de PDF

El [editor](../scripts/pdf_form.py) trabaja con una copia del impreso público en blanco. Usa Python 3.11 o posterior y las [dependencias](../scripts/requirements.txt). Si el cliente puede ejecutar Python pero falta una dependencia, usa un entorno ya habilitado o conserva la entrega en texto en ese turno.

```sh
python -B skills/falta-un-papel/scripts/pdf_form.py inspect "original.pdf"
python -B skills/falta-un-papel/scripts/pdf_form.py fill "original.pdf" "borrador.pdf"
```

`inspect` devuelve el SHA-256 como `fingerprint`, el formato y los campos. Cada campo tiene `id`, etiqueta, origen de la etiqueta, tipo, opciones y posiciones. Los números de página empiezan en 1 y las coordenadas PDF se expresan desde la esquina inferior izquierda. Si `label_source` es `id`, el nombre puede ser técnico. Confirma el significado con su posición en la página, el texto visible o las instrucciones oficiales antes de asociar un valor. Si hay nombres de campo repetidos en secciones distintas, conserva el identificador completo y la sección.

`fill` lee un objeto por la entrada estándar. Pon en `values` solo los valores confirmados y, en `required`, los identificadores de los campos obligatorios para ese trámite que el editor ha podido localizar.

```json
{
  "fingerprint": "<fingerprint devuelto por inspect>",
  "values": {"Texto4": "Solicito información sobre la reserva de una sala municipal."},
  "required": ["Nombre", "apellido", "Texto4"]
}
```

El editor devuelve `draft`, `filled`, `missing` y `unresolved`. Si el SHA-256 cambia, vuelve a inspeccionar el impreso y comprueba sus identificadores de nuevo. El editor conserva las páginas y comprueba los valores y su aspecto en cada campo. Deja pendientes los campos que sobresalen de la página o que no puede comprobar. Revisa el aspecto del borrador si el cliente permite previsualizarlo. Los impresos planos requieren una ficha local revisada con `kind: "flat"`, SHA-256 y campos con `label`, `kind` (`text` o `checkbox`), `page` y `rect`. Reserva la firma, el registro y los campos de la Administración.

Para pruebas con identidades inventadas, añade `--sample`. Para datos privados, usa una entrada estándar que el cliente pueda pasar sin incluir valores en argumentos, el historial o archivos auxiliares. La persona también puede ejecutar `fill ... --private` en su propio terminal y elegir una carpeta privada para el borrador. Para limitar la pregunta, añade `--field ID` una vez por campo pendiente. Usa un impreso oficial sin archivos incorporados. Para un PDF con adjuntos, cifrado, firmado, dependiente de XFA o plano sin ficha, entrega el enlace al impreso y las respuestas que puedas preparar.

## Revisar un borrador

```sh
python -B skills/falta-un-papel/scripts/pdf_form.py review "oficial-en-blanco.pdf" "borrador.pdf"
```

Ejecuta el comando desde la carpeta del complemento. Usa como primer archivo el PDF vigente enlazado en la ficha oficial. En tu propio terminal puedes comprobar un borrador privado y compartir solo el resumen si quieres. El comando lee ambos archivos y devuelve las etiquetas del impreso público. Cada campo figura como `present`, `empty`, `appearance_unverified` o `unmatched`. Los valores del borrador quedan en tu equipo. Una coincidencia de campos indica que se han podido comparar sus posiciones y tipos. Sigue siendo necesario comprobar la versión del impreso, las condiciones, los anexos y la validez de las respuestas. Si el borrador es plano, escaneado o está firmado, usa las etiquetas visibles y la ficha oficial para revisarlo.
