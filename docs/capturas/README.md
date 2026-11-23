# Capturas del prototipo para la tesis

Capturas reales de Odoo 18 con el asistente funcionando, tomadas el 23 de noviembre de 2026 para la versión 5
del documento (Capítulo 4, Sprints 2 a 9).

## Cómo se obtuvieron

1. Base `odoo18_chatbot` creada como en `scripts/initialize-database.ps1`: módulos
   `base,contacts,product,sale_management,stock,account` sin datos demo, luego `chatbot_test_data` y
   `chatbot_assistant`, y datos generados con `scripts/generate_synthetic_data.py`
   (900 pedidos confirmados, 144 cotizaciones, 39 cancelados y 656 facturas, los mismos de la evaluación).
   Se cargó además el idioma español (`--load-language=es_419`) para que la interfaz se vea en español.
2. `scripts/capturas/configurar_asistente.py` (odoo shell): Groq `openai/gpt-oss-120b` como principal y Gemini
   `gemini-3.1-flash-lite` como respaldo; usuario administrador en español y contraseña de prueba para el
   vendedor Diego Salinas (grupo Ventas, sin Facturación).
3. `scripts/capturas/limpiar_chat.py` deja el chat y la auditoría vacíos antes de capturar.
4. `scripts/capturas/tomar_capturas.js` (Playwright) escribe las consultas en el chat con la IA real y captura
   los Ajustes, los permisos, la auditoría, las métricas y «Ver todo»; `recortar_chat.js` recorta cada
   conversación.

| Archivo | Figura de la tesis |
|---|---|
| `f_chat.png` | Consulta de una factura y del stock en el chat (Sprint 2) |
| `f_help.png` | Ayuda con /help (Sprint 2) |
| `f_permiso.png` | Usuario sin permiso para facturas (Sprint 4) |
| `c7_permisos.png` | Tabla de permisos por consulta (Sprint 4) |
| `c8_auditoria.png`, `c9_metricas.png` | Auditoría y métricas (Sprint 5) |
| `c6_ajustes.png` | Ajustes del proveedor de IA (Sprint 6) |
| `f_memoria.png` | Seguimiento, aclaración y rechazo (Sprint 7) |
| `c6b_respaldo.png` | Modelo de respaldo (Sprint 8) |
| `f_extenso.png`, `c5_ver_todo.png` | Resultado extenso y «Ver todo» (Sprint 9) |
