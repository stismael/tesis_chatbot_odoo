# Cambios realizados en el documento de la tesis

Registro de las ediciones hechas al documento Word de la tesis (no al código; los cambios de código están en
`SEGUIMIENTO_CAMBIOS.md`). Para cada versión se indica qué se cambió, dónde y por qué.

**Reglas que se respetan en todas las ediciones**
- Se conserva la estructura del documento: capítulos, secciones y numeración.
- Se usan los estilos que ya tiene el documento: Título 3 para las secciones, párrafo normal, estilo
  «Descripción» para los títulos de tablas y figuras (con su número automático), tablas con el estilo
  APA del documento y notas en tamaño 10 con «Nota.» en cursiva y «Elaboración propia».
- No se agregan formatos nuevos ni se tocan las citas y referencias de Zotero.
- Después de cada edición se compara el texto con la versión anterior para confirmar que solo cambió lo
  acordado.

---

## Versión 4 · 23 de noviembre de 2026

**Archivo base:** versión 3. **Archivo entregado:** `TESIS_ISMAEL_CALLE_v4_2026-11-23.docx`.
**Motivo:** revisión completa del documento y resultados de la evaluación completa (Groq y Gemini).
El título no se cambia: es el del tema aprobado.

### Correcciones de la revisión

| Dónde | Qué se cambió | Por qué |
|---|---|---|
| Resumen y Abstract | Redactados (tenían texto de relleno «Xxxx») con palabras clave en español e inglés | Secciones obligatorias |
| 1.4 Metodología | «Para el desarrollo… se llevará a cabo siguiendo» → «El desarrollo… siguió»; métricas de la Fase 4 alineadas con las que se calculan (se quitó «consistencia de las respuestas», que no se mide) | Frase incompleta y coherencia con el Capítulo 5 |
| 3.3.1, 3.3.2, 3.4.5, 3.5.1 | Futuro → presente («permitirá», «podrá», «identificará», «se considerarán»…) | El prototipo ya existe |
| 5.4, tabla de pruebas | 141 pruebas en Odoo (antes 140); «Selección del modelo» 21 | Prueba agregada en el PR #19 |

### Capítulo 5: resultados (nuevo)

| Sección | Contenido |
|---|---|
| 5.5 Resultados generales | Tabla por modelo: intención, entidades, comportamiento y datos correctos; ninguna respuesta con datos incorrectos |
| 5.6 Resultados por categoría | Tabla de comportamiento correcto por categoría y modelo |
| 5.7 Latencia, consumo y disponibilidad | Mediana, p95, promedio, tokens y consultas sin respuesta (primera ejecución y final) |
| 5.8 Análisis de errores | Nombres con errores de escritura, «Ventas de Repuestos», etiqueta de Q032, predicciones, Q076 |
| 5.9 Discusión y limitaciones | Comparación con Text-to-SQL, modelos recomendados y cinco limitaciones |
| Conclusiones y Recomendaciones | Capítulos nuevos: una conclusión por objetivo específico y una del objetivo general; seis recomendaciones |

### Pendiente en el documento (lo hace el autor)
- [ ] Dedicatoria y Agradecimiento (texto de relleno «Xxxx»).
- [ ] Carátula: «Chicaiza **Espinoza**» y en la aprobación «Chicaiza **Espinosa**»; unificar. Lugar: la carátula dice
      Cuenca y la aprobación «Loja, día de mes de año».
- [ ] Declaración de autoría: reemplazar «(se debe colocar los nombres de los capítulos…)» y la C.I. de la directora.
- [ ] Zotero: 2.1.1 «Según (Balić et al., 2022) (2022)» (cita duplicada); 2.4.3 «Según Mishra et al. (2022)»: la
      cita enlazada es Katsogiannis-Meimarakis et al. (2022), revisar autor o cita; 1.4 cita a Lewis (2018) y Sauro y
      Lewis (2016), que no están en las Referencias.
- [ ] En Word, «actualizar campos» (F9) para regenerar los índices de contenido, tablas y figuras.
- [ ] Decisión con la tutora: SUS (1.4 y 1.5) y la etiqueta de la consulta Q032.

---

## Versión 3 · 17 de noviembre de 2026

**Archivo base:** versión 2 (`TESIS_ISMAEL_CALLE_v2_2026-11-17.docx`).
**Archivo entregado:** `TESIS_ISMAEL_CALLE_v3_2026-11-17.docx`.
**Motivo:** recomendaciones sobre el escrito (`Recomendaciones_escrito_tesis_v2.md`): separar el análisis
(Capítulo 3), la construcción y la arquitectura (Capítulo 4) y la evaluación (Capítulo 5), con requisitos,
planificación, decisiones y riesgos en tablas. Se movió el texto existente en lugar de reescribirlo; solo se
redactó lo nuevo y se ajustaron tiempos verbales en los párrafos movidos («se realizará» → «se realiza»).

### Capítulo 1

| Dónde | Qué se cambió | Por qué |
|---|---|---|
| Introducción | «Solo lectura» se precisa: no crea, modifica ni elimina datos del negocio; el módulo solo registra sus conversaciones y la auditoría | El módulo sí escribe sus propios registros (sesiones, auditoría) |
| 1.5 Estructura del documento | Párrafos de los capítulos 3, 4 y 5 según la nueva estructura (se mantiene la mención a SUS) | Coherencia con los capítulos |

### Capítulo 3 · Análisis y especificación funcional

| Nueva sección | Contenido | Origen |
|---|---|---|
| Introducción | Reescrita según la nueva estructura | — |
| **3.1 Introducción y alcance de la solución** | Qué es el prototipo, alcance de cinco consultas de lectura, sin SQL, entorno sintético | Nuevo; el texto del entorno (antes 3.1.1) pasa al Sprint 1 |
| **3.2 Requisitos** | **Tabla 2** RF-01 a RF-11 y **Tabla 3** RNF-01 a RNF-07, con origen y forma de verificación; el tiempo de respuesta se mide, sin umbral inventado | Nuevo |
| 3.3 Modelos y datos involucrados | 3.3.1 Módulos y modelos de Odoo (antes 3.1.2 y 3.1.3, con la Figura 1); 3.3.2 Datos y campos autorizados (antes 3.1.4 y 3.1.6) | Movido |
| 3.4 Casos de uso | Antes 3.2; subsecciones 3.4.1 a 3.4.6 | Renumerado |
| 3.5 Especificación de intenciones y entidades | Antes 3.3.1 y 3.3.2. **Se eliminó 3.3.3 (bloques JSON)**: su contenido pasa a la tabla del contrato (Sprint 2) | Recomendación: JSON como tabla |
| **3.6 Restricciones funcionales y de seguridad** | 3.6.1 Validación (antes 3.3.4); 3.6.2 Modelos, campos y operaciones (antes 3.4.3); 3.6.3 Control de permisos (antes 3.4.4, con el párrafo de reglas de registro de 3.1.1); 3.6.4 Consultas ambiguas y seguimiento (antes 3.4.5) | Reagrupado |
| **3.7 Planificación del desarrollo iterativo** | **Tabla 19**: nueve sprints con objetivo, entregable, requisitos y PR del repositorio como evidencia | Nuevo |

Salen del Capítulo 3: preparación de la base (al Sprint 1), volúmenes de la base y conjunto de evaluación
(al Capítulo 5), flujo y capas de control (Figura 11, a 4.3.5), secuencia de una consulta (Figura 10, a
4.3.4), tabla de intenciones y funciones y ejecución con el ORM (al Sprint 3).

### Capítulo 4 · Diseño y desarrollo del prototipo

| Dónde | Qué se cambió |
|---|---|
| Título y 4.1 | Subtítulo «Diseño y desarrollo del prototipo» y **4.1 Introducción** nueva |
| 4.2 Desarrollo iterativo | Antes 4.1; sprints 4.2.1 a 4.2.9; referencias «sección 3.4.4/3.4.5/4.1.8» actualizadas |
| 4.2.1 Sprint 1 | Recibe la instancia de Odoo y los pasos de preparación de la base |
| 4.2.2 Sprint 2 | **Tabla 21** responsabilidades del orquestador (responsabilidad, entrada, procesamiento, salida, restricciones) y **Tabla 22** contrato de la salida del modelo (intent, entities, status, missing_entities, reply), con el texto de responseSchema e invalid_output que acompañaba a los JSON |
| 4.2.3 Sprint 3 | Recibe la correspondencia intención-función (Tabla 24) y la ejecución con el ORM |
| **4.3 Arquitectura de la solución** | 4.3.1 **Tabla 32** decisiones de diseño (intenciones + ORM frente a Text-to-SQL y ruta híbrida; módulo interno; proveedores externos; solo lectura); 4.3.2 componentes (Figura 8); 4.3.3 **Figura 9 nueva**: arquitectura general ilustrada; 4.3.4 flujo de una consulta (Figura 10) y caminos alternativos (aclaración, sin permiso, fallo del proveedor); 4.3.5 seguridad (Figura 11) y **Tabla 33** riesgos, controles y comportamiento esperado |
| 4.4 Estrategia de pruebas | Antes 4.1.10, ahora breve (texto y Figura 12); la tabla de pruebas pasa a 5.4 |

### Capítulo 5 · Evaluación y análisis de resultados (nuevo)

| Sección | Contenido |
|---|---|
| 5.1 Introducción y diseño experimental | **Tabla 34** condiciones: versión 18.0.1.14.0, Docker, semilla fija, 106 consultas, modelos evaluados de Gemini y Groq, noviembre de 2026, pausa por cuota |
| 5.2 Construcción y caracterización del conjunto | Antes 3.5 (sin el ejemplo JSON), en pasado, con la tabla de volúmenes de la base (Tabla 35) |
| 5.3 Protocolo y métricas | Procedimiento del script y **Tabla 44** con las métricas tal como se calculan |
| 5.4 Pruebas unitarias y de integración | Diferencia con la evaluación experimental y Tabla 45 de pruebas |

Total: 45 tablas (antes 36) y 12 figuras (antes 11). Las referencias «Tabla N» y «Figura N» del texto se
actualizaron automáticamente y se comprobó que ningún párrafo se perdió salvo los títulos reemplazados, los
bloques JSON y los párrafos reescritos.

### Recomendaciones no aplicadas en esta versión

| Recomendación | Motivo |
|---|---|
| Quitar SUS, cambiar «optimización» o el título | Decisión de la tutora |
| Unificar tiempos verbales en todo el documento | Se hará en la edición final; aquí solo en los párrafos movidos |
| Antecedentes de tesis UPS/UDLA | Los repositorios no fueron accesibles desde el entorno de trabajo |
| Capturas de pantalla y anexos | Requieren el entorno de la tesis; se agregan con los resultados |
| Validación con Pydantic | El validador propio ya cumple la misma función; se explica en 3.6.1 y en la Tabla 22 |
| Subsecciones de cuarto nivel (X.1.1.1) | El estilo Título 4 del documento no es APA; se usaron tablas |
| Correcciones de Zotero (Balić y otras) | Se hacen en Word con Zotero |

### Pendiente en el documento
- [ ] Resultados del Capítulo 5 (5.5 en adelante) cuando termine la evaluación de Groq.
- [ ] En Word, «actualizar campos» (F9) para regenerar índices.
- [ ] Enlace al repositorio y etiqueta de la versión evaluada.

---

## Versión 2 · 17 de noviembre de 2026

**Archivo base:** versión del 9 de noviembre (`TESIS_ISMAEL_CALLE_actualizada.docx`).
**Archivo entregado:** `TESIS_ISMAEL_CALLE_v2_2026-11-17.docx`.
**Motivos:** recomendación de la tutora de explicar la solución con diagramas en lugar de código; cambios del
código del 11 al 17 de noviembre (PR #10 a #19); dataset ampliado y evaluación real.

### Capítulo 3

| Dónde | Qué se cambió | Por qué |
|---|---|---|
| 3.1.3 Modelos de datos | Nueva **Figura 1**: modelos de Odoo consultados, campos autorizados y relaciones | Mostrar con un diagrama lo que antes solo estaba en tablas |
| 3.2 Casos de uso | Nueva **Figura 2**: diagrama de casos de uso (actores, CU-01 a CU-05 y funciones de administración) | Diagrama UML pedido por la tutora |
| 3.2.6, 3.3.4 y Tabla 16 | «Mensaje fijo de respaldo» pasa a «mensaje predeterminado» | Evitar confusión con el nuevo modelo de respaldo |
| 3.4 | La figura del flujo de una consulta pasa a ser la **Figura 3** (se actualizó la referencia en el texto) | Numeración por las figuras nuevas |
| 3.4.2 Ejecución mediante ORM | Se quitó el código (dominio de la factura y búsquedas con `search()`); se explica con texto y con la nueva **Figura 4** (diagrama de secuencia de una consulta) | Recomendación de la tutora: sin código |
| 3.4.5 Memoria corta | La memoria guarda las últimas **preguntas del usuario**; las respuestas del asistente no se envían a la IA porque contienen datos de Odoo | Cambio de privacidad del PR #15 |
| 3.5.1 y Tabla 19 | Dataset de **106 consultas** (antes 62) con categorías nuevas; un solo comportamiento correcto por consulta; **referencia independiente** para comparar los datos; dos filas nuevas en la Tabla 19 (`expected_period`/`expected_dates` y `sequence`/`turn`) | Ampliación del dataset y evaluación confiable (PR #15 y rama del dataset) |
| 3.5.2 | Nueva **Tabla 26**: ejemplos de errores de escritura, secuencias de dos turnos, intentos de manipulación y consultas flexibles no soportadas | Ilustrar las categorías nuevas |

### Capítulo 4

| Dónde | Qué se cambió | Por qué |
|---|---|---|
| 4.1.1 Sprint 1 | Se quitó todo el código (`docker-compose.yml`, `initialize-database.ps1`, manifiesto y generador de datos); se explica con texto y con la nueva **Figura 5** (tecnologías y despliegue) | Recomendación de la tutora: sin código |
| 4.1.2 Sprint 2 | Se quitó el extracto de `discuss_channel.py`; nuevas **Figura 6** (componentes del módulo) y **Figura 7** (diagrama de clases); Groq se describe con los modelos vigentes (gpt-oss y Qwen, ya no Llama) | Diagramas en lugar de código; Groq retiró Llama 3.3 |
| 4.1.3 Sprint 3 | Se quitaron los extractos de `HANDLER_MAP` y `stock.py`; el texto remite a la Figura 4 | Sin código |
| 4.1.4 Sprint 4 | Se quitó el extracto del orquestador; se explica con texto | Sin código |
| 4.1.6 Sprint 6 | Se quitó el extracto de `llm_client.py`; párrafo con las mejoras del 11/11 (probar conexión y actualizar modelos sin guardar, gratuidad estimada, formato de la clave por proveedor, User-Agent propio); nueva **Figura 8** (regla de guardado); en la tabla de configuración, «Reintentos: 1 (0 si hay modelo de respaldo)» y «Prueba de conexión al guardar y botón Probar conexión sin guardar»; los fallos del proveedor se atienden también con el modelo de respaldo | Cambios del 11/11, PR #10 y #12 |
| 4.1.7 Sprint 7 | Se quitó el extracto de `validator.py`; se explica con texto | Sin código |
| **4.1.8 Sprint 8 (nuevo)** | Modelo de respaldo: cuándo responde y cuándo no, regla de guardado y auditoría; nueva **Figura 9** y nueva **Tabla 34** | PR #13 (pedido de la tutora) |
| **4.1.9 Sprint 9 (nuevo)** | Resultados extensos (vista previa, «Ver todo» y CSV) con la nueva **Figura 10**; privacidad de la memoria; modelos retirados por los proveedores y modelos recomendados vigentes (openai/gpt-oss-120b y gemini-3.1-flash-lite); nueva **Tabla 35** | PR #14, #15, #16 y #19 |
| 4.1.10 Pruebas automáticas (antes 4.1.8) | Sección renumerada; tabla con **140 pruebas en Odoo y 28 unitarias** (antes 85 y 22) y filas nuevas (respaldo, resultados extensos, actualización del módulo y privacidad); párrafo de pruebas en el navegador; nueva **Figura 11** (ciclo de desarrollo y pruebas) | Estado actual de las pruebas |

### Resumen de figuras y tablas

| Figura | Título | Sección |
|---|---|---|
| 1 | Modelos de Odoo consultados por el asistente y sus relaciones | 3.1.3 |
| 2 | Diagrama de casos de uso del asistente | 3.2 |
| 3 | Flujo de una consulta y capas de control del asistente (ya existía) | 3.4 |
| 4 | Diagrama de secuencia de una consulta | 3.4.2 |
| 5 | Tecnologías y despliegue del prototipo | 4.1.1 |
| 6 | Componentes del módulo chatbot_assistant | 4.1.2 |
| 7 | Diagrama de clases del módulo chatbot_assistant | 4.1.2 |
| 8 | Regla de guardado de la configuración del modelo de IA | 4.1.6 |
| 9 | Funcionamiento del modelo de respaldo | 4.1.8 |
| 10 | Resultados extensos: vista previa, «Ver todo» y CSV | 4.1.9 |
| 11 | Ciclo de desarrollo y pruebas de cada cambio | 4.1.10 |

- **Tablas nuevas:** 26 (ejemplos de las categorías nuevas del dataset), 34 (cuándo responde el modelo de
  respaldo) y 35 (resultados de los Sprints 8 y 9). Las tablas del Capítulo 4 se renumeraron
  automáticamente (+1 desde la antigua Tabla 26); el total pasó de 33 a 36.
- **Diagramas:** las imágenes del documento son versiones compactas, con letra más grande, de los diagramas
  de `docs/diagramas/`, para que se lean impresos al ancho de la página.

### Lo que no se cambió
- Capítulos 1 y 2, Capítulo 5 en adelante, referencias y anexos: sin cambios de texto (comprobado con la
  comparación del texto completo; solo se corren números de página).
- Los ejemplos JSON de 3.3.3 y 3.5.1 se mantienen: describen el formato de los datos, no son código del
  programa. **Confirmar con la tutora** si también los prefiere como tabla.

### Pendiente en el documento
- [ ] **Capítulo 5:** resultados de la evaluación real (Groq y Gemini), con las consultas de Groq que cortó
      la cuota diaria completadas; limitaciones (cuota de tokens, modelos retirados por los proveedores) y
      trabajo futuro (ruta híbrida, prompt más corto).
- [ ] Al abrir en Word, aceptar «actualizar campos» (o F9) para regenerar los índices de contenido, tablas
      y figuras.
- [ ] Agregar el enlace al repositorio donde el texto dice «se encuentra en el repositorio del proyecto».
- [ ] Revisar en Word la paginación alrededor de las figuras grandes (en algunos casos una figura pasa a la
      página siguiente y deja espacio en blanco).
- [ ] Correcciones de Zotero ya señaladas en `PENDIENTES_TESIS.md`.

---

## Versión 1 · 9 de noviembre de 2026

**Archivo base:** `TESIS_ISMAEL_CALLE.docx` (subido por el autor).
**Archivo entregado:** `TESIS_ISMAEL_CALLE_actualizada.docx`.
**Alcance:** solo lo ya implementado en el código hasta esa fecha, como documento limpio.

| Dónde | Qué se cambió |
|---|---|
| Capítulos 1 y 2 | Correcciones puntuales: «capítulo» con tilde, «revisión de literatura» (no sistemática), referencias a las fases de la metodología, descripción de Odoo 18 y de `display_name`, cita de la OECD y de Malikireddy y Tadanki (2022) |
| Capítulo 3 | Campos permitidos aplicados en el código de cada función; control de permisos por consulta (3.4.4, nueva Tabla 17); intención `conversacion`; entidad `order_state`; esquema de respuesta; manejo de consultas ambiguas y memoria corta (3.4.5); dataset de 62 consultas; Figura 1 (flujo de una consulta) |
| Capítulo 4 | Sprints 2 a 7 (módulo, casos de uso, seguridad, auditoría y métricas, rendimiento y configuración, conversación y memoria) y sección de pruebas automáticas, con sus tablas de resultados |
| Referencias | Malikireddy y Tadanki (2022) en formato APA y en orden alfabético |
| Configuración del documento | Actualización de campos al abrir, para regenerar los índices |
