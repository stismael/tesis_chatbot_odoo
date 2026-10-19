# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Timeout por defecto de 45 s a 20 s (18.0.1.7.0); un valor personalizado se conserva."""
    cr.execute(
        """
        UPDATE ir_config_parameter
           SET value = '20'
         WHERE key = 'chatbot_assistant.timeout'
           AND (value IS NULL OR value IN ('', '45'))
        """
    )
