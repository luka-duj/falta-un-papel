---
name: falta-un-papel
description: Encuentra, prepara, rellena o corrige una solicitud municipal española. Úsala si la persona necesita el trámite, un PDF nuevo o actualizado, o respuestas para la sede, incluso si también pide revisar el borrador antes de corregirlo. Para comprobar un borrador existente y explicar qué falta, usa revisar-solicitud.
license: MIT
---

# Falta un papel

Elige el flujo por el resultado pedido. Si la persona quiere comprobar una solicitud existente y saber qué falta, pasa a [Revisar mi solicitud](../revisar-solicitud/SKILL.md) antes de preparar documentos. Si pide un borrador nuevo, corregir uno existente o «revisa y corrige el PDF», lleva todo el encargo desde esta habilidad e integra la comprobación necesaria en la preparación. Usa el municipio y el trámite ya disponibles en el contexto. Una consulta sobre requisitos de un trámite sin borrador también se atiende aquí.

Una petición de preparación o de edición autoriza una copia de trabajo en el espacio permitido. Para la búsqueda y el uso de datos, sigue la [guía común de fuentes y privacidad](references/fuentes-y-datos.md). Usa [la ficha de Valdemoro](references/profiles/valdemoro-instancia-general.json) solo para esa variante.

## Elige la vía y avanza

1. **Resuelve lo que cambia el modelo.** Usa lo que ya sabes de esta solicitud. Si una respuesta determina si corresponde una instancia general, un trámite específico o una variante, pregúntala al empezar. Por ejemplo, ante «una solicitud para la escuela municipal», pregunta qué quiere que haga la escuela. Para un vado, si falta, agrupa el tipo de inmueble y si el acceso existe o requiere obra. Usa la pregunta estructurada del cliente cuando esté disponible o una pregunta breve en el chat. Entrega lo común que ya esté verificado.
2. **Abre la ficha exacta.** Usa la ruta corta de la guía común. Si solo te piden información, entrega lo confirmado y el enlace oficial. Si te piden preparar un borrador, cierra la búsqueda cuando tengas lo necesario para avanzar.

## Prepara y entrega

3. **Reutiliza valores confirmados del caso.** Usa el contexto autorizado para esta solicitud solo cuando su aplicación y vigencia estén claras. Conserva las correcciones del usuario. Agrupa únicamente los campos obligatorios que faltan. Si la persona no sabe un dato, indica dónde verlo. Por ejemplo, si se requiere la referencia catastral, enlaza la [guía de Catastro](https://www.catastro.hacienda.gob.es/es-ES/referencia_catastral.html) para encontrarla en el IBI u otra fuente oficial.
4. **Crea el borrador en este turno.** Si hay PDF, descarga el oficial en blanco. Para una corrección, contrasta primero el borrador disponible con el impreso vigente y reutiliza los valores confirmados cuando el entorno lo permita. Guarda las correcciones en una copia nueva. Con permiso para ejecutar y devolver archivos, usa [el editor local](references/editor-pdf.md). Rellena los campos claros aunque falten otros datos. Ante una respuesta nueva, conserva los valores confirmados, actualiza solo lo afectado y ofrece la nueva copia. Si el cliente carece de acceso a fuentes, ejecución o entrega de archivos, pide solo el enlace o el PDF que desbloquee el caso, o entrega el enlace oficial y las respuestas en el orden de los campos comprobados. En una sede web, indica el punto de entrada oficial y los anexos. Si todavía falta identificarse, deja pendientes las etiquetas que el usuario aún no puede ver.
5. **Abre con el resultado.** Muestra primero **Descargar borrador** o el enlace al impreso con las respuestas listas para copiar. Sigue con **Qué falta** y **Dónde presentar**. Distingue los campos pendientes de los documentos que la persona tiene que reunir. La persona controla identificación, carga de archivos, pago, firma y presentación. Las muestras ficticias se marcan como ejemplos.
