# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountReport(models.Model):
    """Extend account.report (now a stored model in v17+) to add a sales-person
    filter that restricts move lines by ``move_id.invoice_user_id``.

    The filter is opt-in per report record via ``filter_account``.
    """

    _inherit = 'account.report'

    filter_account = fields.Boolean(
        string="Filter by Sales Person",
        compute=lambda x: x._compute_report_option_filter('filter_account', True),
        readonly=False,
        store=True,
        depends=['root_report_id', 'section_main_report_ids'],
    )

    @api.model
    def _get_filter_account(self):
        return self.env['res.users'].search([])

    def _init_options_account(self, options, previous_options=None):
        if not self.filter_account:
            return

        previous_options = previous_options or {}
        if previous_options.get('account'):
            journal_map = {
                opt['id']: opt['selected']
                for opt in previous_options['account']
                if opt.get('id') != 'divider' and 'selected' in opt
            }
        else:
            journal_map = {}
        options['account'] = []
        for op in self._get_filter_account():
            options['account'].append({
                'id': op.id,
                'account_id': op.id,
                'account_name': op.name,
                'selected': journal_map.get(op.id) or False,
            })

    @api.model
    def _get_options_account(self, options):
        return [a for a in options.get('account', []) if a.get('selected')]

    @api.model
    def _get_options_account_domain(self, options):
        selected = self._get_options_account(options)
        return selected and [('move_id.invoice_user_id', 'in', [j['id'] for j in selected])] or []

    def _get_options_domain(self, options, date_scope):
        res = super()._get_options_domain(options, date_scope)
        res += self._get_options_account_domain(options)
        return res
