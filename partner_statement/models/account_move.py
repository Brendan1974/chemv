# Copyright 2018 ForgeFlow, S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# chemv customisation ported from v16: extra fields on account.move.line and
# res.partner, plus a helper used by an external cron to clear statement_sent.

import logging
from datetime import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


def _topmost_ancestor_4_levels(partner):
    """Reproduce v16 chemv logic: walk parent_id up to four levels.

    If the chain is longer than four levels the field stops at the
    fourth ancestor (intentionally matching v16 behaviour, not the
    full ``commercial_partner_id`` walk).
    """
    p = partner
    if (
        p.parent_id
        and p.parent_id.parent_id
        and p.parent_id.parent_id.parent_id
        and p.parent_id.parent_id.parent_id.parent_id
    ):
        return p.parent_id.parent_id.parent_id.parent_id
    if (
        p.parent_id
        and p.parent_id.parent_id
        and p.parent_id.parent_id.parent_id
    ):
        return p.parent_id.parent_id.parent_id
    if p.parent_id and p.parent_id.parent_id:
        return p.parent_id.parent_id
    if p.parent_id:
        return p.parent_id
    return p


class AccountMove(models.Model):
    _inherit = "account.move"

    partner_parent_id = fields.Many2one(
        "res.partner",
        string="Partner Parent",
        store=True,
        compute="_compute_partner_parent",
    )

    @api.depends("partner_id")
    def _compute_partner_parent(self):
        for rec in self:
            rec.partner_parent_id = _topmost_ancestor_4_levels(rec.partner_id)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    account_internal_type = fields.Selection(
        related="account_id.account_type",
        string="Account Internal Type",
        readonly=True,
        store=True,
    )

    partner_parent_id = fields.Many2one(
        "res.partner",
        string="Partner Parent",
        store=True,
        compute="_compute_partner_parent",
    )

    @api.depends("partner_id")
    def _compute_partner_parent(self):
        for rec in self:
            rec.partner_parent_id = _topmost_ancestor_4_levels(rec.partner_id)


class ResPartner(models.Model):
    _inherit = "res.partner"

    customer = fields.Boolean(string="Is Customer", default=True)
    is_vendor = fields.Boolean(string="Is Vendor", default=True)
    statement_sent = fields.Boolean("Statement Sent", default=False)
    excl_fully_allocated_invoices = fields.Boolean(
        string="Exclude Fully Allocated Invoices"
    )
    statement_email = fields.Char("Statement Email")
    statement_period = fields.Selection(
        [
            ("current_month", "Current Month"),
            ("current_quarter", "Current Quarter"),
            ("current_fiscal_year", "Current Fiscal Year"),
            ("last_fiscal_year", "Last Fiscal Year"),
            ("last_quarter", "Last Quarter"),
            ("last_month", "Last Month"),
        ],
        default="current_month",
        string="Statement Period",
    )

    def update_statement_sent(self):
        config_id = self.env["ir.config_parameter"].sudo().get_param(
            "partner_statement.cron_next_call_date"
        )
        if config_id and int(config_id) - 1 == datetime.now().day:
            self.search([("statement_sent", "=", True)]).update(
                {"statement_sent": False}
            )
