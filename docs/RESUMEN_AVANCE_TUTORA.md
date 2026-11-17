# Asistente conversacional para Odoo 18 — Resumen del avance y propuestas

**Trabajo de Integración Curricular:** Asistente conversacional inteligente (Chatbot) integrado a Odoo 18
para la optimización de consultas de procesos comerciales y financieros
**Autor:** Ismael Alexander Calle Pérez · **Directora:** Janneth Alexandra Chicaiza Espinoza
**Fecha:** 17 de noviembre de 2026 · **Versión del módulo:** 18.0.1.12.0

Este documento resume lo que está implementado en el código y la estructura del prototipo. Al final
se incluyen los cambios propuestos para su aprobación (sección 7).

---

## 1. Resumen general

El prototipo es un módulo de Odoo 18 Community (`chatbot_assistant`) que agrega a Discuss el contacto
**«Asistente ERP»**. El usuario le escribe en lenguaje natural, como a cualquier contacto, y el
asistente responde con datos reales de Odoo sobre facturas, inventario, ventas y vendedores.

Principio de diseño: **la IA interpreta, Odoo responde.**
- El modelo de lenguaje solo clasifica la pregunta y extrae los datos (cliente, producto, fechas…) en
  un JSON con formato fijo.
- El código valida ese JSON, comprueba los permisos del usuario y consulta Odoo mediante el ORM.
- **La IA no genera SQL, no elige tablas y nunca aporta cifras.** Todos los números de las
  respuestas provienen de Odoo.
- El alcance es solo de lectura: el asistente no crea, modifica ni elimina registros.

| Aspecto | Estado |
|---|---|
| Casos de uso CU-01 a CU-05 | Implementados |
| Conversación (saludos, preguntas sobre el asistente, rechazos) | Implementada |
| Memoria corta de la sesión (preguntas de seguimiento) | Implementada |
| Seguridad: permisos por consulta y reglas de Odoo | Implementada |
| Auditoría y métricas | Implementadas |
| Configuración del modelo de IA (catálogo, validación) | Implementada |
| Modelo de respaldo | Implementado |
| Resultados extensos: vista previa, «Ver todo» y CSV | Implementados |
| Pruebas automáticas e integración continua | 136 pruebas en Odoo y 22 unitarias, en verde |
| Ruta híbrida (consultas flexibles) | **Propuesta, pendiente de aprobación** |
| Evaluación final con el dataset | **Pendiente** |

---

## 2. Arquitectura y tecnologías

```
┌────────────────────────────── Docker ───────────────────────────────┐
│                                                                     │
│  ┌──────────────── Odoo 18 Community ───────────────┐  ┌──────────┐ │
│  │                                                  │  │PostgreSQL│ │
│  │  Discuss (chat)  ──►  Módulo chatbot_assistant   │◄─►│    16    │ │
│  │                        │                         │  └──────────┘ │
│  │  Ventas · Inventario · Facturación · Contactos   │               │
│  └────────────────────────┼─────────────────────────┘               │
└───────────────────────────┼─────────────────────────────────────────┘
                            │ HTTPS (solo el texto de la pregunta)
              ┌─────────────┴─────────────┐
              ▼                           ▼
   Google AI Studio (Gemini)        Groq (Llama, Qwen…)
   modelo principal o respaldo      modelo principal o respaldo
```

| Capa | Tecnología | Uso |
|---|---|---|
| ERP | Odoo 18 Community | Datos del negocio, permisos, interfaz (Discuss) |
| Base de datos | PostgreSQL 16 | Almacenamiento de Odoo (el asistente no accede directamente) |
| Contenedores | Docker y Docker Compose | Laboratorio local reproducible |
| Lenguaje | Python 3 (backend) y JavaScript/OWL (ajustes de interfaz) | Módulo de Odoo |
| Modelos de lenguaje | Gemini 2.5 Flash (Google AI Studio) y Llama 3.3 70B (Groq), configurables | Interpretación de la pregunta |
| Datos de prueba | Módulo `chatbot_test_data` (semilla fija) | Base sintética: 1.083 pedidos y 656 facturas |
| Calidad | GitHub y GitHub Actions; Playwright (Chromium) | Control de versiones, pruebas automáticas y pruebas en el navegador |

### Flujo de una consulta

```
Usuario escribe en Discuss
  → 1. Orquestador arma el mensaje (pregunta + fecha actual + memoria corta de la sesión)
  → 2. Modelo de IA devuelve JSON: intención, entidades y estado
        (si el principal no está disponible, responde el modelo de respaldo)
  → 3. Validador: intención del catálogo, estado permitido, fechas válidas, datos faltantes
  → 4. Permisos por consulta: ¿el usuario tiene el grupo de Odoo exigido?
  → 5. Función interna del caso de uso: consulta el ORM con los permisos del usuario
  → 6. Respuesta armada con plantilla (+ «Ver todo» y CSV si el resultado es extenso)
  → 7. Registro en la auditoría (resultado, tiempos, modelo, tokens, errores)
```

---

## 3. Estructura del código

```
tesis_chatbot_odoo/
├── addons/custom/
│   ├── chatbot_assistant/           Módulo del asistente
│   │   ├── models/                  Modelos de datos y lógica de Odoo
│   │   ├── services/                Lógica independiente de Odoo (IA, validación, casos de uso)
│   │   │   └── handlers/            Una función por caso de uso (CU-01 a CU-05)
│   │   ├── controllers/             Descarga del CSV
│   │   ├── views/ · data/ · security/   Pantallas, datos iniciales y permisos
│   │   ├── static/src/              Ajustes de la interfaz (chat y Ajustes)
│   │   ├── migrations/              Scripts de actualización entre versiones
│   │   └── tests/                   Pruebas automáticas en Odoo
│   └── chatbot_test_data/           Generador de la base de datos sintética
├── data/eval/eval_dataset.jsonl     Dataset de evaluación (62 consultas etiquetadas)
├── scripts/                         Instalación, respaldo, evaluación y pruebas e2e
├── docs/                            Seguimiento de cambios y pendientes de la tesis
└── .github/workflows/               Integración continua (pruebas en cada cambio)
```

### Componentes principales del módulo

| Componente | Archivo | Responsabilidad |
|---|---|---|
| Integración con el chat | `models/discuss_channel.py`, `models/chatbot_discuss_service.py` | Detecta los mensajes al «Asistente ERP» y publica la respuesta |
| Orquestador | `models/orchestrator.py` | Coordina el flujo completo y registra cada consulta |
| Cliente de IA | `services/llm_client.py` | Llamadas a Gemini y Groq, reintentos, errores y modelo de respaldo |
| Instrucciones de la IA | `services/prompt_builder.py` | Catálogo de intenciones y entidades, esquema de respuesta |
| Validador | `services/validator.py` | Revisa la salida de la IA y descarta cifras inventadas |
| Casos de uso | `services/handlers/*.py` | Consultas de solo lectura mediante el ORM |
| Resultados extensos | `services/result_set.py`, `controllers/main.py` | Vista previa, «Ver todo» y CSV |
| Sesión y mensajes | `models/chatbot_session.py`, `models/chatbot_message.py` | Memoria corta de la conversación |
| Permisos por consulta | `models/chatbot_intent_permission.py` | Grupo de Odoo exigido por cada caso de uso (tabla editable) |
| Auditoría | `models/chatbot_query_log.py` | Registro de cada consulta y métricas |
| Catálogo de modelos de IA | `models/chatbot_llm_model.py` | Modelos disponibles por proveedor, sincronizados con su API |
| Configuración | `models/res_config_settings.py` | Pantalla de Ajustes: proveedor, clave, modelo, respaldo |

### Modelos de datos propios

| Modelo | Contenido |
|---|---|
| `chatbot.session` | Conversación de un usuario con el asistente y su memoria corta |
| `chatbot.message` | Mensajes de la sesión |
| `chatbot.query.log` | Auditoría: pregunta, intención, resultado, tiempos, modelo, tokens, valoración, resultado extenso |
| `chatbot.intent.permission` | Grupos de Odoo exigidos por intención |
| `chatbot.llm.model` | Catálogo de modelos de IA por proveedor |

---

## 4. Funcionalidades implementadas

### 4.1 Casos de uso
| Caso | Pregunta de ejemplo | Responde |
|---|---|---|
| CU-01 Facturas | «¿Está pagada la factura INV/2026/00001?» | Estado, total y saldo; listado por cliente y periodo |
| CU-02 Inventario | «¿Cuánto stock hay del FIL-M01?» | Existencia, reservado y disponible |
| CU-03 Ventas | «Ventas de Comercial Andina S.A. en julio» | Pedidos y montos por cliente o producto, con estado (cotización, pedido, cancelado) |
| CU-04 Vendedor | «¿Quién es el vendedor de Moto Racing Cuenca?» | Vendedor con correo y teléfono |
| CU-05 Stock y facturación | «Stock y facturación del FIL-M01 este mes» | Stock actual y unidades y valor facturados |

Si hay varias coincidencias (por ejemplo, dos clientes parecidos), el asistente las muestra y pide
precisar. Si falta un dato, lo solicita.

### 4.2 Conversación y memoria
- Saludos, agradecimientos y preguntas sobre el asistente: los redacta la IA, sin datos del ERP.
- Solicitudes fuera del alcance («Crea una factura»): la IA explica qué puede y qué no puede hacer.
- **Control contra datos inventados:** si un texto redactado por la IA contiene cifras, se descarta
  y se usa un mensaje predeterminado.
- **Memoria corta:** «Stock del FIL-M01» → «¿y las ventas de este producto?» hereda el producto, pero
  no las fechas de la pregunta anterior.

### 4.3 Seguridad
- Las consultas se ejecutan **con el usuario que escribe**: Odoo aplica sus derechos de acceso y
  reglas de registro (un vendedor con acceso solo a sus documentos ve solo sus pedidos).
- **Permisos por consulta (mínimo privilegio):** cada caso de uso exige el grupo de su módulo
  (Facturación, Inventario, Ventas), configurable desde una tabla.
- Cada usuario ve solo sus propias sesiones y consultas; el administrador del chatbot ve todas.
- Los mensajes de error no revelan la existencia de registros que el usuario no puede ver.

### 4.4 Auditoría y métricas
- Cada consulta registra: resultado (respondida, sin resultados, aclaración, rechazo, sin permiso,
  IA no disponible, IA respondió mal, error interno), tiempos por etapa (IA, Odoo, total),
  reintentos, proveedor y modelo, tokens, uso del respaldo y valoración 👍/👎 del usuario.
- Menú **Métricas**: gráficos por día y resultado, tabla dinámica de latencias y exportación a Excel.
- Retención configurable: una tarea diaria borra los registros más antiguos (privacidad).

### 4.5 Configuración del modelo de IA
- Proveedor, API key, modelo, temperatura y tiempo de espera desde Ajustes.
- **Catálogo de modelos** sincronizado con la API de cada proveedor, con indicación estimada de si es
  gratuito o de pago.
- «Probar conexión» y «Actualizar modelos» funcionan sin guardar; al guardar se valida la conexión
  y una configuración que no funciona no se guarda.
- Rendimiento: razonamiento de Gemini desactivado, salida con esquema JSON, tiempo de espera de
  20 s y un reintento (espera máxima ≈ 40 s, antes más de 2 minutos).

### 4.6 Modelo de respaldo (pedido por la tutora)
- Segundo modelo, preferiblemente de otro proveedor, con la misma configuración que el principal.
- Responde cuando el principal **no está disponible** (caída, cuota agotada, tiempo agotado, clave
  inválida). No interviene si el principal respondió con un formato incorrecto.
- Para guardar basta con que **uno de los dos** responda; los errores de configuración siempre
  impiden guardar.
- La auditoría indica si respondió el respaldo y por qué falló el principal.

### 4.7 Resultados extensos (pedido por la tutora)
- El chat muestra un resumen y solo las **5 filas más recientes**, con el aviso «Mostrando 5 de N».
- **«Ver todo (N)»** abre la lista nativa de Odoo con los registros exactos de la respuesta.
- **«Descargar CSV»** cuando el resultado pasa de 5 filas, solo con los campos autorizados.
- Solo el dueño de la consulta puede abrir o descargar el resultado, y Odoo vuelve a aplicar sus
  permisos. Las descargas quedan registradas en la auditoría.

---

## 5. Calidad y forma de trabajo

- **Cada cambio en su propia rama**, con un *pull request* hacia la rama principal.
- **Un cambio solo se incorpora si todas las pruebas pasan** en GitHub Actions.
- Cada cambio se registra en `docs/SEGUIMIENTO_CAMBIOS.md`: qué se hizo, dónde y para qué.
- Antes de cada entrega se ejecutan también pruebas en el navegador (Chromium) y la actualización
  del módulo desde la versión anterior.

| Pruebas | Cantidad | Qué verifican |
|---|---|---|
| Casos de uso | 17 | Respuestas de CU-01 a CU-05 con datos de prueba |
| Orquestador y seguridad | 9 | Flujo completo, rechazos y privacidad entre usuarios |
| Permisos por perfil | 13 | Consultas permitidas y rechazadas por perfil |
| Métricas | 14 | Clasificación de resultados, tiempos, tokens y valoraciones |
| Velocidad | 5 | Esquema de respuesta, tiempo de espera y fallos de la IA |
| Selección del modelo | 18 | Catálogo, cambio de proveedor y validación al guardar |
| Conversación | 9 | Saludos, rechazos y descarte de datos inventados |
| Memoria y estado del pedido | 7 | Seguimientos y cambios de tema |
| Modelo de respaldo | 23 | Cada tipo de fallo y regla de guardado |
| Resultados extensos | 18 | Vista previa, «Ver todo», CSV y permisos (incluye descargas HTTP) |
| Actualización del módulo | 3 | Datos iniciales borrados y recreados por el administrador |
| **Total en Odoo 18** | **136** | |
| Unitarias (sin Odoo) | 22 | Validador, esquema de respuesta y cliente de IA |

Durante las pruebas se detectaron y corrigieron defectos que no eran visibles a simple vista, por
ejemplo: «Ver todo» fallaba para usuarios que no eran administradores, y la actualización del módulo
fallaba si el administrador había borrado y recreado un dato inicial.

### Historial de entregas

| PR | Entrega |
|---|---|
| #1 | Correcciones, CU-05 y pruebas automáticas |
| #2 | Plan de mejoras (documentación) |
| #3 | Métricas y monitoreo |
| #4 | Permisos por consulta |
| #5 | Velocidad de la llamada a la IA |
| #6 | Catálogo y validación del modelo de IA |
| #7 | Conversación redactada por la IA |
| #8 | Memoria de la sesión y estado del pedido |
| #9 | Ajustes de los datos de prueba y verificación del dataset |
| #10, #12 | Correcciones en la pantalla de Ajustes |
| #11 | Pendientes de la tesis (documentación) |
| #13 | Modelo de respaldo |
| #14 | Resultados extensos: vista previa, «Ver todo» y CSV |

---

## 6. Dataset de evaluación (estado actual)

Archivo `data/eval/eval_dataset.jsonl`: **62 consultas etiquetadas** con la respuesta esperada
(31 correctas, 10 incompletas, 4 ambiguas, 11 fuera del alcance y 6 de conversación). Las 31
respuestas esperadas se verificaron contra la base de pruebas (31 de 31).

Ejemplo de una consulta etiquetada:
```json
{"id": "Q001", "query": "¿Está pagada la factura INV/2026/00001?", "category": "correcta",
 "expected_intent": "consultar_factura", "expected_entities": {"invoice_number": "INV/2026/00001"},
 "expected_behavior": "execute", "expected_result_contains": ["pagada", "INV/2026/00001"]}
```

Un script envía cada consulta al asistente con la IA real, compara la respuesta con la esperada y
genera las métricas del Capítulo 5: acierto de intención, de entidades y de comportamiento, y tiempo
de respuesta, por modelo.

---

## 7. Cambios propuestos para aprobación

Para cada propuesta se indica qué es, un ejemplo, su impacto en la tesis y una recomendación.

### 7.1 Ruta híbrida: consultas flexibles validadas — **requiere decisión**
**Qué es.** Hoy el asistente solo responde preguntas que encajan en CU-01 a CU-05. La propuesta
agrega una segunda ruta para otras preguntas de datos: la IA genera un **plan en JSON** con piezas
permitidas (modelo, filtros, operación) y el código lo valida contra un **catálogo cerrado de modelos
y campos** antes de ejecutarlo con el ORM. No se genera SQL.

```
Pregunta → ¿Caso de uso CU-01…05? → Ruta 1 (como hoy)
         → ¿Otra pregunta de datos? → Ruta 2 (plan JSON validado)
         → ¿Saludo o fuera de alcance? → conversación o rechazo
```

**Ejemplo.** «¿Qué productos cuestan menos de $20?»
```json
{"intent": "consulta_flexible",
 "plan": {"modelo": "product.product", "operacion": "listar",
          "filtros": [{"campo": "list_price", "operador": "<", "valor": 20}]}}
```
Respuesta: *«Interpreté: productos con precio de venta menor a $20. Encontré 14 productos…»*

| Respondería | No respondería |
|---|---|
| «¿Cuántos clientes tiene asignados Andrea Villafuerte?» (contar) | «¿Cuál es el RUC de Comercial Andina?» (campo sensible) |
| «Total facturado en octubre» (sumar) | «¿Cuánto ganamos con el casco?» (costo, varios pasos) |
| «Ventas por vendedor este año» (agrupar) | «Borra las facturas vencidas» (escritura) |
| «Facturas vencidas de más de $500» (listar) | «Clientes que compraron cascos pero nunca filtros» (cruce complejo) |

**Controles:** catálogo cerrado (editable por el administrador), operadores válidos por tipo de campo,
solo lectura, permisos de Odoo, la línea «Interpreté: …» y el registro del plan en la auditoría.

**Impacto en la tesis:** secciones 3.3 y 3.4 (dos rutas, nuevo esquema JSON, Tabla 6 como catálogo)
y comparación de la Ruta 1 con la Ruta 2 en el Capítulo 5.
**Esfuerzo:** es el cambio más grande pendiente.
**Recomendación:** implementarla si el tiempo lo permite, porque amplía el alcance sin abandonar el
diseño seguro (sin text-to-SQL).

### 7.2 Ampliación del dataset y evaluación final — **necesario para el Capítulo 5**
**Qué es.** Completar el conjunto de consultas y ejecutar la evaluación con los modelos reales.

| Se agrega | Ejemplo | Comportamiento esperado |
|---|---|---|
| Errores de tipeo | «factras de comersial andina» | Entender la consulta |
| Más ambiguas (hoy hay 4) | «Ventas de Carlos» | Mostrar coincidencias |
| Encadenadas | «Stock del FIL-M01» → «¿y cuánto se vendió?» | Recordar el producto |
| Cambios de tema | «Ventas de X» → «¿y el stock del casco?» | No mezclar datos |
| Límites del asistente | «¿Cuánto venderemos el próximo mes?», «¿Cuánto gana Juan?» | Rechazar sin inventar |
| Ruta 2 (si se aprueba 7.1) | «Productos de menos de $20» | Plan y resultado correctos |

Además, se harán más estrictas las etiquetas que hoy aceptan varios comportamientos. El dataset se
congela antes de la evaluación final para que los resultados sean reproducibles y la comparación
entre modelos (Gemini y Groq) sea justa.
**Recomendación:** hacerlo después de decidir 7.1, para que la evaluación cubra ambas rutas.

### 7.3 Cifrado de la API key — **requiere decisión**
**Hoy:** la clave se guarda en texto plano en los parámetros del sistema de Odoo, visibles solo para
los administradores, y se envía al proveedor en un encabezado HTTP, nunca en la URL.
**Propuesta:** guardarla cifrada (AES) con una clave maestra en el archivo de entorno del servidor, y
que el campo sea de solo escritura (se puede reemplazar, pero no leer desde la pantalla).
**Impacto en la tesis:** Sprint 2 y limitaciones.
**Recomendación:** implementarla; el esfuerzo es moderado y refuerza la sección de seguridad.

### 7.4 Mejoras de conversación — **requiere decisión**
| Mejora | Ejemplo | Hoy |
|---|---|---|
| Varias consultas en un mensaje | «Ventas del CAS-001 y su stock» | Atiende solo una |
| Códigos de producto aproximados | «stock del FILM01» (sin guion) | Puede no encontrarlo |
| Saludo más consulta | «Hola, ¿qué facturas tiene X?» | Verificar que siempre ejecute la consulta |

**Recomendación:** la segunda y la tercera son pequeñas; la primera es mediana y puede quedar como
trabajo futuro si se implementa 7.1.

### 7.5 Mejoras opcionales (si queda tiempo)
- **Respuesta sin bloquear el chat:** el mensaje del usuario aparece de inmediato y se muestra
  «escribiendo…» mientras responde la IA.
- **Respuestas de datos redactadas por la IA**, con verificación de que cada número provenga de
  Odoo. Permitiría un experimento de plantilla frente a redacción por IA.
- **Monitoreo de disponibilidad:** tarea programada que prueba la conexión con la IA y registra
  caídas aunque nadie use el chat.

### 7.6 Documento de la tesis: diagramas en lugar de código
Siguiendo la recomendación de la tutora, se propone reemplazar el código de los Capítulos 3 y 4 por:

| Diagrama | Explica |
|---|---|
| Arquitectura (modelo C4: contexto y contenedores) | Componentes y tecnologías |
| Despliegue | Contenedores, puertos y conexión con las APIs |
| Casos de uso (UML) | Actores y CU-01 a CU-05 |
| Clases del módulo | Modelos propios, orquestador y funciones internas |
| Modelo de datos de Odoo consultado | Relaciones entre clientes, pedidos, facturas y stock |
| Secuencia de una consulta | Del mensaje del usuario a la respuesta |
| Actividad del modelo de respaldo | Cuándo responde el respaldo |
| Secuencia de «Ver todo» y CSV | Resultados extensos y permisos |

El código quedaría disponible en el repositorio (enlace) o, si se prefiere, en un anexo breve.

---

## 8. Decisiones solicitadas

| # | Propuesta | Aprobación |
|---|---|---|
| 7.1 | Ruta híbrida con plan JSON validado | ☐ Sí ☐ No ☐ Trabajo futuro |
| 7.2 | Ampliación del dataset y evaluación final | ☐ Sí |
| 7.3 | Cifrado de la API key | ☐ Sí ☐ No |
| 7.4 | Mejoras de conversación (indicar cuáles) | ☐ Varias consultas ☐ Códigos aproximados ☐ Saludo más consulta |
| 7.5 | Mejoras opcionales (indicar cuáles) | ☐ Sin bloqueo ☐ Redacción por IA ☐ Monitoreo |
| 7.6 | Diagramas en lugar de código; código en ☐ enlace al repositorio ☐ anexo | ☐ Sí |

**Pendiente del autor, en paralelo:** pruebas manuales con las claves reales de Gemini y Groq
(chat completo CU-01 a CU-05, modelo de respaldo y resultados extensos).
