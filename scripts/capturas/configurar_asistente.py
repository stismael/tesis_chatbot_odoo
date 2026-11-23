ICP = env["ir.config_parameter"].sudo()
for k, v in {"provider": "groq", "api_key": "gsk_proxy-injected", "model": "openai/gpt-oss-120b", "active": "True",
             "fallback_active": "True", "fallback_provider": "gemini", "fallback_api_key": "AIza-proxy-injected",
             "fallback_model": "gemini-3.1-flash-lite", "timeout": "20"}.items():
    ICP.set_param("chatbot_assistant." + k, v)
admin = env.ref("base.user_admin")
admin.write({"lang": "es_419", "tz": "America/Guayaquil", "name": "Ismael Calle"})
u = env["res.users"].search([("login", "=", "diego.salinas@demo-motos.ec")])
u.write({"password": "demo", "lang": "es_419", "tz": "America/Guayaquil"})
print("grupos diego:", [g.full_name for g in u.groups_id if "Ventas" in g.full_name or "Sales" in g.full_name or "Contab" in g.full_name or "Factur" in g.full_name or "Invent" in g.full_name])
print("company:", env.company.name)
print("params:", [p.key for p in ICP.search([("key", "like", "chatbot_assistant.%")])])
env.cr.commit()
