# Capítulo 4/5 — Notas de implementación del prototipo

## Sprint 1 (completado previamente)
Laboratorio Docker Compose (PostgreSQL 16 + Odoo 18) y módulo `chatbot_test_data` con datos sintéticos.

## Interfaz Discuss (estilo OdooBot)

La UX principal es un DM en **Discuss** con el contacto **Asistente ERP**:

- `data/chatbot_bot_data.xml` — partner del bot
- `models/discuss_channel.py` — hook `_message_post_after_hook`
- `models/chatbot_discuss_service.py` — orquestación + respuesta
- `models/mail_bot.py` — evita que OdooBot interfiera en ese DM
- Menú **Chatbot → Abrir chat**

El usuario solo abre el chat y pregunta; no completa formularios.

## Sprint 3 — CU-01 y CU-02
Handlers ORM:
- `services/handlers/factura.py`
- `services/handlers/stock.py`
Few-shots incluidos en `services/prompt_builder.py`.

## Sprint 4 — CU-03, CU-04 y memoria corta
Handlers:
- `services/handlers/ventas.py`
- `services/handlers/vendedor.py`
Memoria corta en `chatbot.session` (`pending_intent`, `pending_entities_json`, últimos mensajes).

## Sprint 5 — Evaluación
- Dataset: `data/eval/eval_dataset.jsonl` (50 consultas)
- Runner: `scripts/run-chatbot-eval.ps1`
- Auditoría: modelo `chatbot.query.log`
- Guía: `docs/CHATBOT_ASSISTANT.md`

## Cómo configurar antes de evaluar
1. Obtener API key en Google AI Studio
2. Odoo → Chatbot → Ajustes → pegar API key → Guardar
3. Ejecutar `.\scripts\run-chatbot-eval.ps1`

## Métricas esperadas (Cap. 5)
- Intent Accuracy
- Entity Accuracy
- Execution Accuracy
- Latencia promedio (ms)
- Tasa de rechazo correcto en fuera de alcance
