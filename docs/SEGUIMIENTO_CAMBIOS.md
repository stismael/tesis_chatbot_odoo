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
Va primero, porque con el punto 8 los saludos también llaman a la IA.
- [ ] Registrar en el log, por separado, el tiempo de la IA y el de la consulta a Odoo (métrica para
      el Capítulo 5 y para saber dónde está la demora).
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

### Punto 9: selección del modelo
- [ ] Botón "Actualizar modelos" que consulta al proveedor y guarda la lista en Odoo.
- [ ] Desplegable en lugar del campo de texto, filtrado por proveedor, solo modelos de texto, con el
      recomendado marcado.
- [ ] Al cambiar de proveedor, elegir automáticamente el modelo recomendado de ese proveedor.
- [ ] Filtrar también la lista de Groq: hoy muestra todo su catálogo, incluidos modelos que no son
      de texto (por ejemplo, Whisper para audio).
- [ ] Avisar en Ajustes si el modelo configurado ya no aparece en el catálogo del proveedor (por
      ejemplo, si lo retiraron), en lugar de que el chat falle sin explicación.
- [ ] Leer todas las páginas del listado de Gemini (hoy pide hasta 100 y no sigue `nextPageToken`).
- [ ] Mostrar en el desplegable los datos que sí entrega la API (nombre, descripción, límite de
      tokens) y un enlace a la página de precios del proveedor, ya que la API no informa si un modelo
      es gratuito.
- [ ] Pruebas del filtrado y de la lista.

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

### Otros
- [ ] Probar el chat completo en la interfaz web con Gemini real (CU-01 a CU-05).
- [x] Fusionar la rama final en `main` (PR #1).
- [ ] Despliegue en la nube (DigitalOcean con el Student Pack, dominio de Namecheap).
