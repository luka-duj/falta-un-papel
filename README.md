# Falta un papel

¿Tienes que hacer un trámite en tu ayuntamiento y no sabes qué impreso usar ni qué adjuntar? **Falta un papel** es un complemento gratuito y de código abierto para personas que preparan solicitudes municipales en España. Encuentra el trámite oficial y te entrega un borrador del PDF o las respuestas listas para copiar en la sede electrónica.

![Una lupa sobre la sede electrónica, un formulario preparado y una persona que lo revisa](assets/flujo.png)

1. **Encuentra el trámite.** Dile al agente qué quieres pedir y en qué municipio. Abre la ficha oficial y comprueba qué impreso y anexos corresponden.
2. **Prepara tu solicitud.** Reutiliza lo que ya has confirmado en un entorno habilitado. Si quedan datos imprescindibles, te los pide juntos y deja sus campos en blanco en el borrador.
3. **Revisa y presenta.** Recibe el borrador o las respuestas para el formulario web, lo que te falta y el enlace de presentación. Tú revisas, firmas y presentas en la sede oficial.

## Prueba con un ejemplo

> Prepara una instancia general para preguntar por la disponibilidad de una sala municipal en Valdemoro. Usa datos ficticios y marca el borrador como ejemplo.

El ejemplo parte del impreso enlazado en la [ficha oficial de Valdemoro](https://www.valdemoro.es/sede-electronica/tramites/instancia-general). La instancia general se usa cuando el Ayuntamiento carece de un formulario específico para lo que se solicita.

## Instalar

Descarga el código de este repositorio y abre su carpeta en una terminal. Para generar PDF necesitas **Python 3.11 o posterior** y estas dependencias en el entorno que usará el agente. Si solo necesitas el enlace y las respuestas, puedes usar la habilidad sin instalar el editor.

```sh
python -m pip install -r skills/falta-un-papel/scripts/requirements.txt
```

| Cliente | Instalación |
| --- | --- |
| Codex | Ejecuta `codex plugin marketplace add .` y `codex plugin add falta-un-papel@falta-un-papel-alpha`. Abre una sesión nueva, selecciona **Falta un papel** y prueba el mensaje de arriba. |
| Claude Code | Ejecuta `claude --plugin-dir .` y abre `/falta-un-papel:falta-un-papel`. |
| Mistral Vibe | Coloca la carpeta completa en `~/.vibe/plugins/falta-un-papel/`. Abre una sesión, comprueba `/plugins` y usa `/falta-un-papel:falta-un-papel`. |
| Otro cliente compatible | Instala [la habilidad](skills/falta-un-papel/SKILL.md) con sus carpetas `references/` y `scripts/`. |

[Codex](https://developers.openai.com/plugins/build/plugins) · [Claude Code](https://code.claude.com/docs/en/plugins/overview) · [Mistral Vibe](https://docs.mistral.ai/vibe/code/cli/plugins)

## Estado de la alfa

El editor local está probado con impresos oficiales editables y con un impreso plano de prueba que tiene un mapa para esa versión. La búsqueda también puede localizar trámites de municipios sin un perfil previo. Si el cliente carece de ejecución o de entrega de archivos, como ocurre en algunos móviles, la habilidad entrega el enlace y las respuestas en texto. Los tres paquetes de instalación están incluidos. La validación de extremo a extremo en cada cliente sigue abierta. [Pruebas y criterios de verificación](tests/verification.md)

Antes de introducir datos personales, consulta [cómo se manejan los datos](PRIVACIDAD.md). El [editor local](skills/falta-un-papel/references/editor-pdf.md) también admite entrada privada desde tu propio terminal.

## Cuéntanos qué mejorar

¿Encontró el modelo correcto? ¿Te pidió algo que ya habías dicho? ¿Pudiste usar el borrador? Cuéntanos qué ocurrió con el municipio, el enlace oficial, el cliente que usas y un caso ficticio. [Comunicar un error o proponer una mejora](https://github.com/luka-duj/falta-un-papel/issues/new/choose) · [Contribuir al proyecto](CONTRIBUTING.md) · [Comunicar un problema de seguridad](SECURITY.md)

[Licencia MIT](LICENSE) · [Atribuciones](AVISOS.md)
