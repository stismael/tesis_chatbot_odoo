{
    "name": "Chatbot Assistant",
    "version": "18.0.1.9.0",
    "category": "Productivity",
    "summary": "Asistente conversacional en Discuss (estilo OdooBot) para Odoo 18",
    "description": """
        Asistente conversacional de solo lectura integrado a Discuss:

        - Aparece en Direct Messages como "Asistente ERP" (igual que OdooBot)
        - NL -> JSON (LLM) -> validación -> ORM
        - API key en Ajustes del módulo
        - Memoria corta y auditoría
    """,
    "author": "Odoo18 Community Chatbot Project",
    "license": "LGPL-3",
    "depends": [
        "base",
        "base_setup",
        "mail",
        "mail_bot",
        "contacts",
        "product",
        "sale_management",
        "stock",
        "account",
    ],
    "data": [
        "security/chatbot_security.xml",
        "security/ir.model.access.csv",
        "data/default_params.xml",
        "data/chatbot_bot_data.xml",
        "data/ir_cron.xml",
        "data/chatbot_intent_permission_data.xml",
        "data/chatbot_llm_model_data.xml",
        "views/chatbot_llm_model_views.xml",
        "views/res_config_settings_views.xml",
        "views/chatbot_llm_result_wizard_views.xml",
        "views/chatbot_session_views.xml",
        "views/chatbot_query_log_views.xml",
        "views/chatbot_intent_permission_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
    "post_init_hook": "post_init_hook",
    "assets": {
        "web.assets_backend": [
            "chatbot_assistant/static/src/discuss/thread_model_patch.js",
            "chatbot_assistant/static/src/discuss/composer_patch.js",
        ],
    },
}
