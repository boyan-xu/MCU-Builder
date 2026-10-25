[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md)

# Build with AI MCU

**Convierte tu idea en algo que puedas usar.**

Build with AI MCU es una habilidad para asistentes de IA dirigida a personas que empiezan con los microcontroladores. No necesitas aprender programación ni electrónica antes de comenzar. Solo explica qué quieres crear y cómo te gustaría que funcionara.

La IA te ayuda a definir la idea y a encontrar una forma práctica de realizarla, aprovechando el hardware, las herramientas y los conocimientos que ya tienes. Te ayuda con la lista de materiales, enlaces de compra opcionales, diagramas de conexión claros, código, carga del programa y depuración, para que puedas centrarte en lo que quieres conseguir.

No hay un curso fijo que todo el mundo deba seguir. Puedes empezar con una función sencilla o avanzar hacia un objetivo mayor. El proceso se adapta a tu situación y el resultado es un proyecto que responde a tus necesidades, con los archivos y las instrucciones para seguir usándolo y modificándolo.

## Cómo funciona

- **Tu idea es lo primero.** Habla de lo que quieres crear, dónde lo usarás y qué resultado esperas. La memoria disponible ayuda, pero tus necesidades actuales tienen prioridad. No hace falta empezar con un cuestionario de presupuesto ni un curso de teoría.
- **Aprovecha lo que tienes.** La IA revisa las placas, piezas y programas existentes antes de proponer compras o descargas. No sustituye una placa adecuada solo porque otra sea más cómoda.
- **Comprueba qué falta.** Un panel permite marcar materiales y consultar especificaciones, cantidades, uso y coste adicional estimado. Puedes pedir enlaces para tu país o región y elegir productos equivalentes de otras tiendas.
- **Conecta con una imagen clara.** Recibe un diagrama etiquetado y pasos de conexión que coinciden con él. La IA verifica los modelos, explica lo esencial y decide si conviene conectar o cargar el programa primero.
- **Deja el código y la depuración a la IA.** Tú describes el resultado y colaboras con los pasos físicos. La IA usa las herramientas disponibles y conserva el permiso de carga para el mismo dispositivo, indicando qué se ha probado y qué no.
- **Conserva tu propio proyecto.** Recibe el código fuente, las conexiones y una guía breve. Tú decides si el proyecto será privado o de código abierto.

## Instalación

Descarga el repositorio con **Code → Download ZIP** en GitHub, o ejecuta:

```sh
git clone https://github.com/boyan-xu/build-with-ai-mcu.git
```

Copia toda la carpeta `skills/build-with-ai-mcu` al directorio de habilidades de tu herramienta de IA. En Codex, usa `$CODEX_HOME/skills` si está definido; de lo contrario, `~/.codex/skills`. Revisa cualquier habilidad del mismo nombre antes de sustituirla. Actualiza la detección de habilidades o abre otra sesión si hace falta.

Los tres idiomas comparten unas únicas [instrucciones](../skills/build-with-ai-mcu/SKILL.md). La conversación, el panel y las indicaciones del proyecto siguen el idioma elegido. Otras herramientas deben admitir este formato o permitir cargar las instrucciones; las capacidades varían según la plataforma.

## Empieza con tu idea

```text
Usa $build-with-ai-mcu. Quiero un aviso cuando deje una puerta abierta.
Ya tengo un ESP32 y Arduino IDE, pero nunca he usado un microcontrolador.
Ayúdame a definir cómo debe funcionar y encárgate del código.
```

Si no tienes una idea, pide cinco proyectos adecuados. Si ya tienes materiales o un proyecto a medias, empieza desde ahí. Un objetivo difícil puede dividirse en pasos relacionados sin perder la idea original.

## Panel y ejemplo de conexiones

- [Panel reutilizable](../skills/build-with-ai-mcu/assets/parts-checklist.html): la IA lo prepara con tus materiales. Puede mostrarse en un chat compatible o abrirse como un archivo HTML independiente. Guarda el progreso cuando la plataforma o el navegador lo permiten; los cambios de cantidad o especificación requieren otra revisión.
- [Notas de integración](../skills/build-with-ai-mcu/references/checklist.md): el botón envía una solicitud a la IA cuando la plataforma lo permite; si no, muestra un texto para copiar. La página independiente no contacta en secreto con una IA ni con tiendas.
- [Ejemplo de conexión de baja tensión](../skills/build-with-ai-mcu/references/uno-led/README.md): imagen revisada, tabla de conexiones y asignación de pines coherente. Muestra el nivel de entrega, no un primer proyecto obligatorio.

## Herramientas y límites

Es una habilidad para principiantes, no un curso avanzado ni un servicio de programación de dispositivos. La IA necesita acceso real a las herramientas para compilar, depurar o conectar con tu placa. La carga desde el navegador requiere hardware compatible, firmware y acceso local; no se garantiza funcionar siempre sin instalaciones.

Las descargas necesarias se explican antes. Se protegen tu trabajo y tus credenciales. Compilar o cargar correctamente no demuestra que el dispositivo funcione físicamente. Se comprueban hardware y permisos, sin pedir una y otra vez autorización para la misma operación. La memoria personal y los registros privados no se publican con el proyecto.

## Comprobar el código fuente

Ejecuta `node --test tests/*.test.mjs` para comprobar la lógica del panel y la coherencia del ejemplo. El formato de la habilidad puede revisarse con el [validador oficial de skill-creator](https://github.com/openai/skills/tree/main/skills/.system/skill-creator). Las simulaciones y pruebas de software no sustituyen las pruebas físicas.

## Licencia

[MIT](../LICENSE). Puedes usar, compartir y modificar esta habilidad. Cada persona decide la publicación y la licencia de su propio proyecto.
