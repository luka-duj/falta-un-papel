# Verificar y publicar

Ejecuta las pruebas desde la raíz con el mismo Python que usa el editor.

```sh
python -B -m unittest discover -s tests -v
python -B tests/check_release.py
```

## Ensayos con datos ficticios

| Caso | Resultado que se comprueba |
| --- | --- |
| Valdemoro, instancia general por cuenta propia | Empieza por la ficha exacta. Usa el PDF enlazado por el Ayuntamiento. Rellena ambos ejemplares con los mismos valores, marca el ejemplo y devuelve el archivo. |
| Municipio sin perfil | Usa una búsqueda concreta. Verifica el dominio, abre la ficha y el impreso, y rellena los campos inequívocos de un AcroForm desconocido. |
| Condición pendiente | Haz una sola pregunta concreta al inicio cuando cambie la variante. Entrega ese turno un borrador parcial cuando sea posible. Cuando llegue la respuesta, conserva los demás valores. |
| Revisión cambiada o PDF plano | Invalida el mapa anterior al cambiar el SHA-256. Comprueba la salida plana con una ficha revisada y la entrega en texto si falta esa ficha. |
| Trámite web o móvil sin ejecución | Entrega el enlace oficial, respuestas ordenadas y anexos. Deja pendientes los campos tras identificación. |

Empieza desde una instalación nueva en cada cliente antes de afirmar compatibilidad. Registra cliente, modelo, herramienta de acceso público, tiempo al primer PDF útil o a la primera entrega que permite avanzar, preguntas y resultado. Haz tres repeticiones por cliente para el caso conocido y el municipio nuevo. Usa objetivos de mediana de 30 y 60 segundos, respectivamente. Excluye la espera de la respuesta del solicitante e incluye las consultas y renderizados.

## Selección de habilidad

En chats nuevos, pega cada petición sin mencionar ninguna habilidad. Usa datos ficticios y el impreso público de un trámite verificable. Si el cliente muestra la habilidad cargada, registra cuál se usó y comprueba que se ejecutó un solo flujo. Repite la comprobación con un borrador de PDF adjunto y con una lista de respuestas sin archivo.

| Petición | Flujo y resultado esperados |
| --- | --- |
| «Quiero preparar una instancia general en Valdemoro para preguntar por una sala municipal» | `falta-un-papel`. Prepara un borrador cuando sea posible. |
| «¿Qué documentos pide el Ayuntamiento para esta instancia? Todavía no tengo un borrador» | `falta-un-papel`. Explica los requisitos verificados. |
| «Te paso mi borrador. ¿Qué me falta antes de presentarlo?» | `revisar-solicitud`. Devuelve correcciones sin generar un PDF nuevo. |
| «Estas son las respuestas que ya he escrito para la sede. ¿Qué debería corregir?» | `revisar-solicitud`. Contrasta las respuestas existentes con la ficha oficial. |
| «Revisa el borrador y devuélveme una copia corregida» | `falta-un-papel`. Integra la comprobación antes de crear una copia. |
| Después de una revisión, «Corrige ese campo y devuélveme el PDF» | `falta-un-papel` en el nuevo turno. Aprovecha los datos confirmados y preserva el original. |

## Revisión del paquete externo

El [auditor](check_release.py) compara el árbol con la lista de archivos prevista. Acepta solo las dos imágenes PNG revisadas y sin metadatos. Detecta enlaces simbólicos, rutas locales y patrones de secretos. Para la revisión final, pasa con `--deny-file` un archivo privado, fuera del repositorio, con una línea por término o identificador que deba quedar fuera. La salida señala los archivos afectados sin mostrar las coincidencias. Revisa visualmente las imágenes, las atribuciones y los nombres de los ejemplos.

Con `--archive RUTA` el auditor crea un ZIP a partir de los archivos ya comprobados, con rutas relativas y metadatos fijos. Usa un destino fuera del árbol del paquete. Guarda los resultados de las pruebas y los PDF descargados o generados fuera del árbol.

En GitHub, comprueba que `main` coincide con el árbol auditado y que el nombre y el correo de autoría de los cambios sean los que quieres publicar. Comprueba el selector de incidencias y, al abrir el repositorio al público, habilita el canal privado de vulnerabilidades desde **Settings → Advanced Security**. Comprueba que una cuenta sin permisos de mantenimiento puede abrir el formulario privado.
