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

- [ ] **Tabla 13, `intencion_desconocida`:** reemplazarla por la intención `conversacion`, ya
      implementada en el código (ver sección 1.1 de este archivo).
- [ ] **Tablas 14 y 15, entidad `order_state`:** ya implementada en el código (valores `cotizacion`,
      `pedido`, `cancelado`; sin valor se consultan los pedidos confirmados). Revisar que las tablas
      usen esos valores.
- [ ] **Memoria de la sesión (sección de memoria corta):** describir la regla: un seguimiento solo
      hereda el sujeto que falta (cliente, producto o factura); una aclaración conserva lo ya dicho.
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
- [ ] **Capítulo 4:** documentar la configuración del modelo (sin "pensamiento" para Gemini 2.5,
      formato JSON exigido con esquema, timeout y reintentos) y por qué.
- [ ] **Capítulo 5:** comparar los tiempos antes y después de estas mejoras, con los datos del punto 12.

### Métricas y monitoreo (punto 12, observación de la tutora)
- [ ] **2.4.6, métricas:** añadir las métricas de operación: tasa por tipo de resultado,
      disponibilidad del servicio (consultas sin fallo de la IA / total), latencia por etapa (IA,
      consulta a Odoo, total) y satisfacción del usuario (👍 / 👎).
- [ ] **Capítulo 4:** describir el log clasificado (resultado, código de error, tiempos por etapa,
      proveedor, modelo, tokens) y el panel de análisis en Odoo (gráficos, tabla dinámica, filtros).
- [ ] **Capítulo 5:** presentar dos fuentes de métricas: **evaluación controlada** con el dataset
      (precisión de intención, de entidades y de ejecución) y **monitoreo en uso real** con el log
      (resultados, latencias, disponibilidad, satisfacción).
- [ ] Mencionar la retención limitada del log como medida de privacidad.

### Proveedores de IA (aclaración pedida por la tutora)
- [ ] **Capítulo 2 o 4:** distinguir tres roles: desarrollador del modelo (Google, Meta, OpenAI,
      Anthropic, Mistral), proveedor de la API o de inferencia (Google AI Studio/Vertex AI, Groq,
      OpenAI, Azure, AWS Bedrock) y agregadores (OpenRouter, Together AI, Hugging Face).
- [ ] Indicar que el prototipo se conecta directamente a dos proveedores de inferencia: **Google AI
      Studio** (modelos Gemini, desarrollados por Google) y **Groq** (modelos abiertos como Llama, de
      Meta). La lista de modelos disponibles la entrega cada proveedor por su API de listado
      (`models.list` de Gemini y *List models* de Groq), se consulta en tiempo real al pulsar "Listar
      modelos" y no incluye precios: los límites gratuitos se consultan en las páginas de precios.
- [ ] Justificar la elección: cuota gratuita suficiente para un prototipo académico, baja latencia
      (familia Flash de Gemini, inferencia rápida de Groq) y salida JSON nativa.

### Selección y validación del modelo (punto 9)
- [ ] **Capítulo 4 (configuración):** el modelo se elige de un desplegable filtrado por proveedor,
      alimentado por el catálogo que publica el proveedor, en lugar de escribirlo a mano. Explicar que
      el catálogo se sincroniza (agrega, actualiza y marca como no disponibles los modelos retirados,
      sin borrarlos).
- [ ] **Validación de la configuración:** al guardar se prueba la conexión si cambió el proveedor, la
      API key o el modelo; una configuración que no funciona no se guarda.
- [ ] **Separar dos tipos de fallo:** los de configuración se detectan al guardar; los externos
      (caída del proveedor, sin internet, cuota agotada) se manejan en el chat con reintentos,
      mensajes claros y, si se implementa, un modelo de respaldo.

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
- [ ] **Nueva tabla en el Capítulo 3: permisos por caso de uso**, con el grupo mínimo de cada
      consulta: CU-01 Facturación; CU-02 Inventario / Usuario; CU-03 y CU-04 Ventas / Usuario (solo
      documentos propios); CU-05 Inventario / Usuario y Facturación. Indicar que los administradores
      de cada módulo pasan porque en Odoo el Administrador incluye al Usuario.
- [ ] **Describir el control como una capa adicional** (3.4): tabla editable *Permisos por consulta*,
      evaluada por usuario y en cada mensaje, después del validador y antes de consultar. Complementa
      los permisos de Odoo, no los reemplaza ni los modifica; nunca da más acceso que Odoo.
- [ ] **Diagrama de defensa en profundidad:** validador de la salida de la IA → control por rol del
      asistente → permisos de Odoo (derechos de acceso y reglas de registro).
- [ ] **Justificación (mínimo privilegio)** con estos argumentos:
  - El chatbot es un nuevo canal de acceso: facilita llegar a los datos, así que el control debe
    acompañar esa facilidad.
  - Odoo permite lecturas cruzadas para integrar pantallas (por ejemplo, cualquier usuario interno lee
    existencias para ver disponibilidad en una cotización; Inventario lee pedidos de venta), no para
    dar acceso de negocio. El asistente responde preguntas de negocio y aplica roles funcionales.
  - No modifica Odoo (compatible con actualizaciones), es configurable sin programar, es auditable
    (intentos rechazados en el log) y está probado por perfil.
  - Evidencia verificada en Odoo 18: regla `access_stock_quant_all` (lectura de `stock.quant` para
    todo usuario interno) y el ejemplo de CU-05 (administrador 137 unidades facturadas, vendedor 0).
- [ ] **Referencias para la justificación** (verificar cada una antes de citarla):
  - OWASP Top 10 for LLM Applications 2025, LLM06 "Excessive Agency".
  - ISO/IEC 27001:2022, Anexo A: 5.15 Control de acceso y 8.3 Restricción del acceso a la información.
  - NIST SP 800-53 Rev. 5, AC-6 "Least Privilege".
  - Ley Orgánica de Protección de Datos Personales del Ecuador (2021), por los datos de contacto del
    vendedor en CU-04.
  - Ya citadas: Pandey et al. (2024), Mishra et al. (2026), European Data Protection Board (2025).
- [ ] **Preguntas probables y respuestas:** "¿por qué no bastan los permisos de Odoo?" (lecturas
      cruzadas, ejemplo de existencias); "¿no es redundante?" (solo restringe, nunca amplía); "¿y si la
      empresa quiere que ventas vea stock?" (se agrega el grupo en la tabla, sin código).

### Ruta híbrida: consultas flexibles validadas (punto 13, propuesta de la tutora)
- [ ] **Arquitectura (3.3 y 3.4):** describir las dos rutas: Ruta 1 (casos de uso con consulta
      estructurada fija) y Ruta 2 (plan de consulta en JSON generado por la IA a partir de un
      catálogo autorizado, validado contra lista blanca y ejecutado en el ORM).
- [ ] **Tabla 6:** pasa a ser el catálogo real de la Ruta 2 (modelos, campos, descripción, tipo y
      operadores permitidos), con lo que 3.4.3 ("listas blancas") queda respaldado por el código.
- [ ] **Nuevo esquema JSON del plan** en 3.3.3 (modelo, filtros, operación, agrupación, orden) y su
      validación en 3.3.4.
- [ ] **Diagrama de flujo** de la clasificación: caso de uso → Ruta 1; otra consulta de datos →
      Ruta 2; charla → conversación; prohibido → rechazo.
- [ ] **Justificación con la literatura ya citada:** Morshed et al. (2026) (inyección del esquema en
      el prompt), Jarin et al. (2024) (lenguaje natural a JSON), Elder et al. (2026) (lenguaje
      natural a API) y Ma et al. (2025) (validación semántica). Posicionarla como punto medio entre
      intenciones cerradas y Text-to-SQL, sin SQL libre.
- [ ] **Capítulo 5:** comparar Ruta 1 y Ruta 2 en precisión, latencia y errores.

### Limitaciones (punto 14)
- [ ] **Nueva sección de limitaciones en el Capítulo 5**, con ejemplos por categoría:
  - **Por diseño:** escritura, sin permiso, campos sensibles. Son decisiones de seguridad, no fallas.
  - **Por alcance:** módulos no incluidos (nómina, compras, bancos, CRM); se amplían agregando
    modelos al catálogo.
  - **Por complejidad:** cálculos de varios pasos (márgenes, comparación de conjuntos o periodos).
  - **Por naturaleza:** predicciones, análisis de causas, recomendaciones, texto libre y adjuntos.
  - **Fuera del dominio:** temas no comerciales.
- [ ] Indicar que el dataset incluye consultas de estas categorías y que el sistema las rechaza o pide
      aclaración en lugar de inventar.
- [ ] **Trabajo futuro** ligado a cada categoría: agente con *function calling* para varios pasos,
      analítica y predicción, más módulos en el catálogo y escritura con confirmación del usuario.

### Defensa ante el tribunal
- [ ] Preparar la justificación del diseño de dominio cerrado e híbrido (exactitud, seguridad,
      auditabilidad, evaluación y alcance del TIC), citando Bi et al. (2025), Béchard y Ayala (2024),
      Mishra et al. (2026) y Pandey et al. (2024).
- [ ] **Trabajo futuro:** agente con *function calling* que reutilice los handlers como herramientas
      sin perder el validador ni los permisos; operaciones de escritura con confirmación del usuario.

---

## 1.2 Declaración del uso de inteligencia artificial

- [ ] **Formato oficial de la UTPL:** descargar el formato de declaración de uso de herramientas de
      inteligencia artificial desde la página de Trabajos de titulación de la Biblioteca UTPL
      (https://biblioteca.utpl.edu.ec/trabajos-fin-titulacion), llenarlo y entregarlo con el TIC al
      correo de revisión de la biblioteca (`bbc_revision@utpl.onmicrosoft.com`).
- [ ] **Revisar la normativa vigente:** buscar en las normativas públicas de Procuraduría UTPL si
      existe un reglamento o lineamiento específico de IA, y preguntar a la tutora cómo prefiere que
      se declare.
- [ ] **Metodología (1.3):** añadir un párrafo breve que declare el uso de Claude Code (Anthropic) como
      asistente de programación (implementación de código, pruebas automáticas y revisión técnica) y
      deje claro lo realizado por el autor: diseño de la solución, casos de uso, decisiones de
      arquitectura y seguridad, validación de resultados y redacción. Ajustarlo a lo que de verdad
      se hizo.
- [ ] Mencionar el uso de **Gemini y Groq** como componentes del prototipo (no como apoyo a la
      redacción), para no confundir ambos usos de la IA.
- [ ] Coherencia con el historial de GitHub: los commits muestran al autor como "Ismael Calle" y a
      Claude como coautor.

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
