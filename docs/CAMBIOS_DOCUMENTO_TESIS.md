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
