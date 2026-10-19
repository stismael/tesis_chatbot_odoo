# -*- coding: utf-8 -*-
"""Avisos sobre el alcance de lo que el usuario puede ver según los permisos de Odoo."""

# Grupos con los que Odoo muestra TODOS los documentos de un modelo (sin reglas de "solo los míos").
FULL_ACCESS_GROUPS = {
    "sale.order": ("sales_team.group_sale_salesman_all_leads",),
    "account.move": ("account.group_account_invoice", "account.group_account_readonly"),
}

SCOPE_NOTE = " Solo se incluyen los documentos a los que tienes acceso."


def scope_note(env, model):
    """Texto a añadir cuando el usuario solo ve parte de los documentos del modelo."""
    if env.su:
        return ""
    groups = FULL_ACCESS_GROUPS.get(model)
    if not groups or any(env.user.has_group(g) for g in groups):
        return ""
    return SCOPE_NOTE
