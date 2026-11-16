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
    if not key.startswith(PREFIX[config["provider"]]) or "INVALIDA" in key:
        raise llm_client.LLMClientError("auth")
    if "CAIDO" in key:  # simula un proveedor caído (fallo pasajero)
        raise llm_client.LLMClientError("server")


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


# Respuestas simuladas de la IA para el chat (pruebas e2e de resultados extensos). La clave es un
# fragmento de la consulta; el valor, la intención y las entidades que devolvería el modelo.
CHAT_ANSWERS = [
    ("facturas de comercial andina", "consultar_factura", {"customer_name": "Comercial Andina S.A."}),
    ("facturas de motopartes ecuador", "consultar_factura", {"customer_name": "Motopartes Ecuador S.A."}),
    ("ventas de jessica", "consultar_ventas_cliente", {"customer_name": "Jessica Paola Benítez"}),
    ("lista los pedidos de comercial andina", "consultar_ventas_cliente", {"customer_name": "Comercial Andina S.A."}),
    ("ventas de comercial andina", "consultar_ventas_cliente", {"customer_name": "Comercial Andina S.A."}),
    ("lista las ventas del fil-m01", "consultar_ventas_cliente", {"product_code": "FIL-M01"}),
    ("stock y facturación del fil-m01", "consultar_stock_facturacion_producto", {"product_code": "FIL-M01"}),
    ("vendedor de comercial andina", "consultar_vendedor_cliente", {"customer_name": "Comercial Andina S.A."}),
]


def fake_complete_once(config, system_prompt, user_message, meta, response_schema=None, **kwargs):
    _check(config)
    query = user_message.split("Consulta del usuario:\n", 1)[-1].split("\n", 1)[0].lower()
    meta.update({"provider": config["provider"], "model": config["model"], "retries": 0})
    for fragment, intent, values in CHAT_ANSWERS:
        if fragment in query:
            return {"intent": intent, "entities": values, "status": "ready", "missing_entities": []}
    return {"intent": "conversacion", "entities": {}, "status": "ready", "missing_entities": [],
            "reply": "Hola, soy el asistente de pruebas."}


llm_client._complete_once = fake_complete_once
