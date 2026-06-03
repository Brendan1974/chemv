# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"

    def _get_followup_report_lines(self, options):
        """Override to include unreconciled AML rows from partner child contacts."""
        partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
        if not partner:
            return []

        lang_code = partner.lang or get_lang(self.env).code
        lines = []
        res = {}
        today = fields.Date.today()
        line_num = 0

        allowed_companies = self.env.company.search([
            ('id', 'child_of', self.env.context.get('allowed_company_ids', self.env.company.id))
        ])

        def _collect(target_partner):
            for aml in target_partner.unreconciled_aml_ids.sorted().filtered(
                lambda l: not l.currency_id.is_zero(l.amount_residual_currency)
            ):
                if aml.company_id in allowed_companies:
                    currency = aml.currency_id or aml.company_id.currency_id
                    res.setdefault(currency, []).append(aml)

        _collect(partner)
        for child_partner in partner.child_ids:
            _collect(child_partner)

        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            columns = []
            for aml in aml_recs:
                amount = aml.amount_residual_currency if aml.currency_id else aml.amount_residual
                invoice_date = {
                    'name': format_date(self.env, aml.move_id.invoice_date or aml.date, lang_code=lang_code),
                    'class': 'date',
                    'style': 'white-space:nowrap;text-align:left;',
                    'template': 'account_followup.line_template',
                }
                date_due_value = format_date(self.env, aml.date_maturity, lang_code=lang_code)
                total += amount or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else False
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += amount or 0
                date_due = {
                    'name': date_due_value,
                    'class': 'date',
                    'style': 'white-space:nowrap;text-align:left;',
                    'template': 'account_followup.line_template',
                }
                if is_overdue:
                    date_due['style'] += 'color: red;'
                if is_payment:
                    date_due = ''
                move_line_name = {
                    'name': self._followup_report_format_aml_name(aml.name, aml.move_id.ref),
                    'style': 'text-align:left; white-space:normal;',
                    'template': 'account_followup.line_template',
                }
                amount = {
                    'name': formatLang(self.env, amount, currency_obj=currency),
                    'style': 'text-align:right; white-space:normal;',
                    'template': 'account_followup.line_template',
                }
                line_num += 1
                invoice_origin = aml.move_id.invoice_origin or ''
                if len(invoice_origin) > 43:
                    invoice_origin = invoice_origin[:40] + '...'
                invoice_origin = {
                    'name': invoice_origin,
                    'style': 'text-align:center; white-space:normal;',
                    'template': 'account_followup.line_template',
                }
                columns = [
                    invoice_date,
                    date_due,
                    invoice_origin,
                    move_line_name,
                    amount,
                ]
                lines.append({
                    'id': aml.id,
                    'account_move': aml.move_id,
                    'name': aml.move_id.name,
                    'move_id': aml.move_id.id,
                    'type': is_payment and 'payment' or 'unreconciled_aml',
                    'unfoldable': False,
                    'columns': [isinstance(v, dict) and v or {'name': v, 'template': 'account_followup.line_template'} for v in columns],
                })
            total_due = formatLang(self.env, total, currency_obj=currency)
            line_num += 1
            cols = [
                {'name': v, 'template': 'account_followup.line_template'} for v in [''] * 3
            ] + [
                {
                    'name': v,
                    'style': 'text-align:right; white-space:normal; font-weight: bold;',
                    'template': 'account_followup.line_template',
                } for v in [total >= 0 and _('Total Due') or '', total_due]
            ]
            lines.append({
                'id': line_num,
                'name': '',
                'class': 'total',
                'style': 'border-top-style: double',
                'unfoldable': False,
                'level': 3,
                'columns': cols,
            })
            if total_issued > 0:
                total_issued = formatLang(self.env, total_issued, currency_obj=currency)
                line_num += 1
                cols = [
                    {'name': v, 'template': 'account_followup.line_template'} for v in [''] * 3
                ] + [
                    {
                        'name': v,
                        'style': 'text-align:right; white-space:normal; font-weight: bold;',
                        'template': 'account_followup.line_template',
                    } for v in [_('Total Overdue'), total_issued]
                ]
                lines.append({
                    'id': line_num,
                    'name': '',
                    'class': 'total',
                    'unfoldable': False,
                    'level': 3,
                    'columns': cols,
                })
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': '',
                'style': 'border-bottom-style: none',
                'unfoldable': False,
                'level': 0,
                'columns': [{'template': 'account_followup.line_template'} for _col in columns],
            })
        if lines:
            lines.pop()

        for line in lines:
            for col in line['columns']:
                if self.env.company.currency_id.compare_amounts(col.get('no_format', 0.0), 0.0) == -1:
                    col['class'] = 'number color-red'

        return lines
