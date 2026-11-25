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

## Revisión del paquete externo

El [auditor](check_release.py) compara el árbol con la lista de archivos prevista. Acepta solo las dos imágenes PNG revisadas y sin metadatos. Detecta enlaces simbólicos, rutas locales y patrones de secretos. Para la revisión final, pasa con `--deny-file` un archivo privado, fuera del repositorio, con una línea por término o identificador que deba quedar fuera. La salida señala los archivos afectados sin mostrar las coincidencias. Revisa visualmente las imágenes, las atribuciones y los nombres de los ejemplos.

Con `--archive RUTA` el auditor crea un ZIP a partir de los archivos ya comprobados, con rutas relativas y metadatos fijos. Usa un destino fuera del árbol del paquete. Guarda los resultados de las pruebas y los PDF descargados o generados fuera del árbol.

En GitHub, revisa que `main` coincida con el árbol auditado y que el nombre y correo del commit sean los que quieres publicar. Comprueba el selector de incidencias y, al abrir el repositorio al público, habilita el canal privado de vulnerabilidades desde **Settings → Advanced Security**. Verifica el enlace de reporte desde una cuenta sin permisos de mantenimiento.
