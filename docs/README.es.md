[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md)

# Build with AI MCU

**Convierte tu idea en algo que puedas usar.**

Build with AI MCU ofrece dos habilidades para asistentes de IA: una para tu primer proyecto con microcontroladores y otra para los siguientes. No necesitas aprender programación ni electrónica antes de empezar. Si ya tienes algo de experiencia, puedes escribir tu propio código o dejar que lo haga la IA. Empieza por lo que quieres crear y cómo debe funcionar.

La IA te ayuda a definir la idea y a encontrar una forma práctica de realizarla, aprovechando el hardware, las herramientas y los conocimientos que ya tienes. Te ayuda con la lista de materiales, enlaces de compra opcionales, diagramas de conexión claros, código, carga del programa y depuración, para que puedas centrarte en lo que quieres conseguir.

No hay un curso fijo que todo el mundo deba seguir. Puedes empezar con una función sencilla o avanzar hacia un objetivo mayor. El proceso se adapta a tu situación y el resultado es un proyecto que responde a tus necesidades, con los archivos y las instrucciones para seguir usándolo y modificándolo.

## Elige tu habilidad

| Habilidad | Para quién | Quién escribe el código |
| --- | --- | --- |
| [Build with AI MCU](../skills/build-with-ai-mcu/SKILL.md) | Sin experiencia o empezando | La IA por defecto |
| [Develop with AI MCU](../skills/develop-with-ai-mcu/SKILL.md) | Conoce el funcionamiento básico y la carga del programa; ha creado proyectos sencillos | Tú o la IA; puedes cambiar de elección |

Cada habilidad funciona por separado. La experiencia conocida y la petición actual tienen prioridad; no hay que repetir una prueba de nivel ni cambiar de entrada a la fuerza. Si no se conoce tu experiencia y la petición es vaga, basta una elección breve entre empezar de cero o haber hecho proyectos sencillos.

## Cómo funciona

- **Tu idea es lo primero.** Si la primera frase ya explica lo que quieres, se omiten las preguntas ajenas a la tarea. La memoria relevante puede incluir experiencia, forma de conversar, preferencias de aprendizaje y pequeños hábitos. Se usan por separado; la petición actual manda, sin cuestionarios de presupuesto o estilo.
- **Conversa con naturalidad y empieza a actuar.** Recibe opciones breves cuando ayuden, sin la misma pregunta una y otra vez. La conversación sigue tu ritmo y el objetivo del proyecto. Cuando el siguiente paso está claro, empieza; no hace falta completar una larga entrevista.
- **Aprovecha lo que tienes.** Primero se revisan código, configuración e interfaces para ver si basta una solución de software. No se cambia una placa adecuada por comodidad ni se intenta suplir con código un sensor o una etapa de potencia que falta. Se usan primero las herramientas de desarrollo y carga existentes.
- **Comprueba qué falta.** Un panel permite marcar materiales y consultar especificaciones, cantidades, uso y coste adicional estimado. Puedes pedir enlaces para tu país o región y elegir productos equivalentes de otras tiendas.
- **Conecta con una imagen clara.** Recibe un diagrama etiquetado y pasos de conexión que coinciden con él. La IA verifica los modelos, explica lo esencial y decide si conviene conectar o cargar el programa primero.
- **Elige quién escribe si ya tienes experiencia.** En la entrada inicial, la IA escribe por defecto. En la siguiente puedes escribir con orientación, revisión y ayuda para depurar, o dejar la implementación a la IA. No se repiten elecciones conocidas y puedes cambiarlas. Se conserva el permiso de carga para el mismo dispositivo.
- **Conserva tu propio proyecto.** Recibe el código fuente, las conexiones y una guía breve. Tú decides si el proyecto será privado o de código abierto.

## Instalación

Descarga el repositorio con **Code → Download ZIP** en GitHub, o ejecuta:

```sh
git clone https://github.com/boyan-xu/build-with-ai-mcu.git
```

Copia la carpeta completa que elijas (`skills/build-with-ai-mcu` o `skills/develop-with-ai-mcu`) al directorio de habilidades de tu herramienta de IA; puedes instalar una o las dos. En Codex, usa `$CODEX_HOME/skills` si está definido; de lo contrario, `~/.codex/skills`. Revisa cualquier habilidad del mismo nombre antes de sustituirla. Actualiza la detección de habilidades o abre otra sesión si hace falta.

Cada habilidad mantiene unas instrucciones para los tres idiomas e incluye sus propios recursos. La conversación, el panel y las indicaciones del proyecto siguen el idioma elegido. Otras herramientas deben admitir este formato o permitir cargar las instrucciones; las capacidades varían según la plataforma.

## Empieza con tu idea

```text
Usa $build-with-ai-mcu. Quiero un aviso cuando deje una puerta abierta.
Ya tengo un ESP32 y Arduino IDE, pero nunca he usado un microcontrolador.
Ayúdame a definir cómo debe funcionar y encárgate del código.
```

Si no tienes una idea, pide cinco proyectos adecuados. Si ya tienes materiales o un proyecto a medias, empieza desde ahí. Un objetivo difícil puede dividirse en pasos relacionados sin perder la idea original.

Si ya tienes experiencia, también puedes empezar así:

```text
Usa $develop-with-ai-mcu. Continúa mi proyecto STM32 que ya funciona y añade control PWM.
Quiero escribir el código. Ayúdame a revisar la configuración del temporizador
y a elegir el siguiente paso de programación más pequeño.
```

## Una función que viste en otro producto

Indica el comportamiento concreto que quieres. Cuando sea adecuado, la IA comprueba y reutiliza una conexión disponible de [REA](https://github.com/morluto/rea); solo propone instalarlo o conectarlo si hace falta. Los proyectos normales no requieren REA y rechazarlo no detiene el trabajo. Consulta [el flujo opcional](../skills/build-with-ai-mcu/references/rea.md).

Antes de comercializar o publicar la reproducción, deben estar claros los permisos y derechos correspondientes. REA no concede derechos sobre el producto analizado; aprender por cuenta propia no es un permiso automático. El objetivo es implementar el comportamiento de forma independiente, no redistribuir código o recursos propietarios.

## Panel y ejemplo de conexiones

- [Panel reutilizable](../skills/build-with-ai-mcu/assets/parts-checklist.html): la IA lo prepara con tus materiales. Puede mostrarse en un chat compatible o abrirse como un archivo HTML independiente. Guarda el progreso cuando la plataforma o el navegador lo permiten; los cambios de cantidad o especificación requieren otra revisión.
- [Notas de integración](../skills/build-with-ai-mcu/references/checklist.md): el botón envía una solicitud a la IA cuando la plataforma lo permite; si no, muestra un texto para copiar. La página independiente no contacta en secreto con una IA ni con tiendas.
- [Ejemplo de conexión de baja tensión](../skills/build-with-ai-mcu/references/uno-led/README.md): imagen revisada, tabla de conexiones y asignación de pines coherente. Muestra el nivel de entrega, no un primer proyecto obligatorio.

## Herramientas y límites

Las dos habilidades cubren primeros proyectos y experiencia básica, no un curso avanzado ni un servicio de programación de dispositivos. La IA necesita acceso real a las herramientas para compilar, depurar o conectar con tu placa. La carga desde el navegador requiere hardware compatible, firmware y acceso local; no se garantiza funcionar siempre sin instalaciones.

Las descargas necesarias se explican antes. Se protegen tu trabajo y tus credenciales. Compilar o cargar correctamente no demuestra que el dispositivo funcione físicamente. Se comprueban hardware y permisos, sin pedir una y otra vez autorización para la misma operación. La memoria personal y los registros privados no se publican con el proyecto.

## Comprobar el código fuente

Ejecuta `node --test tests/*.test.mjs` para comprobar la lógica del panel y la coherencia del ejemplo. El formato de la habilidad puede revisarse con el [validador oficial de skill-creator](https://github.com/openai/skills/tree/main/skills/.system/skill-creator). Las simulaciones y pruebas de software no sustituyen las pruebas físicas.

## Licencia

[MIT](../LICENSE). Puedes usar, compartir y modificar esta habilidad. Cada persona decide la publicación y la licencia de su propio proyecto.
