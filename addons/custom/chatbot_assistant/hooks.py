# -*- coding: utf-8 -*-
"""Hooks de instalación/actualización del módulo chatbot_assistant."""


def _migrate_deprecated_model(env):
    icp = env["ir.config_parameter"].sudo()
    current = (icp.get_param("chatbot_assistant.model") or "").strip()
    deprecated = {"", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest"}
    if current in deprecated:
        icp.set_param("chatbot_assistant.model", "gemini-2.5-flash")


def _ensure_timeout_default(env):
    """Sube timeouts antiguos muy bajos (p. ej. 30s) al nuevo default 45s."""
    icp = env["ir.config_parameter"].sudo()
    raw = (icp.get_param("chatbot_assistant.timeout") or "").strip()
    try:
        value = int(raw) if raw else 0
    except ValueError:
        value = 0
    if value < 45:
        icp.set_param("chatbot_assistant.timeout", "45")


def post_init_hook(env):
    _migrate_deprecated_model(env)
    _ensure_timeout_default(env)


def uninstall_hook(env):
    # No borramos la API key automáticamente (puede reutilizarla el admin).
    pass
