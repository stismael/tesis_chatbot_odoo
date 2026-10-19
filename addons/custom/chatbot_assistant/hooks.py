# -*- coding: utf-8 -*-
"""Hooks de instalación/actualización del módulo chatbot_assistant."""
from .services.llm_client import DEFAULT_TIMEOUT


def _migrate_deprecated_model(env):
    icp = env["ir.config_parameter"].sudo()
    current = (icp.get_param("chatbot_assistant.model") or "").strip()
    deprecated = {"", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest"}
    if current in deprecated:
        icp.set_param("chatbot_assistant.model", "gemini-2.5-flash")


def _ensure_timeout_default(env):
    """Asigna el timeout por defecto si falta o no es un número positivo."""
    icp = env["ir.config_parameter"].sudo()
    raw = (icp.get_param("chatbot_assistant.timeout") or "").strip()
    try:
        value = int(raw) if raw else 0
    except ValueError:
        value = 0
    if value <= 0:
        icp.set_param("chatbot_assistant.timeout", str(DEFAULT_TIMEOUT))


def post_init_hook(env):
    _migrate_deprecated_model(env)
    _ensure_timeout_default(env)


def uninstall_hook(env):
    # No borramos la API key automáticamente (puede reutilizarla el admin).
    pass
