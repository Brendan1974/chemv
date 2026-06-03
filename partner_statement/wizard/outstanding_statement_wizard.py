# Copyright 2018 ForgeFlow, S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import logging

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OutstandingStatementWizard(models.TransientModel):
    """Outstanding Statement wizard."""

    _name = "outstanding.statement.wizard"
    _inherit = "statement.common.wizard"
    _description = "Outstanding Statement Wizard"

    def _prepare_statement(self):
        res = super()._prepare_statement()
        res.update(
            {
                "is_outstanding": True,
            }
        )
        return res

    def _print_report(self, report_type):
        self.ensure_one()
        data = self._prepare_statement()
        if report_type == "xlsx":
            report_name = "p_s.report_outstanding_statement_xlsx"
        else:
            report_name = "partner_statement.outstanding_statement"
        partners = self.env["res.partner"].browse(data["partner_ids"])
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(partners, data=data)
        )

    def _export(self, report_type):
        """Default export is PDF."""
        return self._print_report(report_type)

    # ------------------------------------------------------------------
    # chemv customisation ported from v16
    # ------------------------------------------------------------------
    def button_send_mail(self):
        """Render the outstanding statement as PDF and email it to each selected partner."""
        Mail = self.env["mail.mail"]
        Attachment = self.env["ir.attachment"]
        if not self._context.get("active_ids"):
            return
        report = self.env.ref(
            "partner_statement.action_print_outstanding_statement",
            raise_if_not_found=False,
        )
        template_rec = self.env.ref(
            "partner_statement.email_template_outstanding_statement_ap",
            raise_if_not_found=False,
        )
        if not report or not template_rec:
            raise UserError(
                "Outstanding-statement mail template or report action is missing."
            )
        for partner in self.env["res.partner"].browse(self._context["active_ids"]):
            data = self._prepare_statement()
            data["partner_ids"] = [partner.id]
            if report.report_type in ("qweb-html", "qweb-pdf"):
                result, fmt = report._render_qweb_pdf(
                    "partner_statement.outstanding_statement",
                    [partner.id],
                    data=data,
                )
            else:
                rendered = report._render([partner.id])
                if not rendered:
                    raise UserError(
                        f"Unsupported report type {report.report_type} found."
                    )
                result, fmt = rendered
            result = base64.b64encode(result)
            report_name = report.report_name or f"report.{report.report_name}"
            ext = f".{fmt}"
            if not report_name.endswith(ext):
                report_name += ext
            mail = Mail.create({})
            attachment = Attachment.create(
                {
                    "name": report_name,
                    "datas": result,
                    "type": "binary",
                    "res_model": "mail.message",
                    "res_id": mail.mail_message_id.id,
                }
            )
            body = template_rec._render_field(
                "body_html",
                [partner.id],
                compute_lang=False,
                options={"post_process": True},
            )[partner.id]
            mail.write(
                {
                    "attachment_ids": [(6, 0, [attachment.id])],
                    "body_html": body,
                    "subject": template_rec.subject,
                    "recipient_ids": [(4, partner.id)],
                }
            )
            mail.send()
