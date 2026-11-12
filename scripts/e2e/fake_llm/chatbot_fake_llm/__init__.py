"""Módulo de servidor solo para pruebas e2e: reemplaza las llamadas reales al proveedor de IA."""
from odoo.addons.chatbot_assistant.services import llm_client

MODELS = {
    "gemini": ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"],
    "groq": ["llama-3.3-70b-versatile", "qwen/qwen3-32b", "openai/gpt-oss-120b"],
}
PREFIX = {"gemini": "AIza", "groq": "gsk_"}


def _check(config):
    key = (config.get("api_key") or "").strip()
    if not key:
        raise llm_client.LLMClientError("missing_key")
    if not key.startswith(PREFIX[config["provider"]]):
        raise llm_client.LLMClientError("auth")


def fake_test_connection(config):
    _check(config)
    return {"ok": True, "provider": config["provider"], "model": config["model"], "latency_ms": 7,
            "message": "ok", "models": []}


def fake_list_models(config):
    _check(config)
    return [{"id": m, "display_name": m, "description": "", "input_token_limit": 1000, "output_token_limit": 100}
            for m in MODELS[config["provider"]]]


llm_client.test_connection = fake_test_connection
llm_client.list_models = fake_list_models
