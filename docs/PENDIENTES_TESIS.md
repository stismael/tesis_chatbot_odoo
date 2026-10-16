# Cambios pendientes en el documento de la tesis

Lista de correcciones para el documento `TESIS_ISMAEL_CALLE_CAP3.docx`, según la revisión del
documento frente al código del repositorio. Marcar cada casilla al aplicarla.

Rama de referencia del código: `feature/cu05-stock-facturacion-producto`.

---

## 1. Alinear el Capítulo 3 con el código (prioridad alta)

### Ya implementado en el código: actualizar el documento

- [ ] **3.4.2, ejemplo de dominio de `account.move.line`:** cambiar `("display_type", "=", False)` por
      `("display_type", "=", "product")`. En Odoo 18 las líneas de producto tienen
      `display_type = "product"`; con `False` la consulta no devuelve nada. Dominio real usado:
      ```python
      [
          ("product_id", "=", product.id),
          ("display_type", "=", "product"),
          ("move_id.move_type", "=", "out_invoice"),
          ("move_id.state", "=", "posted"),
          ("move_id.invoice_date", ">=", date_from),   # opcional
          ("move_id.invoice_date", "<=", date_to),     # opcional
      ]
      ```
- [ ] **3.4.2, ejemplo de búsqueda de producto:** reemplazar el ejemplo con `"|"` y `limit=1`. Contradice
      la Tabla 17 ("Varias coincidencias → mostrar coincidencias"), porque toma la primera sin avisar.
      El código real busca primero por código exacto, luego por nombre, y si hay más de una
      coincidencia responde con la lista para que el usuario precise.
- [ ] **3.4.3, último párrafo:** cambiar "display_type vacío" por "display_type igual a product".
- [ ] **Tabla 16:** los nombres de las funciones no existen en el código. Usar los reales:

      | Intención | Función real |
      |---|---|
      | consultar_factura | `services/handlers/factura.py → handle()` |
      | consultar_stock | `services/handlers/stock.py → handle()` |
      | consultar_ventas_cliente | `services/handlers/ventas.py → handle()` |
      | consultar_vendedor_cliente | `services/handlers/vendedor.py → handle()` |
      | consultar_stock_facturacion_producto | `services/handlers/stock_facturacion.py → handle()` |
      | fuera_de_alcance | Mensaje fijo del orquestador (`OUT_OF_SCOPE_MSG`), sin handler |

      Alternativa: dejar nombres descriptivos y añadir una nota de que en el código cada caso de uso
      es un *handler* registrado en `HANDLER_MAP`.
- [ ] **3.4.2:** el texto dice que se usan `search()`, `search_read()`, `browse()` o `read_group()`.
      El código solo usa `search()` y lectura de campos del recordset. Ajustar.
- [ ] **Tabla 8 (CU-02), fila Resultado:** cambiar "Producto, ubicación y cantidad disponible" por
      "Producto, ubicación, existencia, cantidad reservada y cantidad disponible para la venta".
- [ ] **Tabla 11 (CU-05), fila Resultado:** "Producto, existencia, cantidad reservada, cantidad
      disponible para la venta, cantidad facturada, número de facturas y valor facturado".
- [ ] **Tablas 9 y 15 (CU-03):** la entrada mínima es `customer_name` **o** `product_name` **o**
      `product_code`. El código acepta consultas solo por producto ("¿cuántas ventas hay del CAS-001?").
- [ ] **3.3.2 o 3.3.4, fechas:** añadir que `date_from` y `date_to` van en formato AAAA-MM-DD, que la
      fecha actual se envía al LLM para resolver periodos relativos ("este mes", "julio") y que el
      validador descarta fechas no válidas.
- [ ] **Tabla 6 y 3.4.3, "listas blancas":** el código no tiene una lista blanca de campos que se
      verifique en tiempo de ejecución; cada handler lee solo campos fijos. Redactar así: "cada función
      interna accede únicamente a los campos definidos en la Tabla 6", en lugar de "listas blancas".
- [ ] **2.5.3:** quitar la mención a **Pydantic**; el proyecto no lo usa. La validación está en
      `services/validator.py` (validación de intención, entidades requeridas, estados y fechas).
- [ ] **3.1.1:** la frase sobre reglas de registro ahora es correcta: el módulo define reglas para que
      cada usuario vea solo sus sesiones, mensajes y consultas, y el administrador del chatbot vea todo.
      Se puede mencionar como parte de la seguridad.
- [ ] **Interfaz conversacional:** el Capítulo 3 no menciona que el chat funciona dentro de
      **Discuss** (mensaje directo con el contacto "Asistente ERP", similar a OdooBot, con `/help`).
      Añadir en 3.1.2 (Tabla 2) el módulo Conversaciones/Discuss (`mail`, `mail_bot`) y describir la
      interfaz.

### Todavía no implementado en el código: decidir

- [ ] **Tabla 13, `intencion_desconocida`:** se reemplazará por la intención `conversacion` (ver
      sección 1.1 de este archivo). Esperar a que esté implementada en el código.
- [ ] **Tablas 14 y 15, entidad `order_state`:** no existe en el código. Quitarla o implementarla.
- [ ] **Tabla 5, pedidos de venta (~1.000):** el generador define `TARGET_SALE_ORDERS = 350`. Cambiar
      la cifra, o subir el valor en el generador.

### Dataset de evaluación (3.5)

- [ ] **3.5.1 y Tabla 18:** el campo se llama `expected_result_contains` (lista de textos que debe
      contener la respuesta), no `expected_result`. Actualizar el ejemplo JSON y la tabla. Hay además
      un campo `expected_status` en las consultas de aclaración y rechazo.
- [ ] **Tamaño del dataset:** 56 consultas: 31 correctas, 10 incompletas, 4 ambiguas y 11 fuera de
      alcance (incluye las 5 de CU-05, Q052 a Q056). Contar de nuevo con el archivo final antes de
      citarlo.
- [ ] **Fase 4 (1.3):** el dataset no tiene "operación estructurada esperada". Quitarlo del texto o
      agregarlo al dataset.

---

## 1.1 Cambios planificados en el código que afectarán el documento

Aplicar cuando cada cambio esté implementado (ver `SEGUIMIENTO_CAMBIOS.md`, puntos 7 a 10).

### Arquitectura híbrida: conversación libre, datos solo desde Odoo (punto 8)
- [ ] **Describir la arquitectura como híbrida** (3.3, 3.4 y la introducción del Capítulo 3): la IA
      redacta libremente las respuestas que no involucran datos del negocio (saludos, agradecimientos,
      capacidades, rechazos), pero todo dato del ERP pasa por una consulta estructurada y validada
      sobre el ORM. Frase guía: *"la IA puede decir lo que quiera, excepto datos del negocio: esos solo
      los puede obtener pidiéndolos al sistema"*.
- [ ] **Tabla 13:** reemplazar `intencion_desconocida` por `conversacion` (saludos, agradecimientos,
      preguntas sobre lo que puede hacer el asistente y charla general).
- [ ] **3.3.3, esquema JSON:** añadir el campo `reply` (texto redactado por la IA, solo para
      `conversacion` y `fuera_de_alcance`) y el estado `chat`. Incluir un ejemplo de saludo.
- [ ] **3.3.4, validación:** añadir el control anti-invención (una respuesta conversacional con montos,
      números de factura o códigos de producto se descarta) y el límite de longitud de `reply`.
- [ ] **3.2.6 y Tablas 12 y 23:** las respuestas fuera de alcance las redacta la IA (explica por qué no
      puede y qué sí puede hacer); el mensaje fijo queda solo como respaldo.
- [ ] **Tabla 17:** fila "Consulta no relacionada" → la IA responde con sus palabras e indica el
      alcance.
- [ ] **3.5.2:** añadir la categoría de consultas de conversación al dataset.

### Velocidad (punto 7)
- [ ] **2.4.6 o Capítulo 5, tiempo de respuesta:** distinguir el tiempo de la IA y el de la consulta a
      Odoo (se registrarán por separado en el log).
- [ ] **Capítulo 4:** documentar la configuración del modelo (sin "pensamiento" para Gemini 2.5,
      formato JSON exigido con esquema, timeout y reintentos) y por qué.

### Selección del modelo (punto 9)
- [ ] **Capítulo 4 (configuración):** el modelo se elige de un desplegable filtrado por proveedor,
      alimentado por la lista que publica el proveedor, en lugar de escribirlo a mano.

### Respuestas de datos redactadas por la IA (punto 10, opcional)
- [ ] Si se implementa: describirlo como opción configurable con verificación de que los números de la
      respuesta coinciden con los datos de Odoo, sin contradecir "sin inventar valores" (3.2.1).
- [ ] **Capítulo 5:** experimento plantilla vs. redacción por IA (exactitud, latencia, naturalidad).

### Permisos de usuario (punto 11)
- [ ] **3.1.1 y 3.4.3:** explicar con evidencia que el chatbot respeta los permisos de Odoo: cada
      consulta corre con el usuario autenticado, así que los derechos de acceso y las reglas de
      registro se aplican igual que en la interfaz. Ejemplo verificado: un vendedor que solo ve sus
      documentos obtiene 0 unidades facturadas donde el administrador obtiene 137.
- [ ] **Tabla 17:** añadir la fila "Usuario sin permiso" → mensaje en español sin detalles técnicos.
- [ ] Mencionar que las respuestas se basan solo en los documentos a los que el usuario tiene acceso.
- [ ] Documentar la decisión sobre inventario (Odoo permite a todo usuario interno leer existencias).

### Defensa ante el tribunal
- [ ] Preparar la justificación del diseño de dominio cerrado e híbrido (exactitud, seguridad,
      auditabilidad, evaluación y alcance del TIC), citando Bi et al. (2025), Béchard y Ayala (2024),
      Mishra et al. (2026) y Pandey et al. (2024).
- [ ] **Trabajo futuro:** agente con *function calling* que reutilice los handlers como herramientas
      sin perder el validador ni los permisos; operaciones de escritura con confirmación del usuario.

---

## 2. Contradicciones internas

- [ ] **Datos demo:** la Introducción y la Fase 2 dicen "datos demo de Odoo y datos sintéticos";
      3.1.1 y el Capítulo 4 dicen base limpia (`--without-demo=all`). Unificar a "base limpia con
      datos sintéticos".
- [ ] **Objetivo específico 1:** dice "revisión sistemática". Cambiar a "revisión de literatura" o
      añadir un flujo tipo PRISMA en 2.5.1 (84 registros → descartados por título/resumen → por texto
      completo → 12 seleccionados, con motivos de exclusión).
- [ ] **2.5.1, artículo número 84:** explicar cómo se encontró si no salió en las dos búsquedas
      (búsqueda manual, referencias de otro artículo, etc.).
- [ ] **"E2"** aparece en las Fases 3 y 4 sin definirse. Definirlo o reemplazarlo por "la Fase 2".
- [ ] **Fase 3:** promete pruebas unitarias y de integración al cierre de cada sprint. Ajustar a lo
      que de verdad se hizo (script de pruebas del validador y pruebas en Odoo).

---

## 3. Errores técnicos y de fuentes

- [ ] **2.2.1:** "Odoo 18 es la última versión mayor" ya no es cierto (Odoo 19 salió en septiembre de
      2025). Cambiar a "Odoo 18, versión utilizada en este trabajo…" y citar las notas de versión
      oficiales en lugar del blog de Scorpora.
- [ ] **2.2.3:** `name_get()` ya no existe desde Odoo 17 (se reemplazó por `display_name` /
      `_compute_display_name`). Quitarlo o actualizarlo. Preferir la documentación oficial del ORM
      sobre el blog de Kalariya (CandidRoot).
- [ ] **2.4.6, tiempo de respuesta:** se cita Wang et al. (2026), que trata de *prompt engineering* en
      salud. Buscar una fuente sobre latencia o tiempo de respuesta en chatbots.
- [ ] **2.5.3:** Huang et al. (2025, CRMArena) aparece como trabajo Text-to-SQL, pero evalúa agentes
      en tareas de CRM. Moverlo al grupo correcto y escribir "Huang et al.".
- [ ] **2.4.3:** se cita "Mishra et al. (2022)", pero en las referencias solo está Mishra et al. (2026).

---

## 4. Tabla 1 (trabajos relacionados)

- [ ] Leer los 12 artículos (casi todos tienen DOI) y completar los datos reales: modelo usado,
      dataset y métricas.
- [ ] Quitar las frases "no se detalla en los metadatos revisados" y "no se detallan en la tabla
      bibliográfica proporcionada". Si un artículo de verdad no reporta un dato, escribir
      "No reportado".

---

## 5. Referencias y citas (APA 7)

- [ ] Corregir **"Oddo" → "Odoo"** en el texto (2.2.2, 2.3.6) y en las tres entradas de referencias.
- [ ] Añadir las entradas que faltan o unificar su forma:
  - [ ] Lewis (2018)
  - [ ] Sauro y Lewis (2016)
  - [ ] Mishra et al. (2022), o corregir la cita a 2026
  - [ ] Odoo (2024): en la lista solo está "Oddo (2024)"
  - [ ] "Organisation for Economic Co-operation and Development (2021)" vs. "OECD" en la lista: usar
        la misma forma
  - [ ] Arteaga et al. (2022) → la referencia es Pionce Arteaga et al.
  - [ ] IBM (2024) citado para chatbots empresariales: la página citada es sobre NLP; la de chatbots
        es Finio (2026)
- [ ] "Béchard y Ayala (2024)" en el texto vs. "Ayala, O., & Bechard, P." en la lista: el orden de
      autores debe coincidir.
- [ ] Citas mal formadas:
  - [ ] "Según (Balić et al., 2022) (2022)" → "Según Balić et al. (2022)"
  - [ ] "organizaciones(SAP, 2026)" → falta un espacio antes del paréntesis
  - [ ] "(Sai Kiran Reddy Malikireddy & Snigdha Tadanki, 2022)" → "(Malikireddy & Tadanki, 2022)";
        en la lista "Malikireddy, S. K. R., & Tadanki, S."
- [ ] Completar referencias sin revista, editorial ni URL: Bawa (2024), de Araújo y Silva (2023),
      Himawan (2024).
- [ ] Verificar contra la fuente: Quamar et al. (2022) repite "Lei, C., & Lei, C."; el año de
      Katsogiannis-Meimarakis et al. no parece coincidir con su DOI.

---

## 6. Formato y plantilla

- [ ] Numeración del Capítulo 1: hay dos "1.1" (Problemática y Justificación); Objetivos, Metodología
      y Estructura quedan desfasados.
- [ ] Tildes: "Capitulo dos" → "Capítulo dos"; "capitulo 1" → "capítulo 1".
- [ ] 2.5.2 y 2.5.3 tienen estilo de título de nivel 2; deben ser nivel 3. Borrar los párrafos vacíos
      con estilo de título alrededor de la Tabla 1.
- [ ] Página de aprobación:
  - [ ] "Loja" vs. "CUENCA" en la carátula
  - [ ] "en calidad de director" → "directora"
  - [ ] "Chicaiza Espinoza" (carátula) vs. "Espinosa" (aprobación): unificar
- [ ] Añadir figuras al Capítulo 3 (hoy no hay ninguna):
  - [ ] Diagrama de arquitectura: Discuss → orquestador → LLM → validador → handler ORM → respuesta
  - [ ] Diagrama de flujo o de secuencia de una consulta
- [ ] Pendientes de plantilla: dedicatoria, agradecimiento, resumen, abstract, palabras clave, nombres
      de capítulos en la declaración de autoría y C.I. de la directora.
