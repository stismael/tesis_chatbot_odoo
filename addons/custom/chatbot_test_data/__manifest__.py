{
    "name": "Chatbot Test Data",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "summary": "Datos sintéticos deterministas para pruebas de asistente conversacional",
    "description": """
        Genera datos de prueba controlados para tesis sobre asistente conversacional:
        clientes, productos, inventario, pedidos, facturas y pagos.
        Semilla fija: random.seed(2026).
    """,
    "author": "Odoo18 Community Chatbot Project",
    "license": "LGPL-3",
    "depends": [
        "contacts",
        "product",
        "sale_management",
        "stock",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "wizard/chatbot_test_data_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
}
