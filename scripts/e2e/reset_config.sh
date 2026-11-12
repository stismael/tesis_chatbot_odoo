#!/bin/sh
docker exec tdb psql -U odoo -d web1 -q -c "
DELETE FROM ir_config_parameter WHERE key IN ('chatbot_assistant.provider','chatbot_assistant.api_key','chatbot_assistant.model','chatbot_assistant.active','chatbot_assistant.last_verified');
INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date) VALUES
 ('chatbot_assistant.provider','gemini',1,1,now(),now()),
 ('chatbot_assistant.api_key','AIzaCLAVE-GEMINI',1,1,now(),now()),
 ('chatbot_assistant.model','gemini-2.5-flash',1,1,now(),now()),
 ('chatbot_assistant.active','True',1,1,now(),now());"
