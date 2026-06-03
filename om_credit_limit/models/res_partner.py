from odoo import models, fields, api, _
from odoo.tools import SQL


class ResPartner(models.Model):
    _inherit = 'res.partner'

    amount_credit_limit = fields.Monetary(string='Internal Credit Limit', default=-1)
    credit_limit_compute = fields.Monetary(
        string='Credit Limit ', default=-1,
        compute='_compute_credit_limit_compute', inverse='_inverse_credit_limit_compute',
        help='A limit of zero means no limit. A limit of -1 will use the default (company) limit.'
    )
    show_credit_limit = fields.Boolean(compute='_compute_show_credit_limit')
    account_credit_limit = fields.Boolean(
        string="Sales Credit Limit", readonly=False,
        help="ETrigger alerts when creating Invoices and Sales Orders for Partners with a Total Receivable amount exceeding a limit.")
    account_default_credit_limit = fields.Monetary(
        string="Default Credit Limit", readonly=False,
        help="A limit of zero means no limit by default.")
    credit_limit_type = fields.Selection([('warning', 'Warning'), ('block', 'Block')],string="Credit Limit Type", 
                                         readonly=False)
    compute_credit_limit_type = fields.Selection([('warning', 'Warning'), ('block', 'Block')],compute="_compute_credit_limit_type")

    @api.depends('credit_limit_type')
    def _compute_credit_limit_type(self):
        self.compute_credit_limit_type = False
        for rec in self:
            if rec.parent_id:
                rec.compute_credit_limit_type = rec.parent_id.credit_limit_type
            else:
                rec.compute_credit_limit_type = rec.credit_limit_type

    @api.depends('amount_credit_limit')
    @api.depends_context('company')
    def _compute_credit_limit_compute(self):
        for partner in self:
            if partner.parent_id:
                partner.credit_limit_compute = partner.parent_id.account_default_credit_limit if partner.parent_id.amount_credit_limit == -1 else partner.parent_id.amount_credit_limit    
            else:
                partner.credit_limit_compute = partner.account_default_credit_limit if partner.amount_credit_limit == -1 else partner.amount_credit_limit

    @api.depends('credit_limit_compute')
    @api.depends_context('company')
    def _inverse_credit_limit_compute(self):
        for partner in self:
            if partner.parent_id:
                is_default = partner.parent_id.credit_limit_compute == partner.parent_id.account_default_credit_limit
                partner.amount_credit_limit = -1 if is_default else partner.parent_id.credit_limit_compute
            else:
                is_default = partner.credit_limit_compute == partner.account_default_credit_limit
                partner.amount_credit_limit = -1 if is_default else partner.credit_limit_compute

    @api.depends_context('company')
    def _compute_show_credit_limit(self):
        for partner in self:
            if partner.parent_id:
                partner.show_credit_limit = partner.parent_id.account_credit_limit
            else:
                partner.show_credit_limit = partner.account_credit_limit

    def _commercial_fields(self):
        return super(ResPartner, self)._commercial_fields() + ['amount_credit_limit']

    @api.depends_context('company')
    def _credit_debit_get(self):
        if not self.ids:
            self.debit = False
            self.credit = False
            return

        query = self.env['account.move.line']._where_calc([
            ('parent_state', '=', 'posted'),
            ('company_id', '=', self.env.company.id)
        ])
        self.env['account.move.line'].flush_model(
            ['account_id', 'amount_residual', 'company_id', 'parent_state', 'partner_id', 'reconciled']
        )
        self.env['account.account'].flush_model(['account_type'])
        query = SQL("""
            SELECT account_move_line.partner_id, a.account_type, SUM(account_move_line.amount_residual)
            FROM %s
            LEFT JOIN account_account a ON (account_move_line.account_id = a.id)
            WHERE a.account_type IN ('asset_receivable', 'liability_payable')
            AND account_move_line.partner_id IN %s
            AND account_move_line.reconciled IS NOT TRUE
            AND %s
            GROUP BY account_move_line.partner_id, a.account_type
            """,
            query.from_clause,
            tuple(self.ids),
            query.where_clause or SQL("TRUE"),
        )
        treated = self.browse()
        for partner_id, account_type, value in self.env.execute_query(query):
            partner = self.browse(partner_id)
            if account_type == 'asset_receivable':
                partner.credit = value
                if partner not in treated:
                    partner.debit = False
                    treated |= partner
            elif account_type == 'liability_payable':
                partner.debit = -value
                if partner not in treated:
                    partner.credit = False
                    treated |= partner
        remaining = self - treated
        remaining.debit = False
        remaining.credit = False
