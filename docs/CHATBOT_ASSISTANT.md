# Chatbot Assistant — Guía de uso (tesis)

## Qué incluye

Módulo Odoo `chatbot_assistant` para consultas de **solo lectura**:

| CU | Intención | Ejemplo |
|----|-----------|---------|
| CU-01 | `consultar_factura` | ¿Está pagada la factura INV/2026/00001? |
| CU-02 | `consultar_stock` | ¿Cuántas unidades hay del producto FIL-M01? |
| CU-03 | `consultar_ventas_cliente` | ¿Qué ventas tiene Comercial Andina S.A.? |
| CU-04 | `consultar_vendedor_cliente` | ¿Quién es el vendedor de Moto Racing Cuenca? |
| — | `fuera_de_alcance` | Crear/editar/borrar o temas no comerciales |

Arquitectura: **NL → JSON (LLM) → validación → handler ORM → respuesta con plantilla**.

- Sin RAG, sin SQL libre.
- Memoria corta de sesión (2–3 turnos) para aclaraciones.
- API key en **Ajustes del módulo**, no en `.env`.

## Instalación

```powershell
.\scripts\start.ps1
.\scripts\update-module.ps1 -ModuleName chatbot_assistant
```

Si el módulo no aparece, actualice la lista de aplicaciones en Odoo (modo desarrollador) e instale **Chatbot Assistant**.

Dependencias: `contacts`, `product`, `sale_management`, `stock`, `account`, `mail`, `base_setup`.

## Configurar el LLM (obligatorio)

1. Obtenga una API key gratuita en [Google AI Studio](https://aistudio.google.com/apikey).
2. En Odoo: **Chatbot → Ajustes**.
3. Complete:
   - Proveedor: `Google Gemini`
   - API Key: (pegue la clave; campo password)
   - Modelo: `gemini-2.5-flash` (recomendado; no use `gemini-2.0-flash`)
   - Temperature: `0.1`
4. Pulse **Listar modelos** para ver IDs vigentes del proveedor.
5. Pulse **Probar conexión** (valida key + modelo y muestra latencia).
6. Guarde.

Errores controlados que verá el usuario (no se queda colgado):
- Timeout
- 401 API Key inválida
- 403 Permiso denegado
- 429 Cuota / rate limit
- 5xx Error del proveedor

Alternativa: proveedor `Groq` + modelo tipo `llama-3.3-70b-versatile`.

## Usar el chat (Discuss)

No hace falta un menú especial para chatear.

1. Configure la API key en **Chatbot → Ajustes** (solo administradores).
2. Abra **Discuss**.
3. En **Direct Messages** verá **Asistente ERP** (se crea solo al iniciar sesión, como OdooBot).
4. Escriba la pregunta y envíe.

Si no aparece, cierre sesión y vuelva a entrar, o busque “Asistente ERP” con el `+` de Direct Messages.

## Evaluación automatizada (Cap. 5)

Dataset: `data/eval/eval_dataset.jsonl` (50 consultas etiquetadas).

```powershell
.\scripts\run-chatbot-eval.ps1
# opcional: -Limit 10  para prueba rápida
```

Salida: `data/eval/results/eval_summary.json` con:

- Intent Accuracy
- Entity Accuracy
- Execution Accuracy
- Latencia promedio (ms)

## Decisiones de diseño (para Cap. 4)

1. **Gemini Flash**: costo cero, buen español, JSON structured output.
2. **Sin RAG**: dominio tabular cerrado + whitelist de intenciones; el contexto va en el prompt (schema injection + few-shot).
3. **Memoria corta**: solo pending intent/entities y últimos turnos; no vector DB.
4. **API en Ajustes**: patrón `res.config.settings` / `ir.config_parameter`.
5. **Respuestas con plantilla + ORM**: el LLM no inventa montos; las cifras salen de Odoo.

## Estructura del módulo

```
addons/custom/chatbot_assistant/
  models/          session, message, query.log, settings, orchestrator
  services/        llm_client, prompt_builder, validator, handlers/
  views/           chat, auditoría, ajustes, menús
  security/        grupos usuario/manager
```
