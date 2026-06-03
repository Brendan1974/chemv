# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class OutstandingStatementWizard(models.TransientModel):
    """Outstanding Statement wizard."""

    _inherit = "outstanding.statement.wizard"

    def sent_activity_statement_outstanding(self):
        for each in self._context.get('active_ids') or []:
            partner = self.env['res.partner'].browse(each)
            if partner:
                data = self._prepare_statement()
                self.env['activity.statement.record'].create({
                    'date_end': data.get('date_end'),
                    'show_aging_buckets': data.get('show_aging_buckets'),
                    'filter_partners_non_due': data.get('is_activity'),
                    'account_type': data.get('account_type'),
                    'aging_type': data.get('aging_type'),
                    'filter_negative_balances': data.get('filter_negative_balances'),
                    'partner_ids': partner.id,
                    'report_type': 'outstanding',
                    'company_id': self.company_id and self.company_id.id or False,
                    'is_sent': False,
                })


class ActivityStatementWizard(models.TransientModel):
    """Activity Statement wizard."""

    _inherit = "activity.statement.wizard"

    def sent_activity_statement_button(self):
        for each in self._context.get('active_ids') or []:
            partner = self.env['res.partner'].browse(each)
            if partner:
                data = self._prepare_statement()
                self.env['activity.statement.record'].create({
                    'date_end': data.get('date_end'),
                    'date_start': data.get('date_start'),
                    'show_aging_buckets': data.get('show_aging_buckets'),
                    'filter_partners_non_due': data.get('is_activity'),
                    'account_type': data.get('account_type'),
                    'aging_type': data.get('aging_type'),
                    'filter_negative_balances': data.get('filter_negative_balances'),
                    'is_activity': data.get('is_activity'),
                    'partner_ids': partner.id,
                    'report_type': 'activity',
                    'company_id': self.company_id and self.company_id.id or False,
                    'is_sent': False,
                })


class ActivityStatementRecord(models.Model):
    _name = 'activity.statement.record'
    _description = 'Activity Statement Record (queue for email-based delivery)'

    is_sent = fields.Boolean(string='Is Sent', default=False)
    date_end = fields.Date(required=True, default=fields.Date.context_today)
    show_aging_buckets = fields.Boolean(default=False)
    filter_partners_non_due = fields.Boolean(default=False)
    account_type = fields.Selection(
        [("asset_receivable", "Receivable"), ("liability_payable", "Payable")],
    )
    aging_type = fields.Selection(
        [("days", "Age by Days"), ("months", "Age by Months")],
        string="Aging Method",
        required=True,
    )
    date_start = fields.Date()
    filter_negative_balances = fields.Boolean("Exclude Negative Balances")
    is_activity = fields.Boolean("Is Activity", default=False)
    partner_ids = fields.Many2one("res.partner", string="Vendor", domain="[('is_company', '=', True)]")
    report_type = fields.Selection([('activity', 'Activity'), ('outstanding', 'Outstanding')], string='Report Type')
    company_id = fields.Many2one('res.company', string="Company")

    def _prepare_statement_ap(self):
        return {
            "date_end": self.date_end,
            "show_aging_buckets": self.show_aging_buckets,
            "filter_non_due_partners": self.filter_partners_non_due,
            "account_type": self.account_type,
            "aging_type": self.aging_type,
            "filter_negative_balances": self.filter_negative_balances,
            "date_start": self.date_start,
            "is_activity": self.is_activity,
            "partner_ids": self.partner_ids,
        }

    def sent_activity_statement_by_email_ap(self):
        records = self.env['activity.statement.record'].search([('is_sent', '=', False)], limit=20)
        for record in records:
            data = record._prepare_statement_ap()
            partner = record.partner_ids

            if partner.email:
                partner_email = partner.email
            else:
                child = partner.child_ids.filtered(lambda x: x.type == 'invoice' and x.email)
                partner_email = child[:1].email if child else False

            if not partner_email:
                _logger.warning("No email found for partner %s. Skipping...", partner.display_name)
                record.is_sent = True
                continue

            try:
                if record.report_type == 'activity':
                    template = self.env.ref('ap_partner_statment_extended.email_template_partner_statement')
                    report_action = self.env.ref('partner_statement.action_print_activity_statement')
                    report_xml_id = 'partner_statement.activity_statement'
                else:
                    template = self.env.ref('ap_partner_statment_extended.email_template_partner_outstanding_statement')
                    report_action = self.env.ref('partner_statement.action_print_outstanding_statement')
                    report_xml_id = 'partner_statement.outstanding_statement'

                report_action._render_qweb_pdf(report_xml_id, [partner.id], data=data)

                ctx = {
                    'default_model': 'res.partner',
                    'default_res_id': partner.id,
                    'default_email_to': partner_email,
                    'default_email_from': partner.company_id.email or self.env.user.company_id.email,
                    'company_id': partner.company_id.id,
                    'data': data,
                }

                template = template.with_context(**ctx).with_company(partner.company_id.id)
                mail_id = template.send_mail(
                    partner.id,
                    force_send=True,
                    raise_exception=False,
                )

                if mail_id:
                    _logger.info("Email sent successfully to %s for partner %s", partner_email, partner.display_name)
                else:
                    _logger.warning("Template returned False for partner %s", partner.display_name)

            except Exception as e:
                _logger.error("Failed to send email for %s: %s", partner.display_name, e)

            record.is_sent = True
