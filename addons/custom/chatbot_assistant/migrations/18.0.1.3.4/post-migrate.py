# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Timeout por defecto 45s y mensajes/reintentos LLM (18.0.1.3.4)."""
    cr.execute(
        """
        UPDATE ir_config_parameter
           SET value = '45'
         WHERE key = 'chatbot_assistant.timeout'
           AND (
                value IS NULL
                OR value = ''
                OR value ~ '^[0-9]+$' AND value::integer < 45
           )
        """
    )
