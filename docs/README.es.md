[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md)

# Haz realidad tus ideas con microcontroladores

**Trae una idea. Crea algo que puedas usar.**

Explica qué quieres que haga tu producto. La IA concreta los requisitos y se encarga del diseño, materiales, firmware, simulación, configuración y depuración con las herramientas a las que realmente tiene acceso. No necesitas aprender a programar microcontroladores ni gestionar el código para empezar.

Aprovecha el hardware y los programas que ya tienes. Recibe una lista de materiales que puedes marcar, enlaces de compra opcionales para tu región, un diagrama claro y pasos breves para el trabajo físico. La IA elige comprobaciones útiles para el proyecto, normalmente en segundo plano, y revisa el diseño eléctrico antes de guiar el funcionamiento físico.

Un avisador, un controlador, un dispositivo con sensores: el comportamiento que buscas marca el rumbo. El proceso sigue tu idea y su viabilidad real, sin imponer un límite por tu nivel de experiencia. Avanza mediante resultados concretos hasta obtener algo útil, con los archivos e indicaciones para seguir usándolo y mejorándolo.

## Un proyecto real: STMGames V1

Una consola STM32 con OLED y carcasa amarilla impresa, creada tras **muchas rondas de conversación, montaje y revisión**. Su creador realizó el modelado 3D y el trabajo físico; **GPT-6.1 Sol completó todo el código de aplicación**, conservando los créditos de terceros. No fue una generación de un solo intento ni un resultado de CAD automático.

| Frente | Interior |
| --- | --- |
| ![Consola OLED en una carcasa amarilla impresa](../showcases/stm-games-v1/photos/front.jpg) | ![Placa STM32 y pilas dentro de la carcasa](../showcases/stm-games-v1/photos/inside.jpg) |

La colección incluye Snake, Tetris, Space Invaders, Dino, 2048, Minesweeper, Breakout, Tower Defense, Stack y Timberman, además de nueve proyectos independientes. Consulta [el caso y los materiales](../showcases/stm-games-v1/README.es.md), descarga [todo el código del firmware](../showcases/stm-games-v1/firmware-source.zip), revisa [el diagrama](../showcases/stm-games-v1/wiring.svg) y [la tabla de conexiones](../showcases/stm-games-v1/README.es.md#conexiones-y-alimentación), o abre [el modelo y proyecto de laminado 3MF original](../showcases/stm-games-v1/OLEDGames.3mf). Las fotos muestran el montaje real; parte de la alimentación sigue sin verificarse y esta publicación no repitió todos los juegos ni operó hardware.

## Elige cómo trabajar

| Entrada | Qué hace | Quién escribe el código |
| --- | --- | --- |
| [Haz realidad tus ideas con microcontroladores](../skills/build-with-ai-mcu/SKILL.md) | La IA lleva la parte técnica desde la idea hasta el producto | La IA por defecto |
| [Desarrollo colaborativo](../skills/develop-with-ai-mcu/SKILL.md) | Colabora en un producto nuevo o continúa un proyecto existente | Tú o la IA; puedes cambiar de elección |
| [Pruebas en segundo plano](../skills/test-mcu-in-background/SKILL.md) | Ejecuta comprobaciones con scripts incluidos y entorno reutilizable | La IA prepara y ejecuta las pruebas útiles |
| [Carga de firmware](../skills/flash-mcu-firmware/SKILL.md) | Reutiliza programas de carga mediante un script incluido | La IA comprueba el destino y realiza cargas autorizadas |

Las cuatro entradas funcionan por separado. Las dos entradas de creación se adaptan a tu experiencia y preferencias. Una petición clara evita preguntas ajenas a la tarea; no hay una prueba de nivel que decida qué puedes crear. Se mantienen la dirección del repositorio, las carpetas y las llamadas `$build-with-ai-mcu` y `$develop-with-ai-mcu`. Se añaden `$test-mcu-in-background` y `$flash-mcu-firmware` como herramientas ejecutables.

## De la idea al producto

1. **Define el resultado.** Habla de lo que debe hacer y cómo comprobarlo. La memoria relevante puede incluir herramientas, experiencia, preferencias al conversar, forma de aprender y pequeños hábitos. Tu petición actual tiene prioridad, sin cuestionarios de presupuesto o estilo.
2. **Reutiliza lo adecuado.** Primero se revisan código, configuración, interfaces y hardware existentes. Para piezas nuevas se prefieren combinaciones de MCU y módulos con simulación documentada que cumplan la necesidad; no se cambia una placa útil por comodidad.
3. **Comprueba qué comprar.** El panel muestra especificaciones, cantidades, materiales disponibles, faltantes y coste adicional estimado. Los enlaces regionales son ejemplos; puedes elegir piezas equivalentes de otras tiendas.
4. **La IA implementa y verifica.** Escribe, compila y corrige el firmware con las herramientas disponibles, eligiendo pruebas o simulación cuando sean útiles. Si quieres escribir, elige la entrada colaborativa. No necesitas completar un curso ni gestionar cambios de código.
5. **Conecta y prueba.** Recibe una imagen revisada y texto coincidente. El orden entre conexiones sin alimentación y carga en la placa depende del montaje. Cada vez se indica una acción breve, el resultado esperado y qué comunicar; se conserva la autorización del mismo dispositivo.
6. **Conserva tu producto.** Recibe código, conexiones, los archivos y resultados de pruebas o simulación que se hayan producido, una guía breve y límites conocidos. Tú decides si el producto será privado o de código abierto.

La conversación sigue tu ritmo sin insistir en la misma pregunta ni desviarse. Cuando el siguiente paso está claro, se empieza. Obtener algo útil en pocos días es un objetivo cuando lo permiten el alcance, las herramientas y las piezas, no una promesa para cualquier idea ni un catálogo fijo de ejercicios iniciales.

## Comprobaciones, vista previa y primera puesta en marcha

No todos los proyectos necesitan pruebas o simulación. La IA elige comprobaciones que resuelvan una incertidumbre o un riesgo real y utiliza por defecto las herramientas existentes en segundo plano. Si quieres ver el efecto antes de cargar el programa, puede ofrecer una vista previa en el navegador o imágenes renderizadas. El proceso se adapta a tu necesidad actual, sin imponer una secuencia fija.

Se conservan las evidencias de las comprobaciones realizadas, vinculadas al código y las conexiones probadas. Compilar, probar lógica en el ordenador o crear una maqueta web no equivale a simular el MCU. Ejecutar instrucciones ARM con periféricos simulados cubre las rutas de código ejercitadas, pero no toda la placa ni su comportamiento eléctrico. Los cambios pertinentes requieren volver a comprobar lo afectado cuando sea necesario.

La simulación no demuestra ausencia total de errores ni que sea imposible dañar el hardware. Se comprueban aparte alimentación, polaridad, niveles lógicos, corriente, resistencias, controladores y límites de carga. Se informa por separado de compilación, pruebas de lógica, simulación MCU, revisión eléctrica, carga/lectura y comportamiento físico.

Si tu placa o módulo no tiene un modelo adecuado, se conserva cuando cumple el objetivo. La IA explica las carencias relevantes y continúa el trabajo seguro y útil con las herramientas disponibles. Con permiso para el dispositivo exacto y tras revisar objetivo y condiciones eléctricas, puede hacerse una carga y diagnóstico de la placa aislando las cargas externas. Eso no demuestra que funcione todo el producto ni permite pasar directamente a plena carga. Consulta [las reglas de verificación](../skills/build-with-ai-mcu/references/verification.md).

## Instalar y empezar

Descarga con **Code → Download ZIP** en GitHub o ejecuta:

```sh
git clone https://github.com/boyan-xu/build-with-ai-mcu.git
```

Copia las carpetas completas que necesites de `skills/` al directorio de habilidades admitido por tu herramienta. Las entradas de creación son `build-with-ai-mcu` y `develop-with-ai-mcu`; las herramientas ejecutables son `test-mcu-in-background` y `flash-mcu-firmware`. En Codex, usa `$CODEX_HOME/skills` si está definido; si no, `~/.codex/skills`. Revisa una habilidad del mismo nombre antes de sustituirla; actualiza la detección o abre otra sesión si hace falta. Cada entrada incluye sus recursos y unas instrucciones para los tres idiomas. Las herramientas disponibles varían según la plataforma.

```text
Usa $build-with-ai-mcu. Crea un avisador que suene si dejo la puerta abierta
más de 30 segundos. Encárgate de la parte técnica; ya tengo un ESP32
y Arduino IDE. Ayúdame a conseguir un resultado que funcione.
```

```text
Usa $develop-with-ai-mcu. Continúa mi proyecto STM32 que ya funciona y añade PWM.
Quiero escribir el código. Revisa el temporizador y ayúdame a elegir
el siguiente cambio pequeño.
```

Si no tienes una idea, pide cinco posibilidades adecuadas. Si ya hay materiales o un producto a medias, empieza desde ahí. Los pasos deben llevar a tu objetivo, no sustituirlo por un ejercicio ajeno.

## Herramientas y evidencias incluidas

- **Herramientas ejecutables reutilizables:** el [script de pruebas](../skills/test-mcu-in-background/references/workflow.md) ejecuta comprobaciones existentes o compila y ejecuta C para Cortex-M, con imágenes opcionales del búfer OLED. El [script de carga](../skills/flash-mcu-firmware/references/workflow.md) muestra una vista previa sin hardware por defecto y reutiliza programas STM32, ESP o Arduino para escrituras autorizadas. La IA prepara la configuración del proyecto; no necesitas editar scripts ni JSON. Requiere Python 3.10 o posterior. Las dependencias ARM se preparan una vez en una caché privada y se reutilizan. El compilador y una herramienta de carga compatible deben estar disponibles; cualquier instalación necesaria se explica primero. Los scripts no simulan todos los periféricos ni garantizan cualquier placa sin adaptación.

- [Panel de materiales](../skills/build-with-ai-mcu/assets/parts-checklist.html) y [notas de integración](../skills/build-with-ai-mcu/references/checklist.md): marca materiales y conserva el progreso válido en chats compatibles o HTML independiente. Las solicitudes de enlaces usan la acción de IA disponible o muestran texto para copiar. La página no contacta en secreto con tiendas ni con una IA.
- [Ejemplo de baja tensión](../skills/build-with-ai-mcu/references/uno-led/README.md): imagen, conexiones, firmware y diagrama coherentes, con un [registro real de simulación MCU](../skills/build-with-ai-mcu/references/uno-led/simulation-result.json) ligado a los archivos probados. Arranque y salida digital se comprobaron en Wokwi; no se probó hardware físico ni se demostró seguridad eléctrica. Es evidencia de esos escenarios, no un primer producto obligatorio.
- [Flujo opcional de REA](../skills/build-with-ai-mcu/references/rea.md): al reproducir una función, reutiliza una conexión pertinente de [REA](https://github.com/morluto/rea) y solo propone configurarlo si es necesario y falta. Rechazarlo no impide proyectos normales. Antes de comercializar o publicar se aclaran los derechos; el acceso a una herramienta no autoriza a distribuir código o recursos propietarios.

## Alcance mecánico y límites prácticos

Esta versión no incluye normalmente CAD automático, diseño mecánico listo para imprimir ni impresión directa. Para una carcasa se prefieren piezas comerciales, estructuras existentes o modelos aportados por el usuario. La experiencia en CAD y las impresoras o CNC siguen siendo contexto útil. Una futura etapa automática de CAD/impresión requiere una actualización explícita de la habilidad; no se activa por la confianza del propio modelo.

La IA necesita conexiones reales para compilar, depurar, simular o acceder al hardware. Las descargas, cuentas y costes necesarios se explican antes. La carga desde el navegador necesita hardware compatible y acceso local; no se promete funcionar siempre sin instalaciones. Credenciales, memoria y registros privados no se publican. Es un flujo para crear productos, no un curso fijo de microcontroladores.

## Comprobar el código fuente

Ejecuta `node --test tests/*.test.mjs` para comprobar panel, paquetes, conexiones y coherencia del registro. El formato puede revisarse con el [validador oficial de skill-creator](https://github.com/openai/skills/tree/main/skills/.system/skill-creator). Las pruebas unitarias son distintas de la ejecución MCU registrada y no sustituyen pruebas físicas.

Ejecuta `python -B -m unittest discover -s tests -p "*_test.py"` para comprobar reutilización, fallos, adaptadores de carga sin hardware y exportación OLED. Las pruebas de carga usan procesos de proveedor simulados; la ejecución ARM real del ejemplo tiene evidencias separadas en la guía de pruebas.

## Licencia

[MIT](../LICENSE). Puedes usar, compartir y modificar estas habilidades y sus scripts originales. Las dependencias descargadas conservan sus propias licencias. Cada persona decide la publicación y licencia de su producto.
