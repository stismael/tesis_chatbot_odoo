# Seguimiento de cambios del prototipo

Registro de las correcciones y mejoras del código. Marcar `[x]` cuando un punto quede terminado.
Los cambios pendientes en el **documento de la tesis** están en
[`PENDIENTES_TESIS.md`](PENDIENTES_TESIS.md).

## Ramas

| Rama | Contenido | Estado |
|---|---|---|
| `claude/repository-analysis-84h0jn` | Totales de ventas, privacidad, test corregido | Fusionada en `main` (PR #1) |
| `feature/cu05-stock-facturacion-producto` | CU-05, stock unificado, lista de la tesis | Fusionada en `main` (PR #1) |
| `fix/correcciones-handlers-y-pruebas-odoo` | Correcciones del punto 1 y pruebas en Odoo | Fusionada en `main` (PR #1) |
| `docs/plan-mejoras-llm-y-permisos` | Planificación de los puntos 7 a 14 (solo documentación) | Fusionada en `main` (PR #2) |
| `feature/metricas-y-monitoreo` | Paso 1: métricas y monitoreo | Fusionada en `main` (PR #3) |
| `feature/permisos-por-consulta` | Paso 2: permisos por consulta | Fusionada en `main` (PR #4) |
| `feature/velocidad-llm` | Paso 3: velocidad de la IA | Fusionada en `main` (PR #5) |
| `feature/seleccion-modelo` | Paso 4: catálogo y validación del modelo | PR #6 |

Las ramas siguientes se crean una por paso del **plan de avance** (abajo).

---

## Registro de cambios aprobados

Cada vez que se aprueba y fusiona un PR en `main` se agrega aquí una entrada con **qué se hizo**,
**dónde** (archivos) y **para qué**. Las entradas van de la más reciente a la más antigua.

### PR #6 · Paso 4: catálogo y validación del modelo de IA
- **Rama:** `feature/seleccion-modelo` · **Versión del módulo:** 18.0.1.8.0
- **Estado:** se fusiona cuando las pruebas de GitHub Actions pasen.
- **Pruebas:** 69 pruebas en Odoo 18 (11 nuevas) y 2 pruebas unitarias nuevas; verificada la
  actualización desde 18.0.1.7.0.

| Qué se hizo | Dónde | Para qué |
|---|---|---|
| Al cambiar de proveedor, el modelo pasa siempre al recomendado | `models/res_config_settings.py` (`_onchange_chatbot_provider`) | Corregir el defecto verificado: con `openai/gpt-oss-120b` o `qwen/qwen3-32b` el campo se quedaba con un modelo de Groq aunque el proveedor fuera Gemini |
| Catálogo de modelos por proveedor con "Actualizar modelos": sincroniza sin borrar (agrega, actualiza, marca "no disponible", reactiva); tarea semanal | `models/chatbot_llm_model.py`, `data/chatbot_llm_model_data.xml`, `views/chatbot_llm_model_views.xml`, `views/menus.xml`, `security/ir.model.access.csv` | Responder a la tutora de dónde sale la lista de modelos y mantenerla al día sin perder historial |
| Listados solo con modelos de texto (Groq sin audio ni moderación) y todas las páginas de Gemini | `services/llm_client.py` (`list_gemini_models`, `list_groq_models`, `is_text_model`) | Que no se pueda elegir un modelo que no sirve para el chatbot |
| Desplegable filtrado por proveedor, aviso de modelo no disponible, fecha de actualización y enlace a precios | `models/res_config_settings.py`, `views/res_config_settings_views.xml` | Evitar elegir un modelo de otro proveedor y dejar claro que la API no informa si es gratuito |
| Prueba de conexión al guardar si cambió el proveedor, la API key o el modelo; no al desactivar ni al cambiar otros datos; rechazo de modelos de otro proveedor | `models/res_config_settings.py` (`set_values`, `_chatbot_check_before_save`) | Que no se guarde una configuración que no funciona y que una caída del proveedor no impida apagar el asistente |
| Estado del proveedor en Ajustes: última verificación y última falla de la auditoría | `models/res_config_settings.py`, `views/res_config_settings_views.xml` | Ver de un vistazo si la IA está fallando después de guardar |
| Corrección de "Activar asistente": se guarda siempre como "True" / "False" | `models/res_config_settings.py` | Defecto verificado en `main`: Odoo borra el parámetro de un booleano en False, el asistente seguía activo y el ajuste volvía a aparecer marcado |
| Pruebas de cambio de proveedor, catálogo, desplegable, guardado y estado; paginación de Gemini y filtro de Groq | `tests/test_model_selection.py`, `scripts/test_chatbot_unit.py` | Evitar regresiones en la configuración del LLM |

### PR #5 · Paso 3: velocidad de la llamada a la IA
- **Rama:** `feature/velocidad-llm` · **Versión del módulo:** 18.0.1.7.0
- **Estado:** fusionado el 2026-10-19, con las pruebas de GitHub Actions en verde.
- **Pruebas:** 58 pruebas en Odoo 18 (5 nuevas) y 3 pruebas unitarias nuevas; verificada la
  actualización desde 18.0.1.6.0 (timeout de 45 s a 20 s).

| Qué se hizo | Dónde | Para qué |
|---|---|---|
| Gemini 2.5 Flash y Flash-Lite sin "pensamiento" (`thinkingBudget: 0`); 2.5 Pro y otros modelos conservan la configuración del proveedor | `services/llm_client.py` (`_gemini_generation_config`) | Responder más rápido: clasificar y extraer datos no requiere razonar |
| Esquema de respuesta (`responseSchema`) generado desde las intenciones, entidades y estados permitidos | `services/prompt_builder.py` (`RESPONSE_SCHEMA`, `ENTITY_KEYS`), `services/validator.py`, `models/orchestrator.py` | Evitar JSON inválido e intenciones inventadas; una sola lista de entidades |
| Timeout por defecto de 20 s y un solo reintento; migración que cambia el valor antiguo de 45 s y respeta uno personalizado | `services/llm_client.py`, `models/res_config_settings.py`, `data/default_params.xml`, `hooks.py`, `migrations/18.0.1.7.0/post-migrate.py` | Bajar el peor caso de espera de más de 2 minutos a unos 41 s |
| Ejemplo "Hola" en el prompt y pruebas de que el chat siempre responde, también con la IA caída | `services/prompt_builder.py`, `tests/test_speed.py` | Que un saludo nunca quede sin respuesta |
| Pruebas de la configuración enviada a Gemini, del esquema y de los reintentos | `scripts/test_chatbot_unit.py`, `tests/test_speed.py` | Evitar regresiones en la llamada a la IA |

### PR #4 · Paso 2: permisos por consulta
- **Rama:** `feature/permisos-por-consulta` · **Versión del módulo:** 18.0.1.6.0
- **Estado:** fusionado el 2026-10-19, con las pruebas de GitHub Actions en verde.
- **Pruebas:** 53 pruebas en Odoo 18 (13 nuevas, por perfil de usuario); verificada la
  actualización desde 18.0.1.5.0.

| Qué se hizo | Dónde | Para qué |
|---|---|---|
| Tabla editable de permisos por consulta con los grupos mínimos (Facturación, Inventario / Usuario, Ventas / Usuario) | `models/chatbot_intent_permission.py`, `data/chatbot_intent_permission_data.xml`, `views/chatbot_intent_permission_views.xml`, `views/menus.xml`, `security/ir.model.access.csv` | Aplicar el principio de mínimo privilegio: cada consulta exige el rol de su módulo, porque Odoo permite lecturas cruzadas (por ejemplo, todo usuario interno lee existencias) |
| Control de permisos en el orquestador, antes de ejecutar y antes de pedir datos faltantes; registro como "Sin permiso" con código propio | `models/orchestrator.py`, `models/chatbot_query_log.py` | Que un usuario sin el rol no reciba datos ni preguntas de aclaración, y que el intento quede auditado |
| Mensajes que no confirman registros no visibles ("…entre las facturas que puedes consultar") y aviso de totales parciales | `services/handlers/access.py`, `services/handlers/factura.py`, `services/handlers/ventas.py`, `services/handlers/stock_facturacion.py` | Que el usuario entienda que la respuesta se limita a lo que puede ver (por ejemplo, un vendedor que solo ve sus pedidos) |
| `/help` muestra solo las consultas permitidas | `services/help_text.py`, `models/discuss_channel.py` | No ofrecer ejemplos de consultas que el usuario no puede hacer |
| Pruebas por perfil: sin grupos, solo Inventario, administrador de Inventario, solo Facturación, vendedor, administrador; edición de la tabla y su seguridad | `tests/test_permissions.py`, `tests/test_metrics.py` | Demostrar la matriz de permisos para la tesis y evitar regresiones |

### PR #3 · Paso 1: métricas y monitoreo
- **Rama:** `feature/metricas-y-monitoreo` · **Versión del módulo:** 18.0.1.5.0
- **Estado:** fusionado el 2026-10-19, con las pruebas de GitHub Actions en verde.
- **Pruebas:** 40 pruebas en Odoo 18 (14 nuevas) y pruebas unitarias; verificados el camino real de
  las reacciones de Discuss y la actualización desde 18.0.1.4.1.

| Qué se hizo | Dónde | Para qué |
|---|---|---|
| Resultado clasificado de cada mensaje (respondida, sin resultados, aclaración, rechazada, sin permiso, IA no disponible, IA respondió mal, error interno) y código de error de la IA | `models/chatbot_query_log.py`, `models/orchestrator.py` | Saber cuándo el chatbot responde bien, cuándo no y cuándo la IA no está disponible (observación de la tutora) |
| Tiempos por etapa (IA, Odoo, total) y número de reintentos | `models/orchestrator.py`, `services/llm_client.py` | Saber dónde se demora la respuesta; medición de "antes" para el paso 3 |
| Proveedor, modelo y tokens de entrada, salida y razonamiento | `services/llm_client.py` (`complete_json(meta=…)`, `_gemini_usage`, `_groq_usage`) | Comparar modelos y medir el costo del "pensamiento" de Gemini |
| Valoración 👍 / 👎 con reacciones de Discuss | `models/mail_message_reaction.py`, `models/chatbot_discuss_service.py` | Medir si la respuesta le sirvió al usuario en uso real |
| Menú *Chatbot → Métricas* (gráfico, tabla dinámica, filtros, agrupaciones) y Auditoría ampliada | `views/chatbot_query_log_views.xml`, `views/menus.xml` | Analizar resultados y latencias sin herramientas externas; exportar datos para el Capítulo 5 |
| Ajuste "Conservar auditoría (días)" y tarea diaria de limpieza | `models/res_config_settings.py`, `views/res_config_settings_views.xml`, `data/ir_cron.xml`, `data/default_params.xml` | Limitar cuánto tiempo se guardan las preguntas de los usuarios (privacidad) |
| Error de permisos de Odoo mostrado en español; detalle técnico solo en el log | `models/orchestrator.py` (`FORBIDDEN_MSG`) | Que el usuario no vea mensajes técnicos en inglés |
| Pruebas de métricas | `tests/test_metrics.py`, `scripts/test_chatbot_unit.py` | Comprobar cada clasificación, tiempos, metadatos, reacciones y limpieza |

### PR #2 · Plan de mejoras y pendientes de la tesis (solo documentación)
- **Rama:** `docs/plan-mejoras-llm-y-permisos`
- **Estado:** fusionado el 2026-10-19, con las pruebas de GitHub Actions en verde.

| Qué se hizo | Dónde | Para qué |
|---|---|---|
| Plan de avance en 9 pasos y puntos 7 a 14 (velocidad, conversación, modelo, redacción, permisos, métricas, ruta híbrida, límites) | `docs/SEGUIMIENTO_CAMBIOS.md` | Ordenar el trabajo en pasos pequeños, cada uno probado antes del siguiente |
| Cambios del documento derivados de cada punto, declaración del uso de IA (formato UTPL) y defensa ante el tribunal | `docs/PENDIENTES_TESIS.md` | Mantener la tesis alineada con el código y preparar la defensa |

### PR #1 · Correcciones, CU-05 y pruebas automáticas (fusionado el 2026-10-13)
- **Ramas:** `claude/repository-analysis-84h0jn`, `feature/cu05-stock-facturacion-producto` y
  `fix/correcciones-handlers-y-pruebas-odoo` · **Versión del módulo:** 18.0.1.4.1
- **Pruebas:** 26 pruebas en Odoo 18, en verde en GitHub Actions.

| Qué se hizo | Dónde | Para qué |
|---|---|---|
| El resumen de ventas por cliente cuenta y suma todos los pedidos, no solo los 15 más recientes | `services/handlers/ventas.py` | Que los totales de ventas sean correctos |
| Reglas de registro: cada usuario ve solo sus sesiones, mensajes y consultas; el administrador ve todo | `security/chatbot_security.xml` | Privacidad entre usuarios |
| CU-05: stock y facturación por producto en un periodo | `services/handlers/stock_facturacion.py`, `services/prompt_builder.py`, `services/validator.py`, `models/orchestrator.py` | Responder en una sola consulta existencias y lo facturado (caso de uso de la tesis) |
| Fecha actual enviada a la IA y fechas normalizadas a AAAA-MM-DD | `services/prompt_builder.py`, `services/validator.py` | Resolver "este mes" o "julio" y evitar errores por fechas inválidas |
| Stock unificado: existencia, reservado y disponible, con el mismo cálculo con o sin ubicación | `services/handlers/stock.py` | Que CU-02 y CU-05 den cifras coherentes con Odoo |
| CU-01 aplica el periodo de fechas | `services/handlers/factura.py` | Cumplir lo que dice la Tabla 15 de la tesis |
| El chat no muestra textos de errores internos | `models/chatbot_discuss_service.py` | No exponer detalles técnicos al usuario |
| API key de Gemini en el encabezado y timeout de 45 s en Ajustes | `services/llm_client.py`, `models/res_config_settings.py` | Seguridad de la clave y configuración coherente |
| 26 pruebas en Odoo, script local y GitHub Actions | `tests/`, `scripts/run-odoo-tests.ps1`, `.github/workflows/pruebas.yml` | Detectar errores automáticamente en cada cambio |
| Test de errores HTTP corregido y 5 consultas de CU-05 en el dataset | `scripts/test_chatbot_unit.py`, `data/eval/eval_dataset.jsonl` | Pruebas en verde y evaluación del nuevo caso de uso |
| Listas de seguimiento del código y de la tesis | `docs/SEGUIMIENTO_CAMBIOS.md`, `docs/PENDIENTES_TESIS.md` | Llevar el control de lo hecho y lo pendiente |

---

## Plan de avance (paso a paso)

Cada paso va en **su propia rama**, con pruebas automáticas, un PR hacia `main` y una **prueba
manual en tu Odoo con Gemini real** antes de pasar al siguiente. Si algo falla en la prueba manual,
se corrige en esa misma rama.

| Paso | Punto | Rama sugerida | Por qué en este orden |
|---|---|---|---|
| 1 ✅ | 12. Métricas y monitoreo | `feature/metricas-y-monitoreo` | Medir primero: da los números de "antes" para todo lo demás |
| 2 ✅ | 11. Permisos por consulta | `feature/permisos-por-consulta` | Seguridad; la Ruta 2 (paso 7) depende de esta tabla |
| 3 ✅ | 7. Velocidad de la IA | `feature/velocidad-llm` | Con las métricas ya activas se mide el antes y el después |
| 4 (en revisión) | 9. Selección y validación del modelo | `feature/seleccion-modelo` | Corrige el defecto del campo "Modelo" y valida la configuración |
| 5 | 8. Conversación libre | `feature/conversacion-libre` | Requiere la IA rápida (paso 3), porque los saludos también la llaman |
| 6 | 3 y 4. Memoria y `order_state` | `fix/memoria-y-estado-pedido` | Ajustes acotados sobre el flujo actual |
| 7 | 13. Ruta híbrida | `feature/ruta-hibrida` | Usa la tabla de permisos (paso 2), las métricas (paso 1) y la clasificación (paso 5) |
| 8 | 6. Dataset de evaluación | `feature/dataset-evaluacion` | Con todas las rutas listas, se amplía y se ejecuta la evaluación final |
| 9 | 5 y 10. Respuesta sin bloqueo y redacción por IA (opcionales) | `feature/respuesta-asincrona` | Mejoras finales si queda tiempo |

**Ciclo de cada paso**
1. Crear la rama desde `main` actualizado.
2. Implementar con pruebas automáticas (unitarias y en Odoo).
3. Abrir el PR, con la lista de comprobación para la prueba manual en tu Odoo con Gemini real.
4. Cuando GitHub Actions pase, fusionar el PR en `main`.
5. Agregar la entrada en **Registro de cambios aprobados** (qué, dónde, para qué) y marcar las
   casillas del punto.
6. Empezar el paso siguiente. Si la prueba manual encuentra algo, se corrige en el paso siguiente
   o en una rama `fix/…`.

---

## Hecho

### Revisión inicial
- [x] Test de mapeo de errores HTTP que fallaba (`scripts/test_chatbot_unit.py`).
- [x] Resumen de ventas por cliente: contaba y sumaba solo los 15 pedidos más recientes; ahora usa
      todos y el límite de 15 aplica solo al listado.
- [x] Reglas de registro: cada usuario ve solo sus sesiones, mensajes y consultas; el administrador
      del chatbot ve todo.
- [x] Comentarios del orquestador en español uniforme.

### CU-05: stock y facturación por producto
- [x] Nueva intención `consultar_stock_facturacion_producto` con su handler
      (`services/handlers/stock_facturacion.py`).
- [x] Prompt con reglas y ejemplos de CU-05; se envía la fecha actual al LLM para resolver "este mes",
      "julio", etc.
- [x] Validador: entidad requerida para CU-05 y normalización de fechas a AAAA-MM-DD (las no válidas
      se descartan).
- [x] Los datos faltantes se piden con "o" ("el nombre del producto o el código del producto").
- [x] 5 consultas de CU-05 en el dataset (Q052 a Q056) y corrección del ID duplicado Q050 → Q051.
- [x] Ayuda (`/help`), mensaje de bienvenida y documentación actualizados.

### Stock unificado (CU-02 y CU-05)
- [x] Ambos casos calculan desde `stock.quant` y muestran existencia, reservado y disponible para la
      venta. Verificado contra `qty_available` y `free_qty` de Odoo.

### Punto 1: correcciones rápidas
- [x] El chat ya no muestra el texto de errores internos; muestra el mensaje amable.
- [x] CU-01 aplica el periodo (`date_from`, `date_to`) sobre la fecha de factura.
- [x] Timeout por defecto coherente: 45 s también en Ajustes.
- [x] La API key de Gemini se envía en el encabezado `x-goog-api-key`, no en la URL.
- [x] Ventas con fecha final: **no era un error**. Odoo 18 ya incluye todo el día al comparar una
      fecha y hora con `<= AAAA-MM-DD`. Se dejó una prueba que protege ese comportamiento.

### Punto 2: pruebas automáticas
- [x] 26 pruebas dentro de Odoo (`addons/custom/chatbot_assistant/tests/`), con datos propios:
  - [x] CU-01 a CU-05, ambigüedad, ubicación inexistente y facturas en borrador.
  - [x] Flujo completo del orquestador con el LLM simulado (sin red): datos faltantes, seguimiento,
        fuera de alcance, intención inventada y envío de la fecha actual.
  - [x] Privacidad: un usuario no ve sesiones, mensajes ni consultas de otro; el administrador sí.
  - [x] Errores internos no visibles en el chat de Discuss.
- [x] Se comprobó que las pruebas fallan con el código anterior a las correcciones (filtro por periodo
      y mensaje de error).
- [x] Prueba unitaria (sin Odoo) de que la API key no viaja en la URL.
- [x] Script `scripts/run-odoo-tests.ps1` para correr las pruebas en tu PC.
- [x] GitHub Actions (`.github/workflows/pruebas.yml`): pruebas unitarias y pruebas en Odoo 18 en cada
      push y pull request.

---

## Pendiente

### Punto 3: memoria de conversación
- [ ] Evitar que entidades de una pregunta anterior se mezclen cuando el usuario cambia de tema.
- [ ] Simplificar la lógica de fusión del orquestador (hoy valida dos veces y lee la sesión dos veces).
- [ ] Pruebas de cambio de tema.

### Punto 4: intenciones y entidades del documento
- [ ] `intencion_desconocida`: se reemplaza por la intención `conversacion` (punto 8).
- [ ] Decidir sobre `order_state` (cotización, pedido, cancelado): implementar (recomendado) o quitar.
- [ ] Volumen de pedidos del generador: 350 en el código vs. ~1.000 en la tesis.

### Punto 5: la llamada al LLM no debe bloquear el chat
- [ ] Procesar la respuesta fuera de la transacción del mensaje (cola, cron o `postcommit`), con
      indicador de "escribiendo…" en Discuss. Tu mensaje debe aparecer de inmediato.
- [ ] Revisar reintentos y timeout para que no superen el límite del worker de Odoo (ver punto 7).

### Punto 6: dataset de evaluación
- [ ] Más consultas ambiguas (hoy solo 4).
- [ ] Etiquetas más estrictas: revisar `clarify_or_execute`, `clarify_or_not_found` y
      `reject_or_clarify`, que aceptan casi cualquier resultado.
- [ ] Más variedad: errores de tipeo, preguntas encadenadas y cambios de tema.
- [ ] Ejecutar `run-chatbot-eval.ps1` con la API key y guardar resultados por modelo.

### Punto 7: velocidad de la llamada a la IA
Va antes del punto 8, porque con el 8 los saludos también llaman a la IA. Conviene hacer primero el
punto 12 (métricas) para medir los tiempos antes y después de estas mejoras.
- [x] Desactivar el "pensamiento" de Gemini 2.5 (`thinkingConfig: {thinkingBudget: 0}`); la tarea es
      clasificar y extraer datos, no razonar.
- [x] Exigir el formato con `responseSchema` (Gemini) y `json_object` (Groq) para evitar JSON inválido.
- [x] Timeout de ~20 s y un solo reintento (hoy 45 s × 3 intentos más pausas: más de 2 minutos).
- [ ] Revisar el caso "Hola" sin respuesta con el registro de Chatbot → Consultas (estado, error,
      latencia). Avance: el código siempre responde (probado con rechazo y con la IA caída) y "Hola"
      está en los ejemplos del prompt. Falta confirmar la causa con Gemini real en la prueba manual.

### Punto 8: conversación libre con datos siempre desde Odoo (arquitectura híbrida)
- [ ] Nueva intención `conversacion` y campo `reply` en el JSON: para saludos, agradecimientos,
      "¿qué puedes hacer?" y charla, la IA redacta la respuesta en la misma llamada (sin textos fijos
      en el código y sin llamada extra).
- [ ] Respuestas fuera de alcance redactadas por la IA (por qué no puede y qué sí puede hacer), con el
      mensaje fijo actual solo como respaldo si `reply` viene vacío.
- [ ] Regla en el prompt: si la pregunta es sobre datos de la empresa, se usa una intención de
      consulta, nunca `conversacion`.
- [ ] Control anti-invención en el validador: si una respuesta conversacional contiene montos,
      números de factura o códigos de producto, se descarta y no se muestra.
- [ ] Límite de longitud de `reply`.
- [ ] Pruebas: saludo, agradecimiento, pregunta de capacidades, rechazo redactado y pregunta de datos
      disfrazada de charla ("¿cuánto vendí ayer?").
- [ ] Consultas de conversación en el dataset de evaluación.

### Punto 9: selección y validación del modelo

**Defecto verificado en Odoo 18:** al cambiar de Groq a Gemini, el campo "Modelo" solo se corrige si
el nombre contiene "llama" o "groq". Con `openai/gpt-oss-120b` o `qwen/qwen3-32b` el campo se queda
con el modelo de Groq aunque el proveedor sea Gemini, y el chat falla con "modelo no encontrado".
(La lista de "Listar modelos" sí es correcta: con Gemini solo consulta a Google y con Groq solo a
Groq; los modelos Gemma que aparecen con Gemini son de Google.)

**Arreglo inmediato**
- [x] Al cambiar de proveedor, reemplazar **siempre** el modelo por el recomendado del nuevo proveedor
      (Gemini → `gemini-2.5-flash`; Groq → `llama-3.3-70b-versatile`), sin adivinar por el nombre.

**Catálogo de modelos en Odoo**
- [x] Tabla de modelos por proveedor (proveedor, ID, nombre, descripción, límite de tokens,
      disponible) y botón **"Actualizar modelos"**.
- [x] La actualización **sincroniza, no borra**, y solo toca el proveedor consultado:
  - modelo nuevo → se agrega;
  - modelo existente → se actualizan sus datos;
  - modelo que ya no aparece → se marca **"No disponible"** y sale del desplegable;
  - modelo que vuelve a aparecer → se marca disponible otra vez.
- [x] Guardar la fecha de la última actualización y mostrarla en Ajustes.
- [x] (Opcional) Tarea programada que actualice el catálogo una vez por semana.
- [x] El campo "Modelo" pasa a ser un **desplegable filtrado por el proveedor elegido**, solo con
      modelos de texto disponibles y el recomendado marcado; así no se puede elegir un modelo de otro
      proveedor.
- [x] Filtrar también la lista de Groq: hoy muestra todo su catálogo, incluidos modelos que no son
      de texto (por ejemplo, Whisper para audio).
- [x] Leer todas las páginas del listado de Gemini (hoy pide hasta 100 y no sigue `nextPageToken`).
- [x] Mostrar los datos que entrega la API (nombre, descripción, límite de tokens) y un enlace a la
      página de precios del proveedor, ya que la API no informa si un modelo es gratuito.
- [x] Aviso en Ajustes si el modelo configurado quedó **"No disponible"**: "El modelo configurado ya
      no está disponible en <proveedor>. Elige otro."

**Validación al guardar la configuración**
- [x] Al pulsar **Guardar**, si cambió el proveedor, la API key o el modelo, probar la conexión
      automáticamente:
  - si funciona, guardar y mostrar "Conexión verificada el <fecha> con <modelo>";
  - si falla, no guardar y explicar el motivo (API key inválida, modelo inexistente en el proveedor,
    sin conexión, cuota agotada).
- [x] No probar cuando solo cambian otros datos (temperatura, timeout) ni al **desactivar** el
      chatbot, para que una caída del proveedor no impida apagar el asistente.
- [x] Validar también que el modelo pertenezca al proveedor elegido ("El modelo 'qwen/qwen3-32b' no
      pertenece a Google Gemini").
- [x] Mantener el botón **"Probar conexión"** para verificar en cualquier momento sin guardar.

**Fallos después de guardar (fuera del control del sistema)**
- [x] Indicador en Ajustes con el último error del proveedor y su fecha.
- [ ] (Opcional) **Modelo de respaldo**: si el principal falla (caída, cuota agotada), intentar con
      otro configurado, incluso de otro proveedor, y registrar en el log qué modelo respondió.

**Pruebas**
- [x] Cambio Groq → Gemini con `llama-3.3-70b-versatile`, `openai/gpt-oss-120b`, `qwen/qwen3-32b` y
      `deepseek-r1-distill-llama-70b`: el campo debe quedar en `gemini-2.5-flash`. Y el cambio
      inverso Gemini → Groq.
- [x] Sincronización del catálogo: agregar, actualizar, marcar "No disponible" y reactivar.
- [x] El desplegable solo muestra modelos disponibles del proveedor elegido.
- [x] Guardar con conexión fallida no guarda y muestra el motivo; desactivar el chatbot guarda sin
      probar.
- [ ] (Si se implementa) el modelo de respaldo responde cuando el principal falla.

**Defecto encontrado y corregido en este paso:** el ajuste "Activar asistente" no se podía apagar.
Odoo borra el parámetro de un booleano guardado en False; el asistente lo leía como activo y el
ajuste volvía a aparecer marcado. Verificado en una base de `main`; ahora se guarda como "True" /
"False" y la desactivación se mantiene al actualizar el módulo.

### Punto 10 (opcional): respuestas de datos redactadas por la IA
- [ ] Interruptor en Ajustes "Respuestas redactadas por la IA", apagado por defecto.
- [ ] Segunda llamada a la IA con los datos del handler para redactar la respuesta.
- [ ] Verificación: cada número de la respuesta debe existir en los datos de Odoo; si no, se usa la
      plantilla.
- [ ] Experimento para el Capítulo 5: plantilla vs. redacción por IA (exactitud, latencia,
      naturalidad).

### Punto 11: usuarios sin permisos (hallazgos verificados en Odoo 18)
La seguridad funciona: el chatbot nunca muestra datos que Odoo no permita ver al usuario. Lo que hay
que mejorar son los mensajes y una decisión de diseño.
- [x] **Mensaje técnico en inglés al usuario** (resuelto en el paso 1 al clasificar "Sin permiso"). Sin permiso de Contabilidad o Ventas, el chat muestra
      el error crudo de Odoo ("You are not allowed to access 'Journal Entry'… groups: Invoicing/
      Administrator"). Debe responder en español y sin detalles técnicos, por ejemplo "No tienes
      permiso para consultar facturas. Pide acceso al administrador.", y registrar el detalle solo
      en el log. Causa: `AccessError` hereda de `UserError` y el orquestador muestra su texto.
- [x] **Registros que existen pero el usuario no puede ver.** Un vendedor que solo ve sus propios
      documentos recibe "No encontré la factura INV/…" o "No hay pedidos confirmados", aunque existan.
      Cambiar a "No encontré… o no tienes acceso a ese registro" (sin confirmar que existe).
- [x] **Totales parciales sin aviso.** En CU-05 el administrador ve 137 unidades facturadas en 29
      facturas y el vendedor ve 0 en 0, porque Odoo filtra las facturas que puede ver. Es correcto
      por seguridad, pero la respuesta debe aclarar "según los documentos a los que tienes acceso"
      cuando el usuario no tiene acceso total.
- [x] **Permiso del módulo de cada consulta (decidido).** Odoo reparte la lectura entre módulos de
      forma cruzada (verificado en los `ir.model.access.csv` de Odoo 18):
      - `stock.quant` y `res.partner`: los lee **cualquier usuario interno**.
      - `sale.order`: también Facturación, Inventario, Fabricación y Proyectos.
      - `account.move`: también Ventas (solo sus documentos), Compras, Punto de Venta y Gastos.

      El asistente exigirá, además de los permisos de Odoo, el grupo del módulo de cada consulta:

      | Consulta | Grupo exigido |
      |---|---|
      | CU-01 Facturas | Facturación o Contabilidad |
      | CU-02 Stock | Inventario (Usuario o Administrador) |
      | CU-03 Ventas | Ventas |
      | CU-04 Vendedor asignado | Ventas |
      | CU-05 Stock + facturación | Inventario **y** Facturación |

  - [x] **Implementación (opción A, decidida): tabla editable** en *Chatbot → Permisos por consulta*, una fila por intención con los grupos exigidos (todos deben
        cumplirse). Se carga con valores por defecto al instalar (`noupdate`) y el administrador del
        chatbot puede cambiarla sin tocar código. Una fila sin grupos usa solo los permisos de Odoo.
  - [x] **Grupos mínimos por defecto** (nivel Usuario; el Administrador de cada módulo incluye al
        Usuario en Odoo 18, así que pasa automáticamente con `has_group`):

        | Consulta | Grupo técnico mínimo | Nombre en Ajustes → Usuarios |
        |---|---|---|
        | CU-01 Facturas | `account.group_account_invoice` | Facturación / Contabilidad: Facturación |
        | CU-02 Stock | `stock.group_stock_user` | Inventario: Usuario |
        | CU-03 Ventas | `sales_team.group_sale_salesman` | Ventas: Usuario, solo documentos propios |
        | CU-04 Vendedor asignado | `sales_team.group_sale_salesman` | Ventas: Usuario, solo documentos propios |
        | CU-05 Stock + facturación | `stock.group_stock_user` y `account.group_account_invoice` | Inventario: Usuario y Facturación |

  - [x] Caso especial: el grupo oculto `account.group_account_readonly` (solo lectura contable) no
        incluye a Facturación; queda fuera por defecto. Como la tabla exige *todos* los grupos de una
        fila, para admitir a esos usuarios habría que quitar Facturación de la fila (pasa a depender
        solo de los permisos de Odoo).
  - [x] **Dónde va el control:** en el orquestador, después del validador y antes de ejecutar el
        handler. Es solo del chatbot: no modifica ningún permiso de Odoo ni afecta otras pantallas.
        Se evalúa por usuario y en cada mensaje, con los grupos que tenga en ese momento.
  - [x] Sin el grupo: no se consulta nada y se responde en español, por ejemplo "No tienes permiso
        para consultar inventario. Pide acceso al administrador."
  - [x] Registrar el intento rechazado en el log con estado `forbidden` ("sin permiso") para
        auditoría.
  - [x] Las reglas de registro de Odoo se siguen aplicando encima (un vendedor ve solo sus documentos).
  - [x] Seguridad de la tabla: el administrador del chatbot la edita; los usuarios solo la leen.
  - [x] (Opcional) `/help` muestra solo los ejemplos de las consultas que el usuario puede hacer.
- [x] Pruebas por perfil y por consulta: usuario interno sin grupos, solo Inventario, vendedor (solo
      sus documentos), usuario de Facturación y administrador; con la opción activada y desactivada.

**Implementado en `feature/permisos-por-consulta` (versión 18.0.1.6.0)**
- Tabla *Chatbot → Permisos por consulta* con los grupos mínimos cargados al instalar; el control
  se aplica antes de ejecutar y antes de pedir datos faltantes.
- Mensajes: "No encontré la factura X entre las facturas que puedes consultar", "No hay pedidos
  confirmados que puedas consultar…" y el aviso "Solo se incluyen los documentos a los que tienes
  acceso" cuando el usuario ve parte de los documentos.
- `/help` muestra solo las consultas permitidas.
- 13 pruebas nuevas por perfil (53 en total); verificada la actualización desde 18.0.1.5.0.

### Punto 12: métricas y monitoreo (observación de la tutora)
Objetivo: saber cuándo el chatbot responde bien, cuándo no, cuándo la IA no está disponible y dónde
se demora. Hoy *Chatbot → Auditoría de consultas* guarda la latencia total, un "éxito" sí/no y el
error como texto libre, lo que no basta para analizar.

**Resultado clasificado de cada mensaje** (lista fija, para filtrar y agrupar)
- [x] Respondida con datos · Sin resultados · Aclaración pedida · Conversación · Rechazada (fuera de
      alcance) · Sin permiso · IA no disponible · IA respondió mal (JSON inválido o intención
      inventada) · Error interno.
- [x] Código de error de la IA como campo propio: timeout, sin conexión, cuota agotada (429), API key
      inválida, modelo inexistente, servicio caído (5xx), respuesta bloqueada.

**Tiempos y datos de la llamada**
- [x] Tiempo de la IA, tiempo de la consulta a Odoo y tiempo total, por separado.
- [x] Número de reintentos.
- [x] Proveedor y modelo que respondieron.
- [x] Tokens usados (entrada y salida), que Gemini y Groq informan en cada respuesta.

**Coherencia de las respuestas**
- [ ] Evaluación controlada con el dataset (`run-chatbot-eval.ps1`): métrica principal del
      Capítulo 5.
- [x] Opinión del usuario en el chat: reacciones 👍 / 👎 en la respuesta del bot (Discuss ya las
      tiene), registradas en el log para revisar las respuestas con 👎.

**Panel de análisis en Odoo** (vistas nativas)
- [x] Gráficos: consultas por día, por resultado, por intención y por modelo.
- [x] Tabla dinámica: latencia promedio y máxima por etapa, intención y modelo; porcentaje de cada
      resultado.
- [x] Filtros listos: "IA no disponible", "Lentas (> 5 s)", "Con 👎", "Sin permiso", "Hoy",
      "Esta semana".
- [x] Exportación a Excel para los gráficos de la tesis (exportación nativa de las vistas de Odoo).

**Disponibilidad y retención**
- [x] Disponibilidad del servicio = consultas sin fallo de la IA / total de consultas (se obtiene agrupando por Resultado en Métricas).
- [ ] (Opcional) Tarea programada que pruebe la conexión periódicamente y registre caídas aunque nadie
      use el chat.
- [x] Opción para borrar registros con más de N días (privacidad).

**Pruebas**
- [x] Cada tipo de resultado queda bien clasificado (con la IA simulada).
- [x] Los tiempos por etapa se registran también cuando hay error (el total incluye ambas etapas).
- [x] Una reacción 👍 / 👎 en el chat queda asociada a su registro del log.
- [x] La limpieza por antigüedad borra solo los registros vencidos.

**Implementado en `feature/metricas-y-monitoreo` (versión 18.0.1.5.0)**
- Menú **Chatbot → Métricas** (gráfico, tabla dinámica, lista) y **Chatbot → Auditoría** con los nuevos
  campos, filtros y agrupaciones.
- Ajuste **"Conservar auditoría (días)"** (0 = conservar todo) y tarea diaria de limpieza.
- 14 pruebas nuevas en Odoo (40 en total) y 2 unitarias; verificado también el camino real de las
  reacciones de Discuss y la actualización desde la versión 18.0.1.4.1.
- Los registros creados antes de esta versión quedan sin "Resultado".

### Punto 13: ruta híbrida, consultas flexibles validadas (propuesta de la tutora)
Las preguntas que coinciden con un caso de uso siguen por la **Ruta 1** (consulta estructurada fija,
como hoy). Las demás preguntas de datos van por una **Ruta 2**: la IA arma un plan de consulta en
JSON a partir de un catálogo autorizado, el sistema lo valida contra una lista blanca y lo ejecuta en
el ORM. Ejemplo: "¿Cuántos productos cuestan menos de 100 dólares?" → `product.product`,
`list_price < 100`, contar. Cubre la pregunta de precios, por lo que no hace falta un CU-06 aparte.

**Catálogo autorizado** (implementa la Tabla 6 de la tesis, que hoy no se aplica en el código)
- [ ] Modelos permitidos: `product.product`, `res.partner`, `sale.order`, `account.move`,
      `stock.quant`.
- [ ] Por cada campo: nombre técnico, descripción en español para la IA, tipo y operadores
      permitidos (por ejemplo, `list_price` = "precio de venta"; distinguirlo del costo).
- [ ] Campos sensibles fuera de la lista (RUC/cédula, costo de compra, etc.).
- [ ] Editable por el administrador del chatbot.

**Plan de consulta y validador** (pieza clave de seguridad)
- [ ] Nueva intención `consulta_flexible` con plan JSON: modelo, filtros (campo, operador, valor),
      operación (contar, sumar, promedio, mínimo, máximo, listar), agrupación opcional (una) y orden.
- [ ] Validar: modelo y campos en el catálogo, operador compatible con el tipo, valores del tipo
      correcto, máximo de filtros, límite de 15 resultados al listar. Si algo no cuadra, no se ejecuta.
- [ ] Filtros por nombre de cliente o producto (relación de un nivel); sin cruces complejos.

**Ejecución y respuesta**
- [ ] Convertir el plan en dominio de Odoo y usar `search_count`, `read_group` o `search_read`, con
      los permisos del usuario y la tabla de permisos por consulta (punto 11).
- [ ] Respuesta con plantilla; los números siempre vienen de Odoo, nunca de la IA.
- [ ] Mostrar siempre la interpretación: "Interpreté: productos con precio de venta menor a $100.
      Resultado: 42 productos."
- [ ] Registrar en el log el plan, la ruta usada (1 o 2) y el resultado (punto 12).

**Pruebas**
- [ ] Planes válidos de cada operación (contar, sumar, listar, agrupar).
- [ ] Planes rechazados: modelo no permitido, campo sensible, operador inválido para el tipo, valor de
      tipo incorrecto, demasiados filtros.
- [ ] Respeto de permisos y reglas de registro en la Ruta 2.
- [ ] Consultas de la Ruta 2 en el dataset, con resultado esperado.

### Punto 14: límites conocidos del asistente (para el dataset y la tesis)
Preguntas que el asistente **no** responde, incluso con la ruta híbrida. Deben rechazarse o aclararse
sin inventar una respuesta.
- [ ] **Por diseño (seguridad):** acciones o escritura ("Crea una factura", "Confirma el pedido
      S00045", "Envía la factura por correo"); consultas sin permiso; campos sensibles ("¿Cuál es el
      RUC del cliente X?", "¿Cuál es el costo de compra del casco?").
- [ ] **Por alcance (otros módulos):** nómina ("¿Cuánto gana el vendedor Juan?"), compras ("¿Qué le
      compramos al proveedor X?"), saldos bancarios, CRM.
- [ ] **Por complejidad (varios pasos):** márgenes por producto, comparar conjuntos ("clientes que
      compraron cascos pero nunca filtros"), comparar periodos por vendedor. Listados largos se
      limitan a 15 resultados más el total.
- [ ] **Por naturaleza (no son datos):** predicciones ("¿Cuánto venderemos el próximo mes?"),
      causas ("¿Por qué bajaron las ventas?"), recomendaciones, notas internas o adjuntos.
- [ ] **Fuera del dominio:** clima, poemas, etc. La conversación libre (punto 8) responde con
      amabilidad e indica el alcance.
- [ ] **Decidir:** si la IA puede responder conocimiento general del negocio ("¿Qué es el IVA?") o si
      se limita al alcance del asistente.
- [ ] Incluir ejemplos de cada categoría en el dataset como "rechazar" o "aclarar" (paso 8 del plan).

### Otros
- [ ] Probar el chat completo en la interfaz web con Gemini real (CU-01 a CU-05).
- [x] Fusionar la rama final en `main` (PR #1).
- [ ] Despliegue en la nube (DigitalOcean con el Student Pack, dominio de Namecheap).
