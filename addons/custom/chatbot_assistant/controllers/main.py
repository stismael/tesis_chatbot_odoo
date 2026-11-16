# -*- coding: utf-8 -*-
"""Descarga en CSV de un resultado extenso del asistente."""
import re

from odoo import fields, http
from odoo.exceptions import MissingError, UserError
from odoo.http import request

from ..services.result_set import build_csv


class ChatbotResultController(http.Controller):

    @http.route("/chatbot_assistant/resultado/<int:log_id>/csv", type="http", auth="user", methods=["GET"])
    def download_result_csv(self, log_id, **kwargs):
        """
        Genera el CSV en el momento, con el usuario que lo pide: solo el dueño de la consulta (o el
        administrador del chatbot) puede descargarlo y solo salen los registros que todavía puede ver.
        """
        log = request.env["chatbot.query.log"].browse(log_id)
        try:
            records = log.exists()._result_records() if log.exists() else None
        except (MissingError, UserError):
            records = None
        if records is None:
            return request.not_found()
        log.sudo().write({
            "csv_downloads": log.sudo().csv_downloads + 1,
            "last_csv_download": fields.Datetime.now(),
        })
        name = re.sub(r"[^\w\-]+", "_", log.result_title or "resultado", flags=re.UNICODE).strip("_")
        return request.make_response(build_csv(records), headers=[
            ("Content-Type", "text/csv; charset=utf-8"),
            ("Content-Disposition", http.content_disposition(f"{name[:60] or 'resultado'}.csv")),
        ])
