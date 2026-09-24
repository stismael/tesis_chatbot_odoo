# -*- coding: utf-8 -*-


def migrate(cr, version):
    cr.execute(
        """
        UPDATE ir_config_parameter
           SET value = 'gemini-2.5-flash'
         WHERE key = 'chatbot_assistant.model'
           AND (
                value IS NULL
                OR value IN ('', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-flash-latest')
           )
        """
    )
