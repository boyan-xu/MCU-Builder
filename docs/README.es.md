[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md)

# MCU Builder

**Trae una idea. Crea algo que puedas usar.**

Describe tu producto. La IA ayuda con requisitos, diseño, piezas, firmware, comprobaciones útiles, configuración y depuración mediante herramientas que realmente puede usar. Aprovecha tu hardware y software actuales. No necesitas hacer un curso ni gestionar código; también puedes elegir escribirlo. Un objetivo claro evita preguntas ajenas y la experiencia no impone un límite artificial de complejidad.

## Elige una entrada

| Skill | Función |
| --- | --- |
| [MCU Builder](../skills/build-with-ai-mcu/SKILL.md) — `$build-with-ai-mcu` | La IA gestiona el trabajo técnico de idea a producto. |
| [Colaboración de código](../skills/develop-with-ai-mcu/SKILL.md) — `$develop-with-ai-mcu` | Inicia o continúa un proyecto y elige quién escribe el código. |
| [Comprobaciones en segundo plano](../skills/test-mcu-in-background/SKILL.md) — `$test-mcu-in-background` | Reutiliza programas y entornos existentes para pruebas concretas. |
| [Grabación de firmware](../skills/flash-mcu-firmware/SKILL.md) — `$flash-mcu-firmware` | Previsualiza y realiza cargas autorizadas con herramientas existentes. |
| [Selección de productos](../skills/select-products-to-cart/SKILL.md) — `$select-products-to-cart` | Compara variantes verificadas y completa el carrito; nunca compra. |
| [Diseño PCB opcional](../skills/design-pcb-with-ai/SKILL.md) — `$design-pcb-with-ai` | Diseña y revisa una PCB solicitada con tu software EDA utilizable. |

Las seis carpetas son independientes. Se conservan los cinco nombres de llamada y la ruta del repositorio. Ninguna entrada obliga a instalar sus compañeras. Descarga el ZIP o clona y copia las carpetas completas elegidas desde `skills/` al directorio de Skills de tu herramienta. En Codex usa `$CODEX_HOME/skills` o `~/.codex/skills` si no está definido; revisa copias existentes antes de reemplazarlas y actualiza el descubrimiento si hace falta. Las herramientas disponibles dependen de la plataforma.

```sh
git clone https://github.com/boyan-xu/build-with-ai-mcu.git
```

```text
Usa $build-with-ai-mcu. Quiero un aviso sonoro si la puerta queda abierta
más de 30 segundos. Tengo ESP32 y Arduino IDE. Encárgate del código.
```

```text
Usa $develop-with-ai-mcu. Continúa mi proyecto STM32 y añade control PWM.
Quiero escribir el código. Revisa el temporizador y guía el siguiente paso.
```

## Primero una lista que puedas copiar

La salida predeterminada es una lista numerada completa de texto normal. Cada pieza indica modelo/especificación exactos, función, cantidades necesarias/disponibles/faltantes y coste estimado de lo que falta con fuente/fecha, o indica que se desconoce. Una frase de búsqueda separada y copiable conserva especificaciones críticas y unidades por paquete. Incluye cables, alimentación y consumibles necesarios. Desconocer tienda o región no retrasa la lista; enlaces verificados pueden complementar las palabras. Los paneles antiguos son opcionales solo si se solicitan.

Después de la lista COMPLETA, la IA ofrece ayuda con el carrito una vez. Al aceptar pregunta la plataforma solo si se desconoce y aclara: solo carrito, sin tramitar pedidos, pagar ni suscribirse. Reutiliza permiso y sitio conocidos; respeta una negativa o una petición de enlaces solamente. Requisitos duros, compatibilidad, stock, entrega, vendedor y presupuesto explícito son filtros; después cuenta preferencias verificadas antes de comparar precio. El mapa escalar opcional `preferred_specs` usa `specs` y `spec_evidence` por campo; sin evidencia no hay coincidencia ni puntuación inventada. Omitirlo conserva el orden anterior de total/plazo/vendedor oficial. Verifica variante, paquetes y carrito actual, conservando otros productos. [Contrato de selección](../skills/select-products-to-cart/references/workflow.md).

## Chat principal para el producto, agentes para el trabajo técnico

Si hay agentes, un mismo agente de firmware capaz lleva fuentes, compilación, pruebas y depuración. Solo una petición PCB añade un agente PCB separado. Máximo dos agentes simultáneos y un escritor por ámbito. La IA principal conserva decisiones y autorización, y recibe resultados breves, rutas de pruebas/evidencia, límites y siguiente acción. Si tú escribes código, no lo reescribe sin permiso. Sin agentes continúa trabajo acotado y explica límites. Delegar no autoriza hardware, compras, instalaciones ni publicación.

Ambas entradas de producto incluyen el mismo `scripts/mcu_project.py`, independiente y de biblioteca estándar; requiere Python 3.10+, sin importar Skills vecinas ni crear registros globales. La IA mantiene datos opcionales del proyecto; no pide formularios JSON. Reutiliza programas y cachés actuales, explicando antes las descargas necesarias.

| Comando | Resultado |
| --- | --- |
| `validate` / `export --for test\|flash\|shopping` | Comprobaciones por etapa y entradas compatibles; resta existencias físicas. |
| `parts` | Lista numerada exacta, búsquedas copiables y estado de oferta única/sitio conocido. |
| `wiring` | SVG, texto por cable y asignaciones de pines desde una conexión explícita. |
| `acceptance` / `diagnostics` | Estados/evidencia honestos y resúmenes acotados de informes permitidos. |
| `package` | ZIP permitido con hashes, marcado borrador/no verificado. |
| `package --reproducible` | Contrato final con categorías, entradas, compilación/versión y guía al extraer. |

[Contrato de herramientas](../skills/build-with-ai-mcu/references/project-tools.md) · [Contrato de réplica](../skills/build-with-ai-mcu/references/replication.md) · [Ejemplo ficticio de borrador](../skills/build-with-ai-mcu/assets/project-example/mcu-project.json).

## PCB solo cuando se solicita

La IA principal prepara `pcb-brief.json` con piezas exactas, redes/pines y alimentación comprobados, fuentes de encapsulados, contorno con dimensiones/forma/unidades, conectores, agujeros, zonas excluidas y límites de fabricación. Pregunta solo datos bloqueantes. El agente PCB persistente hace esquema, colocación y ruteado en tu EDA existente y utilizable, separado del firmware. Sin conexión utilizable o sin agentes entrega un brief/borrador honesto, nunca una PCB terminada ni una instalación forzada.

Revisa esquema/ERC, pieza real contra pads/polaridad del encapsulado, colocación/ruteado/DRC y montaje virtual/3D: holguras, orientación, dimensiones y acceso a conectores. Modelos ausentes siguen desconocidos. Simulación de circuito solo cuando sea útil y haya modelos fiables. Separa cada tipo de prueba; no hay garantía de cero errores.

Entrega fuentes EDA editables, esquema, PCB, BOM exacta, redes/conexiones e informes/límites. Para fabricante: Gerber/taladros y datos de montaje necesarios. Para DIY: guías específicas del proceso a escala 1:1 para cobre/contorno/taladros. Sin máquina, herramienta y proceso exactos no se genera G-code genérico. Reabre archivos finales de fabricación y vincúlalos a la revisión. Datos críticos desconocidos de piezas, redes, alimentación, encapsulados o proceso implican borrador. PCB es diseño electrónico; CAD mecánico automático e impresión directa quedan fuera. [Flujo PCB](../skills/design-pcb-with-ai/references/workflow.md).

## Un paquete que otra persona pueda construir

La entrega final incluye imagen de conexiones Y texto con pines de cada cable; BOM/especificaciones/cantidades/búsquedas exactas; fuentes completas compilables, configuración, bibliotecas y recursos; firmware compilado correspondiente cuando proceda; versiones exactas de herramientas/entorno y pasos de compilación/grabación; instrucciones de alimentación/montaje/uso/aceptación; archivos PCB/mecánicos/impresión utilizados; licencias/créditos; evidencia, versión, hashes y límites. Incluye todas las entradas específicas del proyecto, sin rutas privadas, includes/recursos ausentes, arreglos ocultos de IA ni otra sesión de IA para terminar el diseño.

Herramientas o dependencias que no se puedan redistribuir requieren versión exacta e instrucciones oficiales de adquisición/configuración como requisitos externos visibles. `START-HERE.md` las enumera tras extraer; no promete cero descargas ni funcionamiento totalmente desconectado. Cada replicador configura sus credenciales localmente. `--reproducible` comprueba archivos/categorías, includes entre comillas y un informe de compilación exitosa vinculado a entradas/firmware/herramientas/versión sin ejecutar código. La IA aún revisa una compilación limpia real y el inventario completo: las etiquetas no prueban dependencias transitivas arbitrarias ni veracidad del informe. El paquete básico sigue siendo borrador.

El objetivo es el mismo diseño, configuración y comportamiento especificados, con piezas exactas y pasos suministrados, sin volver a programar o diseñar. Integridad de archivos y prueba física son distintas; tolerancias físicas y comportamiento sin probar no pueden garantizarse idénticos. Resuelve hechos críticos de alimentación/pines/diseño antes de declarar entrega final, o explica el bloqueo.

## Comprobaciones y límites físicos

Elige pruebas según proyecto, cambio y riesgo; no todos necesitan cada prueba o simulador. Prioriza herramientas existentes en segundo plano y vistas de navegador si se desean. Informa por separado compilación, lógica del host, simulación MCU, revisión eléctrica, grabación/lectura y resultado físico, ligados a la versión probada. Una prueba del host o maqueta web no es simulación MCU ni prueba seguridad eléctrica.

Antes de conectar/alimentar verifica modelos, pines, fuente, polaridad, corriente y controladores, y compara imagen con firmware. Desconecta alimentación para cambiar cables; movimiento requiere límites y parada. Solo compilar no autoriza grabar. Reutiliza autorización clara del mismo objetivo durante depuración normal, comprobando firmware actual, objetivo y depurador y preservando el trabajo previo. Descarga, instalación y publicación tienen su alcance; registros/secretos siguen privados y crear un ZIP no publica.

## Ejemplo real y evidencia histórica

[STMGames V1](../showcases/stm-games-v1/README.es.md) es un dispositivo STM32 OLED real creado mediante muchas conversaciones y revisiones. Su autor diseñó la carcasa e hizo el montaje; GPT-6.1 Sol completó el código de aplicación con créditos de terceros conservados. [Fuentes](../showcases/stm-games-v1/firmware-source.zip), [conexiones](../showcases/stm-games-v1/wiring.svg), [3MF original](../showcases/stm-games-v1/OLEDGames.3mf). Aún faltan hechos eléctricos/de alimentación: **no es totalmente reproducible**; esta entrega no operó hardware ni volvió a ejecutar todos los juegos.

![STMGames V1 con carcasa amarilla](../showcases/stm-games-v1/photos/front.jpg)

El [ejemplo UNO de baja tensión](../skills/build-with-ai-mcu/references/uno-led/README.md) y el [registro del navegador de tienda ficticia](../skills/select-products-to-cart/references/fixture-verification.json) son evidencia histórica de sus fuentes/escenarios registrados. Editar código no implica una nueva ejecución MCU/navegador. [REA](../skills/build-with-ai-mcu/references/rea.md) sigue siendo opcional; primero hardware/software existentes.

## Verificar fuentes y licencia

Ejecuta `python -B -m unittest discover -s tests -p "*_test.py"` y `node --test tests/*.test.mjs`; valida cada Skill con skill-creator. Las pruebas usan objetivos/procesos de proveedores ficticios locales, no hardware ni cuentas de compra reales. [MIT](../LICENSE) cubre código/Skills originales; terceros conservan sus términos. Cada usuario decide si publica su proyecto.
