[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md)

# Haz realidad tus ideas con microcontroladores

**Trae una idea. Crea algo que puedas usar.**

Explica qué quieres que haga tu producto. La IA concreta los requisitos y se encarga del diseño, materiales, firmware, simulación, configuración y depuración con las herramientas a las que realmente tiene acceso. No necesitas aprender a programar microcontroladores ni gestionar el código para empezar.

Aprovecha el hardware y los programas que ya tienes. Recibe una lista de materiales que puedes marcar, enlaces de compra opcionales para tu región, un diagrama claro y pasos breves para el trabajo físico. En diseños compatibles, la IA ejecuta una simulación real del microcontrolador y revisa el diseño eléctrico por separado antes de guiar la primera prueba conectada.

Un avisador, un controlador, un dispositivo con sensores: el comportamiento que buscas marca el rumbo. El proceso sigue tu idea y su viabilidad real, sin imponer un límite por tu nivel de experiencia. Avanza mediante resultados concretos hasta obtener algo útil, con los archivos e indicaciones para seguir usándolo y mejorándolo.

## Elige cómo trabajar

| Entrada | Qué hace | Quién escribe el código |
| --- | --- | --- |
| [Haz realidad tus ideas con microcontroladores](../skills/build-with-ai-mcu/SKILL.md) | La IA lleva la parte técnica desde la idea hasta el producto | La IA por defecto |
| [Desarrollo colaborativo](../skills/develop-with-ai-mcu/SKILL.md) | Colabora en un producto nuevo o continúa un proyecto existente | Tú o la IA; puedes cambiar de elección |

Cada entrada funciona por separado y se adapta a tu experiencia y preferencias. Una petición clara evita preguntas ajenas a la tarea; no hay una prueba de nivel que decida qué puedes crear. Cambia el título público, pero se mantienen la dirección del repositorio, las carpetas y las llamadas `$build-with-ai-mcu` y `$develop-with-ai-mcu`.

## De la idea al producto

1. **Define el resultado.** Habla de lo que debe hacer y cómo comprobarlo. La memoria relevante puede incluir herramientas, experiencia, preferencias al conversar, forma de aprender y pequeños hábitos. Tu petición actual tiene prioridad, sin cuestionarios de presupuesto o estilo.
2. **Reutiliza lo adecuado.** Primero se revisan código, configuración, interfaces y hardware existentes. Para piezas nuevas se prefieren combinaciones de MCU y módulos con simulación documentada que cumplan la necesidad; no se cambia una placa útil por comodidad.
3. **Comprueba qué comprar.** El panel muestra especificaciones, cantidades, materiales disponibles, faltantes y coste adicional estimado. Los enlaces regionales son ejemplos; puedes elegir piezas equivalentes de otras tiendas.
4. **La IA implementa y verifica.** Escribe, compila, simula y corrige el firmware con las herramientas disponibles. Si quieres escribir, elige la entrada colaborativa. No necesitas completar un curso ni gestionar cambios de código.
5. **Conecta y prueba.** Recibe una imagen revisada y texto coincidente. El orden entre conexiones sin alimentación y carga en la placa depende del montaje. Cada vez se indica una acción breve, el resultado esperado y qué comunicar; se conserva la autorización del mismo dispositivo.
6. **Conserva tu producto.** Recibe código, conexiones, archivos y resultados de simulación, una guía breve y límites conocidos. Tú decides si el producto será privado o de código abierto.

La conversación sigue tu ritmo sin insistir en la misma pregunta ni desviarse. Cuando el siguiente paso está claro, se empieza. Obtener algo útil en pocos días es un objetivo cuando lo permiten el alcance, las herramientas y las piezas, no una promesa para cualquier idea ni un catálogo fijo de ejercicios iniciales.

## Simulación y primera puesta en marcha

En diseños compatibles se prueban los escenarios pertinentes de arranque, funcionamiento normal, límites, tiempos y fallos antes de operar el circuito con dispositivos o cargas externas. Se guardan la versión real de código o compilación, conexiones, proyecto y resultados, y se repiten las comprobaciones afectadas por cambios. Compilar, probar lógica en el ordenador o crear una maqueta web no equivale a simular el MCU.

La simulación no demuestra ausencia total de errores ni que sea imposible dañar el hardware. Se comprueban aparte alimentación, polaridad, niveles lógicos, corriente, resistencias, controladores y límites de carga. Se informa por separado de compilación, pruebas de lógica, simulación MCU, revisión eléctrica, carga/lectura y comportamiento físico.

Si tu placa o módulo no tiene un modelo adecuado, la IA explica lo que no puede cubrir y continúa con código, compilación y comprobaciones de lógica. Con permiso para el dispositivo exacto y tras revisar objetivo y condiciones eléctricas, puede hacerse una carga y diagnóstico de la placa aislando las cargas externas. Eso alimenta la placa, pero no significa que todo el producto haya superado la simulación ni permita pasar directamente a plena carga. Consulta [las reglas de verificación](../skills/build-with-ai-mcu/references/verification.md).

## Instalar y empezar

Descarga con **Code → Download ZIP** en GitHub o ejecuta:

```sh
git clone https://github.com/boyan-xu/build-with-ai-mcu.git
```

Copia la carpeta completa de una o ambas entradas (`skills/build-with-ai-mcu`, `skills/develop-with-ai-mcu`) al directorio de habilidades admitido por tu herramienta. En Codex, usa `$CODEX_HOME/skills` si está definido; si no, `~/.codex/skills`. Revisa una habilidad del mismo nombre antes de sustituirla; actualiza la detección o abre otra sesión si hace falta. Cada entrada incluye sus recursos y unas instrucciones para los tres idiomas. Las herramientas disponibles varían según la plataforma.

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

- [Panel de materiales](../skills/build-with-ai-mcu/assets/parts-checklist.html) y [notas de integración](../skills/build-with-ai-mcu/references/checklist.md): marca materiales y conserva el progreso válido en chats compatibles o HTML independiente. Las solicitudes de enlaces usan la acción de IA disponible o muestran texto para copiar. La página no contacta en secreto con tiendas ni con una IA.
- [Ejemplo de baja tensión](../skills/build-with-ai-mcu/references/uno-led/README.md): imagen, conexiones, firmware y diagrama coherentes, con un [registro real de simulación MCU](../skills/build-with-ai-mcu/references/uno-led/simulation-result.json) ligado a los archivos probados. Arranque y salida digital se comprobaron en Wokwi; no se probó hardware físico ni se demostró seguridad eléctrica. Es evidencia de esos escenarios, no un primer producto obligatorio.
- [Flujo opcional de REA](../skills/build-with-ai-mcu/references/rea.md): al reproducir una función, reutiliza una conexión pertinente de [REA](https://github.com/morluto/rea) y solo propone configurarlo si es necesario y falta. Rechazarlo no impide proyectos normales. Antes de comercializar o publicar se aclaran los derechos; el acceso a una herramienta no autoriza a distribuir código o recursos propietarios.

## Alcance mecánico y límites prácticos

Esta versión no incluye normalmente CAD automático, diseño mecánico listo para imprimir ni impresión directa. Para una carcasa se prefieren piezas comerciales, estructuras existentes o modelos aportados por el usuario. La experiencia en CAD y las impresoras o CNC siguen siendo contexto útil. Una futura etapa automática de CAD/impresión requiere una actualización explícita de la habilidad; no se activa por la confianza del propio modelo.

La IA necesita conexiones reales para compilar, depurar, simular o acceder al hardware. Las descargas, cuentas y costes necesarios se explican antes. La carga desde el navegador necesita hardware compatible y acceso local; no se promete funcionar siempre sin instalaciones. Credenciales, memoria y registros privados no se publican. Es un flujo para crear productos, no un curso fijo de microcontroladores.

## Comprobar el código fuente

Ejecuta `node --test tests/*.test.mjs` para comprobar panel, paquetes, conexiones y coherencia del registro. El formato puede revisarse con el [validador oficial de skill-creator](https://github.com/openai/skills/tree/main/skills/.system/skill-creator). Las pruebas unitarias son distintas de la ejecución MCU registrada y no sustituyen pruebas físicas.

## Licencia

[MIT](../LICENSE). Puedes usar, compartir y modificar estas habilidades. Cada persona decide la publicación y licencia de su producto.
