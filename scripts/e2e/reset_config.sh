#!/bin/sh
# Deja la configuración de partida de la prueba: Gemini guardado con su clave y sin respaldo.
# Actualiza los parámetros en lugar de borrarlos, para no romper su enlace con el módulo.
docker exec tdb psql -U odoo -d web1 -q -c "
DELETE FROM ir_config_parameter WHERE key IN ('chatbot_assistant.last_verified','chatbot_assistant.fallback_active','chatbot_assistant.fallback_provider','chatbot_assistant.fallback_api_key','chatbot_assistant.fallback_model','chatbot_assistant.fallback_last_verified');
INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date) VALUES
 ('chatbot_assistant.provider','gemini',1,1,now(),now()),
 ('chatbot_assistant.api_key','AIzaCLAVE-GEMINI',1,1,now(),now()),
 ('chatbot_assistant.model','gemini-2.5-flash',1,1,now(),now()),
 ('chatbot_assistant.active','True',1,1,now(),now())
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, write_date = now();"
