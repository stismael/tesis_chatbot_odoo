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
| `feature/metricas-y-monitoreo` | Punto 12 (métricas y monitoreo); conviene hacerlo antes del 7 | Por crear |
| `feature/mejoras-llm-modelo-y-latencia` | Puntos 7 a 10 (velocidad, conversación, modelos, redacción) | Por crear |

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
- [ ] Desactivar el "pensamiento" de Gemini 2.5 (`thinkingConfig: {thinkingBudget: 0}`); la tarea es
      clasificar y extraer datos, no razonar.
- [ ] Exigir el formato con `responseSchema` (Gemini) y `json_object` (Groq) para evitar JSON inválido.
- [ ] Timeout de ~20 s y un solo reintento (hoy 45 s × 3 intentos más pausas: más de 2 minutos).
- [ ] Revisar el caso "Hola" sin respuesta con el registro de Chatbot → Consultas (estado, error,
      latencia).

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
- [ ] Al cambiar de proveedor, reemplazar **siempre** el modelo por el recomendado del nuevo proveedor
      (Gemini → `gemini-2.5-flash`; Groq → `llama-3.3-70b-versatile`), sin adivinar por el nombre.

**Catálogo de modelos en Odoo**
- [ ] Tabla de modelos por proveedor (proveedor, ID, nombre, descripción, límite de tokens,
      disponible) y botón **"Actualizar modelos"**.
- [ ] La actualización **sincroniza, no borra**, y solo toca el proveedor consultado:
  - modelo nuevo → se agrega;
  - modelo existente → se actualizan sus datos;
  - modelo que ya no aparece → se marca **"No disponible"** y sale del desplegable;
  - modelo que vuelve a aparecer → se marca disponible otra vez.
- [ ] Guardar la fecha de la última actualización y mostrarla en Ajustes.
- [ ] (Opcional) Tarea programada que actualice el catálogo una vez por semana.
- [ ] El campo "Modelo" pasa a ser un **desplegable filtrado por el proveedor elegido**, solo con
      modelos de texto disponibles y el recomendado marcado; así no se puede elegir un modelo de otro
      proveedor.
- [ ] Filtrar también la lista de Groq: hoy muestra todo su catálogo, incluidos modelos que no son
      de texto (por ejemplo, Whisper para audio).
- [ ] Leer todas las páginas del listado de Gemini (hoy pide hasta 100 y no sigue `nextPageToken`).
- [ ] Mostrar los datos que entrega la API (nombre, descripción, límite de tokens) y un enlace a la
      página de precios del proveedor, ya que la API no informa si un modelo es gratuito.
- [ ] Aviso en Ajustes si el modelo configurado quedó **"No disponible"**: "El modelo configurado ya
      no está disponible en <proveedor>. Elige otro."

**Validación al guardar la configuración**
- [ ] Al pulsar **Guardar**, si cambió el proveedor, la API key o el modelo, probar la conexión
      automáticamente:
  - si funciona, guardar y mostrar "Conexión verificada el <fecha> con <modelo>";
  - si falla, no guardar y explicar el motivo (API key inválida, modelo inexistente en el proveedor,
    sin conexión, cuota agotada).
- [ ] No probar cuando solo cambian otros datos (temperatura, timeout) ni al **desactivar** el
      chatbot, para que una caída del proveedor no impida apagar el asistente.
- [ ] Validar también que el modelo pertenezca al proveedor elegido ("El modelo 'qwen/qwen3-32b' no
      pertenece a Google Gemini").
- [ ] Mantener el botón **"Probar conexión"** para verificar en cualquier momento sin guardar.

**Fallos después de guardar (fuera del control del sistema)**
- [ ] Indicador en Ajustes con el último error del proveedor y su fecha.
- [ ] (Opcional) **Modelo de respaldo**: si el principal falla (caída, cuota agotada), intentar con
      otro configurado, incluso de otro proveedor, y registrar en el log qué modelo respondió.

**Pruebas**
- [ ] Cambio Groq → Gemini con `llama-3.3-70b-versatile`, `openai/gpt-oss-120b`, `qwen/qwen3-32b` y
      `deepseek-r1-distill-llama-70b`: el campo debe quedar en `gemini-2.5-flash`. Y el cambio
      inverso Gemini → Groq.
- [ ] Sincronización del catálogo: agregar, actualizar, marcar "No disponible" y reactivar.
- [ ] El desplegable solo muestra modelos disponibles del proveedor elegido.
- [ ] Guardar con conexión fallida no guarda y muestra el motivo; desactivar el chatbot guarda sin
      probar.
- [ ] (Si se implementa) el modelo de respaldo responde cuando el principal falla.

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
- [ ] **Mensaje técnico en inglés al usuario.** Sin permiso de Contabilidad o Ventas, el chat muestra
      el error crudo de Odoo ("You are not allowed to access 'Journal Entry'… groups: Invoicing/
      Administrator"). Debe responder en español y sin detalles técnicos, por ejemplo "No tienes
      permiso para consultar facturas. Pide acceso al administrador.", y registrar el detalle solo
      en el log. Causa: `AccessError` hereda de `UserError` y el orquestador muestra su texto.
- [ ] **Registros que existen pero el usuario no puede ver.** Un vendedor que solo ve sus propios
      documentos recibe "No encontré la factura INV/…" o "No hay pedidos confirmados", aunque existan.
      Cambiar a "No encontré… o no tienes acceso a ese registro" (sin confirmar que existe).
- [ ] **Totales parciales sin aviso.** En CU-05 el administrador ve 137 unidades facturadas en 29
      facturas y el vendedor ve 0 en 0, porque Odoo filtra las facturas que puede ver. Es correcto
      por seguridad, pero la respuesta debe aclarar "según los documentos a los que tienes acceso"
      cuando el usuario no tiene acceso total.
- [ ] **Permiso del módulo de cada consulta (decidido).** Odoo reparte la lectura entre módulos de
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

  - [ ] **Implementación (opción A, decidida): tabla editable** en *Chatbot → Configuración →
        Permisos por consulta*, una fila por intención con los grupos exigidos (todos deben
        cumplirse). Se carga con valores por defecto al instalar (`noupdate`) y el administrador del
        chatbot puede cambiarla sin tocar código. Una fila sin grupos usa solo los permisos de Odoo.
  - [ ] **Grupos mínimos por defecto** (nivel Usuario; el Administrador de cada módulo incluye al
        Usuario en Odoo 18, así que pasa automáticamente con `has_group`):

        | Consulta | Grupo técnico mínimo | Nombre en Ajustes → Usuarios |
        |---|---|---|
        | CU-01 Facturas | `account.group_account_invoice` | Facturación / Contabilidad: Facturación |
        | CU-02 Stock | `stock.group_stock_user` | Inventario: Usuario |
        | CU-03 Ventas | `sales_team.group_sale_salesman` | Ventas: Usuario, solo documentos propios |
        | CU-04 Vendedor asignado | `sales_team.group_sale_salesman` | Ventas: Usuario, solo documentos propios |
        | CU-05 Stock + facturación | `stock.group_stock_user` y `account.group_account_invoice` | Inventario: Usuario y Facturación |

  - [ ] Caso especial: el grupo oculto `account.group_account_readonly` (solo lectura contable) no
        incluye a Facturación; queda fuera por defecto y el administrador puede agregarlo a la fila.
  - [ ] **Dónde va el control:** en el orquestador, después del validador y antes de ejecutar el
        handler. Es solo del chatbot: no modifica ningún permiso de Odoo ni afecta otras pantallas.
        Se evalúa por usuario y en cada mensaje, con los grupos que tenga en ese momento.
  - [ ] Sin el grupo: no se consulta nada y se responde en español, por ejemplo "No tienes permiso
        para consultar inventario. Pide acceso al administrador."
  - [ ] Registrar el intento rechazado en el log con estado `forbidden` ("sin permiso") para
        auditoría.
  - [ ] Las reglas de registro de Odoo se siguen aplicando encima (un vendedor ve solo sus documentos).
  - [ ] Seguridad de la tabla: el administrador del chatbot la edita; los usuarios solo la leen.
  - [ ] (Opcional) `/help` muestra solo los ejemplos de las consultas que el usuario puede hacer.
- [ ] Pruebas por perfil y por consulta: usuario interno sin grupos, solo Inventario, vendedor (solo
      sus documentos), usuario de Facturación y administrador; con la opción activada y desactivada.

### Punto 12: métricas y monitoreo (observación de la tutora)
Objetivo: saber cuándo el chatbot responde bien, cuándo no, cuándo la IA no está disponible y dónde
se demora. Hoy *Chatbot → Auditoría de consultas* guarda la latencia total, un "éxito" sí/no y el
error como texto libre, lo que no basta para analizar.

**Resultado clasificado de cada mensaje** (lista fija, para filtrar y agrupar)
- [ ] Respondida con datos · Sin resultados · Aclaración pedida · Conversación · Rechazada (fuera de
      alcance) · Sin permiso · IA no disponible · IA respondió mal (JSON inválido o intención
      inventada) · Error interno.
- [ ] Código de error de la IA como campo propio: timeout, sin conexión, cuota agotada (429), API key
      inválida, modelo inexistente, servicio caído (5xx), respuesta bloqueada.

**Tiempos y datos de la llamada**
- [ ] Tiempo de la IA, tiempo de la consulta a Odoo y tiempo total, por separado.
- [ ] Número de reintentos.
- [ ] Proveedor y modelo que respondieron.
- [ ] Tokens usados (entrada y salida), que Gemini y Groq informan en cada respuesta.

**Coherencia de las respuestas**
- [ ] Evaluación controlada con el dataset (`run-chatbot-eval.ps1`): métrica principal del
      Capítulo 5.
- [ ] Opinión del usuario en el chat: reacciones 👍 / 👎 en la respuesta del bot (Discuss ya las
      tiene), registradas en el log para revisar las respuestas con 👎.

**Panel de análisis en Odoo** (vistas nativas)
- [ ] Gráficos: consultas por día, por resultado, por intención y por modelo.
- [ ] Tabla dinámica: latencia promedio y máxima por etapa, intención y modelo; porcentaje de cada
      resultado.
- [ ] Filtros listos: "IA no disponible", "Lentas (> 5 s)", "Con 👎", "Sin permiso", "Hoy",
      "Esta semana".
- [ ] Exportación a Excel para los gráficos de la tesis.

**Disponibilidad y retención**
- [ ] Disponibilidad del servicio = consultas sin fallo de la IA / total de consultas.
- [ ] (Opcional) Tarea programada que pruebe la conexión periódicamente y registre caídas aunque nadie
      use el chat.
- [ ] Opción para borrar registros con más de N días (privacidad).

**Pruebas**
- [ ] Cada tipo de resultado queda bien clasificado (con la IA simulada).
- [ ] Los tiempos por etapa suman el total y se registran también cuando hay error.
- [ ] Una reacción 👍 / 👎 en el chat queda asociada a su registro del log.
- [ ] La limpieza por antigüedad borra solo los registros vencidos.

### Otros
- [ ] Probar el chat completo en la interfaz web con Gemini real (CU-01 a CU-05).
- [x] Fusionar la rama final en `main` (PR #1).
- [ ] Despliegue en la nube (DigitalOcean con el Student Pack, dominio de Namecheap).
