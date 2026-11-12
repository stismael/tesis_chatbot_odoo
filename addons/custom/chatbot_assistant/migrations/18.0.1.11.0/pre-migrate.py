# -*- coding: utf-8 -*-


def migrate(cr, version):
    """
    Re-enlaza los parámetros por defecto del módulo (data/default_params.xml) cuyo registro original
    ya no existe pero sí hay otro con la misma clave. Pasaba en versiones anteriores al paso 4: al
    desactivar el asistente, Odoo borraba el parámetro y al reactivarlo creaba uno nuevo sin enlace.
    Sin esto, la actualización intenta crear el parámetro de nuevo y falla por clave duplicada.
    """
    cr.execute(
        """
        UPDATE ir_model_data imd
           SET res_id = icp.id
          FROM ir_config_parameter icp
         WHERE imd.module = 'chatbot_assistant'
           AND imd.model = 'ir.config_parameter'
           AND imd.name LIKE 'param\\_chatbot\\_%%'
           AND NOT EXISTS (SELECT 1 FROM ir_config_parameter x WHERE x.id = imd.res_id)
           AND icp.key = 'chatbot_assistant.' || substring(imd.name FROM 15)
        """
    )
