# Seguimiento de cambios del prototipo

Registro de las correcciones y mejoras del código. Marcar `[x]` cuando un punto quede terminado.
Los cambios pendientes en el **documento de la tesis** están en
[`PENDIENTES_TESIS.md`](PENDIENTES_TESIS.md).

## Ramas

| Rama | Contenido | Estado |
|---|---|---|
| `claude/repository-analysis-84h0jn` | Totales de ventas, privacidad, test corregido | Subida, sin fusionar |
| `feature/cu05-stock-facturacion-producto` | CU-05, stock unificado, lista de la tesis | Subida, sin fusionar |
| `fix/correcciones-handlers-y-pruebas-odoo` | Correcciones del punto 1 y pruebas en Odoo | Subida, sin fusionar |

Cada rama parte de la anterior, así que la última contiene todo. Basta con fusionar la última en
`main`.

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
- [ ] Decidir sobre `intencion_desconocida`: implementar o quitar de la tesis.
- [ ] Decidir sobre `order_state` (cotización, pedido, cancelado): implementar (recomendado) o quitar.
- [ ] Volumen de pedidos del generador: 350 en el código vs. ~1.000 en la tesis.

### Punto 5: la llamada al LLM no debe bloquear el chat
- [ ] Procesar la respuesta fuera de la transacción del mensaje (cola, cron o `postcommit`).
- [ ] Revisar reintentos y timeout para que no superen el límite del worker de Odoo.

### Punto 6: dataset de evaluación
- [ ] Más consultas ambiguas (hoy solo 4).
- [ ] Etiquetas más estrictas: revisar `clarify_or_execute`, `clarify_or_not_found` y
      `reject_or_clarify`, que aceptan casi cualquier resultado.
- [ ] Más variedad: errores de tipeo, preguntas encadenadas y cambios de tema.
- [ ] Ejecutar `run-chatbot-eval.ps1` con la API key y guardar resultados por modelo.

### Otros
- [ ] Probar el chat completo en la interfaz web con Gemini real (CU-01 a CU-05).
- [ ] Fusionar la rama final en `main`.
- [ ] Despliegue en la nube (DigitalOcean con el Student Pack, dominio de Namecheap).
