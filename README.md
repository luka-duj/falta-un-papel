# Falta un papel

¿Tienes que hacer un trámite en tu ayuntamiento y no sabes qué impreso usar ni qué adjuntar? **Falta un papel** es un complemento gratuito y de código abierto para personas que preparan solicitudes municipales en España. Encuentra el trámite oficial y te entrega un borrador del PDF o las respuestas listas para copiar en la sede electrónica.

![Una lupa sobre la sede electrónica, un formulario preparado y una persona que lo revisa](assets/flujo.png)

1. **Encuentra el trámite.** Dile al agente qué quieres pedir y en qué municipio. Abre la ficha oficial y comprueba qué impreso y anexos corresponden.
2. **Prepara tu solicitud.** Reutiliza lo que ya has confirmado en un entorno habilitado. Si quedan datos imprescindibles, te los pide juntos y deja sus campos en blanco en el borrador.
3. **Revisa y presenta.** Recibe el borrador o las respuestas para el formulario web, lo que te falta y el enlace de presentación. Tú revisas, firmas y presentas en la sede oficial.

## Empieza sin terminal

### Codex en la aplicación de escritorio de ChatGPT

1. [Descarga el ZIP](https://github.com/luka-duj/falta-un-papel/archive/refs/heads/main.zip) y descomprímelo. En la app de ChatGPT, cambia a **Codex** y abre la carpeta descomprimida como un proyecto local. Selecciona la carpeta que contiene el `README`.
2. Abre **Plugins**, elige el catálogo **falta-un-papel-alpha** y pulsa **Instalar** en **Falta un papel**. Si el catálogo aún no aparece, reinicia la app con el proyecto abierto. [Cómo descubre Codex los catálogos del proyecto](https://developers.openai.com/plugins/build/plugins#build-your-own-curated-plugin-list)
3. Abre un chat nuevo en Codex y pega el [mensaje de prueba](#prueba-con-un-ejemplo). Si quieres seleccionar el complemento directamente, escribe `@` y elige **Falta un papel**.

### Claude en la web o en la aplicación de escritorio

1. Abre **Customize → Plugins → Add → Add marketplace**. Elige **Add from a repository** y pega `https://github.com/luka-duj/falta-un-papel`.
2. Abre **falta-un-papel** en el catálogo y pulsa **Install** o **Add**. Inicia un chat nuevo y pega el [mensaje de prueba](#prueba-con-un-ejemplo). Si usas la pestaña **Code** con la misma cuenta, abre una sesión nueva y selecciona la habilidad con `/falta-un-papel:falta-un-papel`. [Instalar en Claude](https://support.claude.com/en/articles/13837440-use-plugins-in-claude) · [Usar los plugins de tu cuenta en Claude Code](https://code.claude.com/docs/en/plugins/install#plugins-from-your-claude-ai-account)

### Pídeselo al agente

En un chat local de **Codex** o **Claude Code**, puedes pedirle que haga la instalación por ti.

> Instala el complemento Falta un papel desde https://github.com/luka-duj/falta-un-papel siguiendo el README para este cliente. Usa el instalador de plugins y dime si tengo que confirmar algo en la app. Después, dime si puedes generar un PDF y qué falta si no puedes.

Si el agente necesita tu permiso o tu cliente gestiona los plugins desde un menú, te indicará dónde continuar. Después de instalarlo, abre un chat nuevo.

## Prueba con un ejemplo

> Usa Falta un papel para preparar una instancia general y preguntar por la disponibilidad de una sala municipal en Valdemoro. Usa datos ficticios y marca el borrador como ejemplo.

El ejemplo parte del impreso enlazado en la [ficha oficial de Valdemoro](https://www.valdemoro.es/sede-electronica/tramites/instancia-general). La instancia general se usa cuando el Ayuntamiento carece de un formulario específico para lo que se solicita.

## Instala desde la terminal

**Codex CLI**

```sh
codex plugin marketplace add luka-duj/falta-un-papel
codex plugin add falta-un-papel@falta-un-papel-alpha
```

**Claude Code CLI**

```sh
claude plugin marketplace add luka-duj/falta-un-papel
claude plugin install falta-un-papel@falta-un-papel-alpha
```

Abre una sesión nueva y pega el [mensaje de prueba](#prueba-con-un-ejemplo). En **Mistral Vibe**, coloca la carpeta completa en `~/.vibe/plugins/falta-un-papel/`, comprueba `/plugins` y usa `/falta-un-papel:falta-un-papel`. Otros clientes pueden usar [la habilidad](skills/falta-un-papel/SKILL.md) junto con sus carpetas `references/` y `scripts/`. [Codex CLI](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli) · [Claude Code CLI](https://code.claude.com/docs/en/plugins/install#install-from-your-shell) · [Mistral Vibe](https://docs.mistral.ai/vibe/code/cli/plugins)

## Si quieres recibir un PDF

Pide al agente que compruebe si el entorno de la sesión puede ejecutar **Python 3.11 o posterior** y devolver archivos. Si faltan las dependencias, puedes pedirle que las instale desde `skills/falta-un-papel/scripts/requirements.txt`. Si prefieres hacerlo tú, ejecuta esto desde la carpeta descomprimida, con el mismo Python que usará el agente.

```sh
python -m pip install -r skills/falta-un-papel/scripts/requirements.txt
```

Si tu sesión no puede usar el editor, puedes pedir igualmente el enlace oficial y las respuestas listas para copiar. Un trámite web tampoco necesita el editor.

## Estado de la alfa

El editor local está probado con impresos oficiales editables y con un impreso plano de prueba que tiene un mapa para esa versión. La búsqueda también puede localizar trámites de municipios sin un perfil previo. Si el cliente carece de ejecución o de entrega de archivos, como ocurre en algunos móviles, la habilidad entrega el enlace y las respuestas en texto. Los tres paquetes de instalación están incluidos. La validación de extremo a extremo en cada cliente sigue abierta. [Pruebas y criterios de verificación](tests/verification.md)

Antes de introducir datos personales, consulta [cómo se manejan los datos](PRIVACIDAD.md). El [editor local](skills/falta-un-papel/references/editor-pdf.md) también admite entrada privada desde tu propio terminal.

## Cuéntanos qué mejorar

¿Encontró el modelo correcto? ¿Te pidió algo que ya habías dicho? ¿Pudiste usar el borrador? Cuéntanos qué ocurrió con el municipio, el enlace oficial, el cliente que usas y un caso ficticio. [Comunicar un error o proponer una mejora](https://github.com/luka-duj/falta-un-papel/issues/new/choose) · [Contribuir al proyecto](CONTRIBUTING.md) · [Comunicar un problema de seguridad](SECURITY.md)

[Licencia MIT](LICENSE) · [Atribuciones](AVISOS.md)
