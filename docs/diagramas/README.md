# Diagramas para la tesis

Diagramas del prototipo hechos a partir del código real, para reemplazar los fragmentos de código de los
Capítulos 3 y 4 (recomendación de la tutora). Cada diagrama está en PNG (alta resolución, para Word) y en
SVG (vectorial). Sus fuentes están en `fuentes/` (formato Mermaid), así que se pueden corregir y volver a
generar.

| # | Archivo | Tipo | Dónde va en la tesis | Reemplaza |
|---|---|---|---|---|
| 1 | `01_contexto.png` | Arquitectura, nivel de contexto (C4 nivel 1) | Inicio del Capítulo 4 (arquitectura de la solución) o 3.4 | — (nuevo) |
| 2 | `02_contenedores.png` | Arquitectura, nivel de contenedores (C4 nivel 2) y tecnologías | Capítulo 4, arquitectura de la solución | Explicación textual de tecnologías |
| 3 | `03_despliegue.png` | Despliegue | 4.1.1 Sprint 1 | `docker-compose.yml` y `initialize-database.ps1` |
| 4 | `04_componentes.png` | Componentes del módulo | 4.1.2 Sprint 2 | Extracto de `discuss_channel.py` |
| 5 | `05_casos_uso.png` | Casos de uso (UML) | 3.2, antes de las tablas CU-01 a CU-05 | — (nuevo) |
| 6 | `06_clases.png` | Clases del módulo | 4.1.2 Sprint 2 (o 4.1.4 y 4.1.5) | Extractos del orquestador y de los modelos |
| 7 | `07_modelo_datos.png` | Modelo de datos de Odoo consultado | 3.1.3, junto a las Tablas 3 y 6 | — (complementa las tablas) |
| 8 | `08_secuencia_consulta.png` | Secuencia de una consulta | 3.4 o 4.1.3 Sprint 3 | Extractos de los handlers y del validador |
| 9 | `09_actividad_respaldo.png` | Actividad: modelo de respaldo | Nueva sección del modelo de respaldo (Capítulo 4) | — (nuevo) |
| 10 | `10_actividad_guardado.png` | Actividad: regla de guardado de Ajustes | 4.1.6 Sprint 6 (configuración del modelo) | Extracto de `llm_client.py` |
| 11 | `11_secuencia_ver_todo.png` | Secuencia: «Ver todo» y CSV | Nueva sección de resultados extensos (Capítulo 4) | — (nuevo) |
| 12 | `12_ciclo_desarrollo.png` | Proceso: ciclo de desarrollo y pruebas | 4.1.8 Pruebas automáticas o metodología | — (nuevo) |

## Diagramas ilustrados (vista general)

Versión con íconos, logos y pasos numerados, más fácil de leer para alguien que no conoce UML. Sirven para
la arquitectura, la sustentación y para abrir cada sección; los diagramas UML de arriba quedan para el
detalle técnico.

| Archivo | Muestra | Dónde va en la tesis |
|---|---|---|
| `ilustrados/A1_flujo_consulta.png` | Cómo se responde una consulta, en 9 pasos | Arquitectura de la solución (Capítulo 4) o junto a la Figura 1 |
| `ilustrados/A2_tecnologias.png` | Tecnologías y despliegue (Odoo, Python, PostgreSQL, Docker, Gemini, Groq, GitHub) | Sprint 1 o arquitectura |
| `ilustrados/A3_modelo_respaldo.png` | Cuándo responde el modelo de respaldo y la regla de guardado | Sección del modelo de respaldo |
| `ilustrados/A4_resultados_extensos.png` | Vista previa, «Ver todo» y CSV | Sección de resultados extensos |

Se generan con `node scripts/diagramas/ilustrado.js docs/diagramas/ilustrados/fuentes docs/diagramas/ilustrados`
(requiere `npm install playwright simple-icons@13.21.0 @tabler/icons@3.24.0`). Los logos son de Simple Icons
y los íconos de Tabler Icons, ambos de licencia libre.

## Notas para el documento

- **Figura 1 actual** («Flujo de una consulta y capas de control del asistente»): se mantiene; el
  diagrama 8 la complementa con el detalle de quién llama a quién.
- **Código del generador de datos** (Sprint 1): se reemplaza por las tablas de volúmenes que ya existen
  (Tablas 5 y 26) y una frase con el enlace al repositorio.
- **Pie de cada figura:** «Elaboración propia» (en formato APA, igual que la Figura 1).
- **Tamaño en Word:** insertar los PNG con el ancho de la página; los de secuencia (8 y 11) se leen mejor
  en una página horizontal o a ancho completo.
- **Código:** queda en el repositorio (enlace en el documento) o en un anexo corto, según decida la tutora.

## Volver a generar

```bash
npm install mermaid@11.4.1 playwright      # una sola vez, en la raíz del proyecto
node scripts/diagramas/render.js docs/diagramas/fuentes docs/diagramas
```

`scripts/diagramas/render.js` abre cada fuente en Chromium con Mermaid (tema «neutral», fuente Arial) y guarda el SVG y un
PNG a escala 3×.
