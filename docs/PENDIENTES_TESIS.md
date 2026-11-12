# Cambios pendientes en el documento de la tesis

Lista de correcciones para el documento de la tesis, según la revisión del documento frente al
código del repositorio. Marcar cada casilla al aplicarla.

**Versión aplicada:** `TESIS_ISMAEL_CALLE_actualizada.docx` (12/11/2026), generada a partir de la
versión entregada por el autor. Incluye solo lo ya implementado en el código; la ruta híbrida y el
Capítulo 5 quedan pendientes. Al abrirla en Word hay que aceptar "actualizar campos" (o F9) para
regenerar los índices.

---

## 1. Alinear el Capítulo 3 con el código (prioridad alta)

### Ya implementado en el código: actualizar el documento

- [x] **3.4.2, ejemplo de dominio de `account.move.line`:** cambiar `("display_type", "=", False)` por
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
- [x] **3.4.2, ejemplo de búsqueda de producto:** reemplazar el ejemplo con `"|"` y `limit=1`. Contradice
      la Tabla 17 ("Varias coincidencias → mostrar coincidencias"), porque toma la primera sin avisar.
      El código real busca primero por código exacto, luego por nombre, y si hay más de una
      coincidencia responde con la lista para que el usuario precise.
- [x] **3.4.3, último párrafo:** cambiar "display_type vacío" por "display_type igual a product".
- [x] **Tabla 16:** los nombres de las funciones no existen en el código. Usar los reales:
      *Aplicado: nombres reales `handlers/<archivo>.py → handle()`, filas de `conversacion` y `fuera_de_alcance`, y nota sobre `HANDLER_MAP`.*

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
- [x] **3.4.2:** el texto dice que se usan `search()`, `search_read()`, `browse()` o `read_group()`.
      El código solo usa `search()` y lectura de campos del recordset. Ajustar.
- [x] **Tabla 8 (CU-02), fila Resultado:** cambiar "Producto, ubicación y cantidad disponible" por
      "Producto, ubicación, existencia, cantidad reservada y cantidad disponible para la venta".
- [x] **Tabla 11 (CU-05), fila Resultado:** "Producto, existencia, cantidad reservada, cantidad
      disponible para la venta, cantidad facturada, número de facturas y valor facturado".
- [x] **Tablas 9 y 15 (CU-03):** la entrada mínima es `customer_name` **o** `product_name` **o**
      `product_code`. El código acepta consultas solo por producto ("¿cuántas ventas hay del CAS-001?").
      *Aplicado: además, CU-03 por producto, estado del pedido y modelos relacionados.*
- [x] **3.3.2 o 3.3.4, fechas:** añadir que `date_from` y `date_to` van en formato AAAA-MM-DD, que la
      fecha actual se envía al LLM para resolver periodos relativos ("este mes", "julio") y que el
      validador descarta fechas no válidas.
      *Aplicado: párrafo después de la Tabla 15.*
- [x] **Tabla 6 y 3.4.3, "listas blancas":** el código no tiene una lista blanca de campos que se
      verifique en tiempo de ejecución; cada handler lee solo campos fijos. Redactar así: "cada función
      interna accede únicamente a los campos definidos en la Tabla 6", en lugar de "listas blancas".
- [x] **2.5.3:** quitar la mención a **Pydantic**; el proyecto no lo usa. La validación está en
      `services/validator.py` (validación de intención, entidades requeridas, estados y fechas).
- [x] **3.1.1:** la frase sobre reglas de registro ahora es correcta: el módulo define reglas para que
      cada usuario vea solo sus sesiones, mensajes y consultas, y el administrador del chatbot vea todo.
      Se puede mencionar como parte de la seguridad.
- [x] **Interfaz conversacional:** el Capítulo 3 no menciona que el chat funciona dentro de
      **Discuss** (mensaje directo con el contacto "Asistente ERP", similar a OdooBot, con `/help`).
      Añadir en 3.1.2 (Tabla 2) el módulo Conversaciones/Discuss (`mail`, `mail_bot`) y describir la
      interfaz.
      *Aplicado: fila en la Tabla 2 y párrafo en 3.1.2.*

### Implementado después de la revisión inicial

- [x] **Tabla 13, `intencion_desconocida`:** reemplazarla por la intención `conversacion`, ya
      implementada en el código (ver sección 1.1 de este archivo).
- [x] **Tablas 14 y 15, entidad `order_state`:** ya implementada en el código (valores `cotizacion`,
      `pedido`, `cancelado`; sin valor se consultan los pedidos confirmados). Revisar que las tablas
      usen esos valores.
- [x] **Memoria de la sesión (sección de memoria corta):** describir la regla: un seguimiento solo
      hereda el sujeto que falta (cliente, producto o factura); una aclaración conserva lo ya dicho.
      *Aplicado: párrafo en 3.4.5, con cita a Maharana et al. (2024).*
- [x] **Tabla 5, pedidos de venta (~1.000):** la cifra es correcta. Verificado: la base generada
      tiene 1.083 pedidos (900 confirmados, 144 cotizaciones, 39 cancelados) y 656 facturas. Opcional:
      poner las cifras exactas y el desglose por estado.
      *Aplicado: nota con las cifras exactas bajo la Tabla 5 y en el Sprint 1.*

### Dataset de evaluación (3.5)

- [x] **3.5.1 y Tabla 18:** el campo se llama `expected_result_contains` (lista de textos que debe
      contener la respuesta), no `expected_result`. Actualizar el ejemplo JSON y la tabla. Hay además
      un campo `expected_status` en las consultas de aclaración y rechazo.
- [x] **Tamaño del dataset:** 56 consultas: 31 correctas, 10 incompletas, 4 ambiguas y 11 fuera de
      alcance (incluye las 5 de CU-05, Q052 a Q056). Contar de nuevo con el archivo final antes de
      citarlo.
      *Aplicado: 62 consultas (31 correctas, 10 incompletas, 4 ambiguas, 11 fuera del alcance y 6 de conversación).*
- [x] **Fase 4 (1.3):** el dataset no tiene "operación estructurada esperada". Quitarlo del texto o
      agregarlo al dataset.

---

## 1.1 Cambios planificados en el código que afectarán el documento

Aplicar cuando cada cambio esté implementado (ver `SEGUIMIENTO_CAMBIOS.md`, puntos 7 a 10).

### Arquitectura híbrida: conversación libre, datos solo desde Odoo (punto 8)
- [x] **Describir la arquitectura como híbrida** (3.3, 3.4 y la introducción del Capítulo 3): la IA
      redacta libremente las respuestas que no involucran datos del negocio (saludos, agradecimientos,
      capacidades, rechazos), pero todo dato del ERP pasa por una consulta estructurada y validada
      sobre el ORM. Frase guía: *"la IA puede decir lo que quiera, excepto datos del negocio: esos solo
      los puede obtener pidiéndolos al sistema"*.
      *Aplicado: en 3.3 y 3.4 se describe que la IA solo interpreta y redacta conversación, y que los datos salen de Odoo. No se usa la palabra "híbrida" para no confundirla con la ruta híbrida (punto 13).*
- [x] **Tabla 13:** reemplazar `intencion_desconocida` por `conversacion` (saludos, agradecimientos,
      preguntas sobre lo que puede hacer el asistente y charla general).
- [x] **3.3.3, esquema JSON:** añadir el campo `reply` (texto redactado por la IA, solo para
      `conversacion` y `fuera_de_alcance`) y el estado `chat`. Incluir un ejemplo de saludo.
      *Aplicado: campo `reply` con ejemplo de saludo. No existe un estado `chat`: la conversación usa `status = "ready"`.*
- [x] **3.3.4, validación:** añadir el control anti-invención (una respuesta conversacional con montos,
      números de factura o códigos de producto se descarta) y el límite de longitud de `reply`.
- [x] **3.2.6 y Tablas 12 y 23:** las respuestas fuera de alcance las redacta la IA (explica por qué no
      puede y qué sí puede hacer); el mensaje fijo queda solo como respaldo.
      *Aplicado: en 3.2.6 y la Tabla 12. La Tabla 24 (antes 23) se dejó igual.*
- [x] **Tabla 17:** fila "Consulta no relacionada" → la IA responde con sus palabras e indica el
      alcance.
      *Aplicado: ahora es la Tabla 18.*
- [x] **3.5.2:** añadir la categoría de consultas de conversación al dataset.
      *Aplicado: Tabla 25.*

### Velocidad (punto 7)
- [x] **Capítulo 4:** documentar la configuración del modelo (sin "pensamiento" para Gemini 2.5,
      formato JSON exigido con esquema, timeout y reintentos) y por qué.
      *Aplicado: Sprint 6 (4.1.6), con la Tabla 31 de antes y después.*
- [ ] **Capítulo 5:** comparar los tiempos antes y después de estas mejoras, con los datos del punto 12.

### Métricas y monitoreo (punto 12, observación de la tutora)
- [x] **2.4.6, métricas:** añadir las métricas de operación: tasa por tipo de resultado,
      disponibilidad del servicio (consultas sin fallo de la IA / total), latencia por etapa (IA,
      consulta a Odoo, total) y satisfacción del usuario (👍 / 👎).
- [x] **Capítulo 4:** describir el log clasificado (resultado, código de error, tiempos por etapa,
      proveedor, modelo, tokens) y el panel de análisis en Odoo (gráficos, tabla dinámica, filtros).
      *Aplicado: Sprint 5 (4.1.5).*
- [ ] **Capítulo 5:** presentar dos fuentes de métricas: **evaluación controlada** con el dataset
      (precisión de intención, de entidades y de ejecución) y **monitoreo en uso real** con el log
      (resultados, latencias, disponibilidad, satisfacción).
- [x] Mencionar la retención limitada del log como medida de privacidad.

### Proveedores de IA (aclaración pedida por la tutora)
- [x] **Capítulo 2 o 4:** distinguir tres roles: desarrollador del modelo (Google, Meta, OpenAI,
      Anthropic, Mistral), proveedor de la API o de inferencia (Google AI Studio/Vertex AI, Groq,
      OpenAI, Azure, AWS Bedrock) y agregadores (OpenRouter, Together AI, Hugging Face).
      *Aplicado: en el Sprint 2 (4.1.2).*
- [x] Indicar que el prototipo se conecta directamente a dos proveedores de inferencia: **Google AI
      Studio** (modelos Gemini, desarrollados por Google) y **Groq** (modelos abiertos como Llama, de
      Meta). La lista de modelos disponibles la entrega cada proveedor por su API de listado
      (`models.list` de Gemini y *List models* de Groq), se consulta en tiempo real al pulsar "Listar
      modelos" y no incluye precios: los límites gratuitos se consultan en las páginas de precios.
      *Aplicado: el botón ahora se llama "Actualizar modelos" y sincroniza un catálogo.*
- [x] Justificar la elección: cuota gratuita suficiente para un prototipo académico, baja latencia
      (familia Flash de Gemini, inferencia rápida de Groq) y salida JSON nativa.

### Selección y validación del modelo (punto 9)
- [x] **Capítulo 4 (configuración):** el modelo se elige de un desplegable filtrado por proveedor,
      alimentado por el catálogo que publica el proveedor, en lugar de escribirlo a mano. Explicar que
      el catálogo se sincroniza (agrega, actualiza y marca como no disponibles los modelos retirados,
      sin borrarlos).
- [x] **Validación de la configuración:** al guardar se prueba la conexión si cambió el proveedor, la
      API key o el modelo; una configuración que no funciona no se guarda.
- [x] **Separar dos tipos de fallo:** los de configuración se detectan al guardar; los externos
      (caída del proveedor, sin internet, cuota agotada) se manejan en el chat con reintentos,
      mensajes claros y, si se implementa, un modelo de respaldo.

### Respuestas de datos redactadas por la IA (punto 10, opcional)
- [ ] Si se implementa: describirlo como opción configurable con verificación de que los números de la
      respuesta coinciden con los datos de Odoo, sin contradecir "sin inventar valores" (3.2.1).
- [ ] **Capítulo 5:** experimento plantilla vs. redacción por IA (exactitud, latencia, naturalidad).

### Permisos de usuario (punto 11)
- [x] **3.1.1 y 3.4.3:** explicar con evidencia que el chatbot respeta los permisos de Odoo: cada
      consulta corre con el usuario autenticado, así que los derechos de acceso y las reglas de
      registro se aplican igual que en la interfaz. Ejemplo verificado: un vendedor que solo ve sus
      documentos obtiene 0 unidades facturadas donde el administrador obtiene 137.
      *Aplicado: en 3.1.1. El ejemplo numérico (137 frente a 0 unidades) no se incluyó.*
- [x] **Tabla 17:** añadir la fila "Usuario sin permiso" → mensaje en español sin detalles técnicos.
- [x] Mencionar que las respuestas se basan solo en los documentos a los que el usuario tiene acceso.
- [x] **Nueva tabla en el Capítulo 3: permisos por caso de uso**, con el grupo mínimo de cada
      consulta: CU-01 Facturación; CU-02 Inventario / Usuario; CU-03 y CU-04 Ventas / Usuario (solo
      documentos propios); CU-05 Inventario / Usuario y Facturación. Indicar que los administradores
      de cada módulo pasan porque en Odoo el Administrador incluye al Usuario.
      *Aplicado: Tabla 17 en la nueva sección 3.4.4.*
- [x] **Describir el control como una capa adicional** (3.4): tabla editable *Permisos por consulta*,
      evaluada por usuario y en cada mensaje, después del validador y antes de consultar. Complementa
      los permisos de Odoo, no los reemplaza ni los modifica; nunca da más acceso que Odoo.
      *Aplicado: sección 3.4.4.*
- [x] **Diagrama de defensa en profundidad:** validador de la salida de la IA → control por rol del
      asistente → permisos de Odoo (derechos de acceso y reglas de registro).
      *Aplicado: Figura 1 en 3.4.*
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
- [x] **Metodología (1.3):** añadir un párrafo breve que declare el uso de Claude Code (Anthropic) como
      asistente de programación (implementación de código, pruebas automáticas y revisión técnica) y
      deje claro lo realizado por el autor: diseño de la solución, casos de uso, decisiones de
      arquitectura y seguridad, validación de resultados y redacción. Ajustarlo a lo que de verdad
      se hizo.
      *Aplicado: subsección "Uso de herramientas de inteligencia artificial" al final de 1.4 Metodología. El autor debe revisarla y ajustarla.*
- [x] Mencionar el uso de **Gemini y Groq** como componentes del prototipo (no como apoyo a la
      redacción), para no confundir ambos usos de la IA.
- [ ] Coherencia con el historial de GitHub: los commits muestran al autor como "Ismael Calle" y a
      Claude como coautor.

---

## 2. Contradicciones internas

- [x] **Datos demo:** la Introducción y la Fase 2 dicen "datos demo de Odoo y datos sintéticos";
      3.1.1 y el Capítulo 4 dicen base limpia (`--without-demo=all`). Unificar a "base limpia con
      datos sintéticos".
- [x] **Objetivo específico 1:** dice "revisión sistemática". Cambiar a "revisión de literatura" o
      añadir un flujo tipo PRISMA en 2.5.1 (84 registros → descartados por título/resumen → por texto
      completo → 12 seleccionados, con motivos de exclusión).
      *Aplicado: se cambió a "revisión de literatura" (también en la Fase 1).*
- [ ] **2.5.1, artículo número 84:** explicar cómo se encontró si no salió en las dos búsquedas
      (búsqueda manual, referencias de otro artículo, etc.).
- [x] **"E2"** aparece en las Fases 3 y 4 sin definirse. Definirlo o reemplazarlo por "la Fase 2".
- [x] **Fase 3:** promete pruebas unitarias y de integración al cierre de cada sprint. Ajustar a lo
      que de verdad se hizo (script de pruebas del validador y pruebas en Odoo).

---

## 3. Errores técnicos y de fuentes

- [x] **2.2.1:** "Odoo 18 es la última versión mayor" ya no es cierto (Odoo 19 salió en septiembre de
      2025). Cambiar a "Odoo 18, versión utilizada en este trabajo…" y citar las notas de versión
      oficiales en lugar del blog de Scorpora.
      *Aplicado: solo el texto. Falta reemplazar la fuente de Scorpora por las notas de versión oficiales.*
- [x] **2.2.3:** `name_get()` ya no existe desde Odoo 17 (se reemplazó por `display_name` /
      `_compute_display_name`). Quitarlo o actualizarlo. Preferir la documentación oficial del ORM
      sobre el blog de Kalariya (CandidRoot).
      *Aplicado: solo el texto. Falta preferir la documentación oficial del ORM sobre el blog de Kalariya.*
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

- [x] Corregir **"Oddo" → "Odoo"** en el texto (2.2.2, 2.3.6) y en las tres entradas de referencias.
      *Aplicado: en el texto y en las tres referencias. Hay que corregirlo también en Zotero, o se revierte al actualizar las citas.*
- [ ] Añadir las entradas que faltan o unificar su forma:
  - [ ] Lewis (2018)
  - [ ] Sauro y Lewis (2016)
  - [ ] Mishra et al. (2022), o corregir la cita a 2026
  - [x] Odoo (2024): en la lista solo está "Oddo (2024)"
  - [x] "Organisation for Economic Co-operation and Development (2021)" vs. "OECD" en la lista: usar
        la misma forma
      *Aplicado: el texto ahora dice "OECD (2021)".*
  - [x] Arteaga et al. (2022) → la referencia es Pionce Arteaga et al.
  - [ ] IBM (2024) citado para chatbots empresariales: la página citada es sobre NLP; la de chatbots
        es Finio (2026)
- [x] "Béchard y Ayala (2024)" en el texto vs. "Ayala, O., & Bechard, P." en la lista: el orden de
      autores debe coincidir.
      *Aplicado: el texto ahora dice "Ayala y Bechard (2024)". Corregirlo también en Zotero.*
- [ ] Citas mal formadas:
  - [ ] "Según (Balić et al., 2022) (2022)" → "Según Balić et al. (2022)"
  - [x] "organizaciones(SAP, 2026)" → falta un espacio antes del paréntesis
  - [x] "(Sai Kiran Reddy Malikireddy & Snigdha Tadanki, 2022)" → "(Malikireddy & Tadanki, 2022)";
        en la lista "Malikireddy, S. K. R., & Tadanki, S."
      *Aplicado: en la cita y en la referencia, reubicada en orden alfabético. Corregirlo también en Zotero.*
- [ ] Completar referencias sin revista, editorial ni URL: Bawa (2024), de Araújo y Silva (2023),
      Himawan (2024).
- [ ] Verificar contra la fuente: Quamar et al. (2022) repite "Lei, C., & Lei, C."; el año de
      Katsogiannis-Meimarakis et al. no parece coincidir con su DOI.

---

## 6. Formato y plantilla

- [x] Numeración del Capítulo 1: hay dos "1.1" (Problemática y Justificación); Objetivos, Metodología
      y Estructura quedan desfasados.
      *Aplicado: 1.2 Justificación, 1.3 Objetivos, 1.4 Metodología y 1.5 Estructura.*
- [x] Tildes: "Capitulo dos" → "Capítulo dos"; "capitulo 1" → "capítulo 1".
- [ ] 2.5.2 y 2.5.3 tienen estilo de título de nivel 2; deben ser nivel 3. Borrar los párrafos vacíos
      con estilo de título alrededor de la Tabla 1.
- [ ] Página de aprobación:
  - [ ] "Loja" vs. "CUENCA" en la carátula
  - [x] "en calidad de director" → "directora"
  - [ ] "Chicaiza Espinoza" (carátula) vs. "Espinosa" (aprobación): unificar
- [ ] Añadir figuras al Capítulo 3 (hoy no hay ninguna):
  - [x] Diagrama de arquitectura: Discuss → orquestador → LLM → validador → handler ORM → respuesta
      *Aplicado: Figura 1.*
  - [ ] Diagrama de flujo o de secuencia de una consulta
- [ ] Pendientes de plantilla: dedicatoria, agradecimiento, resumen, abstract, palabras clave, nombres
      de capítulos en la declaración de autoría y C.I. de la directora.

---

## 7. Pendientes nuevos (revisión del 12/11/2026)

### Después de abrir la versión actualizada
- [ ] Aceptar "actualizar campos" en Word (o F9) para regenerar el índice de contenido, el de tablas
      y el de figuras con la nueva numeración (Tablas 1 a 33, Figura 1).
- [ ] Revisar el Capítulo 4: los sprints 2 a 7 y la sección 4.1.8 describen lo implementado, pero
      el orden en sprints es una propuesta y se puede reorganizar.
- [ ] Revisar y ajustar la subsección "Uso de herramientas de inteligencia artificial" (1.4).
- [ ] Sincronizar en Zotero las citas corregidas a mano ("Odoo", Ayala y Bechard, Malikireddy y
      Tadanki); si no, se revierten al actualizar las citas.
- [ ] "Según (Balić et al., 2022) (2022)": cambiar a cita narrativa desde Zotero.
- [ ] 2.5.3: sacar a Huang et al. (2025) del grupo Text-to-SQL. La cita es un campo de Zotero, por
      eso no se cambió a mano.

### Cambios del código del 11/11/2026 que deben reflejarse en el Capítulo 4
- [ ] Catálogo de modelos con **gratuidad estimada** (columna "Precio": gratis, de pago o sin dato).
      Aclarar que es una estimación, porque la API no informa precios.
- [ ] "Probar conexión" y "Actualizar modelos" funcionan sin pulsar Guardar.
- [ ] Revisión del formato de la API key según el proveedor (Groq `gsk_…`, Gemini `AIza…`) y API key
      vacía al cambiar de proveedor.
- [ ] Encabezado User-Agent propio en las llamadas HTTP, porque Groq (Cloudflare) bloqueaba el de
      Python con el error 403 / 1010.

### Decisiones pendientes que afectan al documento
- [ ] **API key:** hoy se guarda en texto plano en los parámetros del sistema (solo la ven los
      administradores). Si se implementa el cifrado propuesto, actualizar el Sprint 2 y las
      limitaciones.
- [ ] **Ruta híbrida (punto 13):** se documenta cuando esté aprobada por la tutora e implementada
      (3.3, 3.4, Tabla 6 como catálogo, nuevo esquema JSON del plan y diagrama de rutas).
- [ ] **Capítulo 5:** evaluación controlada con el dataset y monitoreo con la auditoría; comparación
      de tiempos antes y después; limitaciones; trabajo futuro.
- [ ] Diagrama de secuencia de una consulta (Capítulo 3, opcional; la Figura 1 ya muestra el flujo).
