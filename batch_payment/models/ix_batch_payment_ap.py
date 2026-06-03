# -*- coding: utf-8 -*-

import base64
import logging
from datetime import datetime
from io import BytesIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Batch payment header
# ---------------------------------------------------------------------------
class IxBatchPaymentAp(models.Model):
    _name = 'ix.batch.payment.ap'
    _description = 'Batch Payment (chemv)'
    _rec_name = 'payment_date'

    state = fields.Selection(
        [('to be approved', 'To Be Approved'),
         ('approved', 'Approved'),
         ('rejected', 'Rejected')],
        string="State", default="to be approved",
    )
    payment_date = fields.Date(string="Payment Date")
    memo = fields.Char(string="Memo")
    vendor_bill_ids = fields.One2many(
        'vendor.invoice.ap', 'vendor_id', string='Vendor bill',
        default=lambda self: self._default_vendor_bills(),
    )
    requested_person_id = fields.Many2one('res.users', string="Requested Person")
    approve_person_id = fields.Many2one('res.users', string="Approved Person")
    run_date = fields.Date(string='Run Date')
    number = fields.Char('Number')
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self._default_company_id(),
    )
    bank_id = fields.Many2one(
        'account.journal', string="Bank",
        default=lambda self: self._default_bank_id(),
    )
    invoice_ids = fields.Many2many('account.move')
    invoice_list_ids = fields.Many2many(
        'account.move', compute="_compute_invoice_list_ids",
    )
    is_add = fields.Boolean(default=False, string="Add More Vendor Bills")

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------
    @api.model
    def _default_vendor_bills(self):
        active_ids = self._context.get('active_ids')
        if not active_ids:
            return []
        invoices = self.env['account.move'].browse(active_ids)
        rec_list = []
        for data in invoices:
            if data.state != 'posted':
                raise UserError(_('You can only register payments for open invoices'))
            if not data.partner_id.is_approve:
                raise UserError(_('Please approve bank details of %s') % data.partner_id.name)
            if data.payment_state in ('paid', 'in_payment'):
                raise UserError(_('Vendor bill %s is already been paid') % data.name)
            rec_list.append((0, 0, {
                'invoice_id': data.id,
                'partner_id': data.partner_id.id,
                'number': data.number,
                'balance_amount': data.amount_total,
                'pay_amount': data.amount_residual_signed,
                'amount_untaxed': data.amount_untaxed,
            }))
        return rec_list

    @api.model
    def _default_company_id(self):
        active_ids = self._context.get('active_ids')
        if active_ids:
            vendor_bills = self.env['account.move'].browse(active_ids)
            companies = vendor_bills.mapped('company_id')
            if len(companies) > 1:
                raise UserError(_('Please select Vendor bills of only one Company'))
            return companies and companies[0].id or False
        return self.env.user.company_id.id

    @api.model
    def _default_bank_id(self):
        active_ids = self._context.get('active_ids')
        if active_ids:
            vendor_bills = self.env['account.move'].browse(active_ids)
            companies = vendor_bills.mapped('company_id')
            company_id = companies and companies[0].id or self.env.user.company_id.id
        else:
            company_id = self.env.user.company_id.id
        return self.env['account.journal'].search(
            [('name', '=', 'Standard Bank - Current'), ('company_id', '=', company_id)],
            limit=1,
        ).id

    # ------------------------------------------------------------------
    # Onchange + compute
    # ------------------------------------------------------------------
    @api.onchange('invoice_ids')
    def onchange_invoice_ids(self):
        if not self.invoice_ids:
            return
        rec_list = []
        for data in self.invoice_ids:
            if data in self.invoice_list_ids:
                continue
            if data.state != 'posted':
                raise UserError(_('You can only register payments for open invoices'))
            if not data.partner_id.is_approve:
                raise UserError(_('Please approve bank details of %s') % data.partner_id.name)
            rec_list.append((0, 0, {
                'invoice_id': data.id,
                'partner_id': data.partner_id.id,
                'number': data.number,
                'balance_amount': data.amount_total,
                'pay_amount': data.amount_residual_signed,
                'amount_untaxed': data.amount_untaxed,
            }))
        self.vendor_bill_ids = rec_list

    @api.depends('vendor_bill_ids')
    def _compute_invoice_list_ids(self):
        for rec in self:
            invoices = [d.id for d in rec.vendor_bill_ids.mapped('invoice_id')]
            rec.invoice_list_ids = [(6, 0, invoices)]

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def print_batch_payment_vendor(self):
        return {
            'name': _('Batch Payment XLS'),
            'view_mode': 'form',
            'res_model': 'ix.batch.payment.vendor.report',
            'view_id': self.env.ref('batch_payment.view_batch_payment_xls_report_vendor').id or False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def save_rec(self):
        for lines in self.vendor_bill_ids:
            if not lines.pay_amount:
                raise UserError(_('Please fill Pay Amount'))
        self.ensure_one()

    def btn_approved(self):
        """Approve the batch: for each partner, create one account.payment that
        covers all selected bills and reconcile it against them.

        v18-native flow:
          1. Ensure the bank journal's payment-method-lines have a payment
             outstanding account configured (v18 needs this to create the
             journal entry — sparse setups leave it empty and silently skip
             move creation, leaving the invoice unreconciled).
          2. Use ``account.payment.register`` to assemble payment vals — same
             flow as the standard "Register Payment" button on an invoice.
          3. The wizard creates → posts → reconciles in one call.
          4. Tag every new payment back to this batch via ``chemv_batch_payment_id``.
        """
        if not self.bank_id:
            raise UserError(_('Please select a bank.'))
        bad_state = self.vendor_bill_ids.filtered(lambda x: x.invoice_id.state != 'posted')
        if bad_state:
            raise UserError(
                _('Vendor bill %s is not in Posted state') % bad_state[0].invoice_id.name
            )
        already_paid = self.vendor_bill_ids.filtered(
            lambda x: x.invoice_id.payment_state in ('paid', 'in_payment')
        )
        if already_paid:
            raise UserError(
                _('Vendor bill %s is already been paid') % already_paid[0].invoice_id.name
            )

        # v18 needs payment_account_id set on the journal's method-lines —
        # otherwise outstanding_account_id stays empty on the payment, and
        # _generate_journal_entry() skips move creation, breaking
        # reconciliation. Configure once if missing.
        self._ensure_outstanding_accounts()

        Payment = self.env['account.payment']

        for partner in self.vendor_bill_ids.mapped('partner_id'):
            lines = self.vendor_bill_ids.filtered(lambda x: x.partner_id == partner)
            invoices = lines.mapped('invoice_id').filtered(
                lambda m: m.state == 'posted'
                and m.payment_state not in ('paid', 'in_payment')
            )
            if not invoices:
                continue
            if not partner.is_approve:
                raise UserError(_('Please approve bank details of %s') % partner.name)

            # Sum the per-line `pay_amount` overrides (chemv feature: user may
            # part-pay an invoice). Default wizard amount = invoice residual.
            total_amount = sum(abs(l.pay_amount) for l in lines)
            communication = ' '.join((inv.name or '') for inv in invoices)

            register = self.env['account.payment.register'].with_context(
                active_model='account.move',
                active_ids=invoices.ids,
                dont_redirect_to_payments=True,
            ).create({
                'journal_id': self.bank_id.id,
                'payment_date': self.payment_date,
                'amount': total_amount,
                'group_payment': True,
                'communication': communication,
            })
            new_payments = register._create_payments()
            new_payments.write({'chemv_batch_payment_id': self.id})

        self.state = 'approved'

    def _ensure_outstanding_accounts(self):
        """Auto-configure outbound/inbound method-line payment_account_id on
        the batch's bank journal when missing. Required for v18 to create the
        payment's journal entry on `action_post`."""
        if not self.bank_id:
            return
        fallback = (
            self.company_id.transfer_account_id
            or self.env['account.account'].sudo().search([
                *self.env['account.account']._check_company_domain(self.company_id),
                ('account_type', '=', 'asset_current'),
            ], limit=1)
        )
        if not fallback:
            return
        for pml in self.bank_id.outbound_payment_method_line_ids:
            if not pml.payment_account_id:
                pml.payment_account_id = fallback
        for pml in self.bank_id.inbound_payment_method_line_ids:
            if not pml.payment_account_id:
                pml.payment_account_id = fallback

    def btn_rejected(self):
        self.state = 'rejected'
        for payment in self.env['account.payment'].search([('chemv_batch_payment_id', '=', self.id)]):
            payment.action_draft()
            payment.action_cancel()

    def unlink(self):
        for rec in self:
            if rec.vendor_bill_ids:
                raise UserError(_('You do not have access to delete batch payments.'))
        return super().unlink()

    def print_batch_payment_pdf(self):
        return self.env.ref('batch_payment.action_ap_batch_payment').report_action(self)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec, vals in zip(records, vals_list):
            if vals.get('payment_date'):
                split_date = vals.get('payment_date').split('-') if isinstance(vals['payment_date'], str) else str(vals['payment_date']).split('-')
                date_res = ''.join(map(str, split_date))
                new_seq = self.env['ir.sequence'].with_company(rec.company_id.id).next_by_code("ix.batch.payment.ap")
                if new_seq:
                    rec.write({'number': 'SB' + date_res + 'EFT' + new_seq})
        return records

    def write(self, vals):
        result = super().write(vals)
        for rec in self.filtered(lambda x: x.invoice_ids):
            rec.invoice_ids = False
            rec.is_add = False
        return result

    def print_batch_payment_csv(self):
        """Batch Payment report (XLSX) — debtor-order layout."""
        fl = BytesIO()
        wb = xlsxwriter.Workbook(fl)
        style0 = wb.add_format({'font_name': 'Times New Roman', 'bold': False,
                                'num_format': '#,##0.00;-#,##0.00;"-"'})
        style1 = wb.add_format({'font_name': 'Times New Roman', 'bold': True,
                                'num_format': '#,##0.00;-#,##0.00;"-"'})
        ws = wb.add_worksheet()
        ws.set_column('A:C', 20.25)
        ws.set_column('D:Z', 15.25)
        headers = ['Cr Account Name', 'Cr Account Number', 'Cr Branch Number',
                   'Cr Statement Reference', 'Dr Account Name', 'Dr Account Number',
                   'Dr Branch Number', 'Dr Statement Reference', 'Date', 'Amount',
                   'RTGS/RTC', 'Pay Alert Type', 'Pay Alert Destination']
        for col, h in enumerate(headers):
            ws.write(0, col, h, style1)
        i = 1
        partners = set(self.vendor_bill_ids.mapped('partner_id'))
        for partner in partners:
            for line in self.vendor_bill_ids.filtered(lambda x: x.partner_id == partner):
                ws.write(i, 0, (line.partner_id.name or '')[:30], style0)
                ws.write(i, 1, line.partner_id.acc_no_ap or '', style0)
                ws.write(i, 2, line.partner_id.branch_name_code or '', style0)
                ws.write(i, 3, self.env.user.company_id.name or '', style0)
                ws.write(i, 4, self.env.user.company_id.name or '', style0)
                ws.write(i, 5, self.company_id.dr_account_number or '', style0)
                ws.write(i, 6, self.company_id.dr_branch_number or '', style0)
                ws.write(i, 7, self.number or '', style0)
                ws.write(i, 8, str(self.payment_date).replace("-", "") if self.payment_date else '', style0)
                ws.write(i, 9, sum(self.vendor_bill_ids.filtered(
                    lambda x: x.partner_id == partner).mapped('pay_amount')), style0)
                ws.write(i, 10, 'N', style0)
                ws.write(i, 11, 'E', style0)
                ws.write(i, 12, line.partner_id.email or '', style0)
            i += 1
        wb.close()
        fl.seek(0)
        buf = base64.encodebytes(fl.read())
        fl.close()
        a1 = self.env['batch.payment.csv.wizrd'].create({
            'file': buf,
            'file_name': 'Batch_Payment.xls',
            'exported': True,
        })
        return {
            'name': _('Batch Payment'),
            'view_mode': 'form',
            'res_model': 'batch.payment.csv.wizrd',
            'res_id': a1.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


# ---------------------------------------------------------------------------
# Line items
# ---------------------------------------------------------------------------
class VendorInvoiceAp(models.Model):
    _name = 'vendor.invoice.ap'
    _description = 'Batch Payment Line (chemv)'

    vendor_id = fields.Many2one('ix.batch.payment.ap', string='Vendor')
    invoice_id = fields.Many2one('account.move', string='Supplier Invoice')
    partner_id = fields.Many2one('res.partner', string="Supplier")
    number = fields.Char(string="Supplier Invoice")
    balance_amount = fields.Float(string='Balance Amount')
    pay_amount = fields.Float(string='Pay Amount')
    amount_untaxed = fields.Float(string="Untaxed Amount")


# ---------------------------------------------------------------------------
# Inherited models — add bank detail fields, batch-payment flag, sequences
# ---------------------------------------------------------------------------
class ResPartner(models.Model):
    _inherit = 'res.partner'

    bank_financial_inst = fields.Char(string='Bank / Financial institution:', tracking=True)
    branch_name_code = fields.Char(string='Branch name and code:', tracking=True)
    acc_no_ap = fields.Char(string='Bank account number:', tracking=True)
    type_account = fields.Char(string='Type of account:', tracking=True)
    swift_code = fields.Char(string='Swift Code:', tracking=True)
    tel_ph_dtls = fields.Char(string='Telephone details (accounts department contact person)',
                              tracking=True)
    is_approve = fields.Boolean(string="Is approved")

    def button_approve(self):
        for rec in self:
            msg = "Banking Details has been approved by %s on %s" % (
                self.env.user.name, str(datetime.now().date()))
            rec.message_post(body=msg)
            rec.is_approve = True


class AccountMove(models.Model):
    _inherit = "account.move"

    proman_inv = fields.Char(string="Proman Inv. No")
    is_generate_vat_by_subtotal = fields.Boolean(
        default=False, string="Generate the VAT by Invoice line")
    number = fields.Char('Number')

    is_pm_validated = fields.Boolean('Is PM Validated', compute='_compute_is_pm_validated')
    pm_validated = fields.Float('Total Verification', tracking=True)
    wp_invoice_number = fields.Char('WP Invoice Number', tracking=True)

    @api.depends_context('uid')
    def _compute_is_pm_validated(self):
        # The "force PM approval" group lives in another chemv module; resolve safely.
        try:
            forced = self.env.user.has_group('batch_payment.group_force_pm_approval')
        except ValueError:
            forced = False
        for rec in self:
            rec.is_pm_validated = forced

    def action_pm_validate(self):
        self.ensure_one()
        # Defensive: only block if the optional project_id is present and references this user.
        proj_user = getattr(self, 'project_id', False) and self.project_id.user_id or False
        if proj_user and proj_user.id != self._context.get('uid', False):
            raise UserError(_('Only project manager can Validate.'))
        self.message_post(body="PM Validated : %s" % self.pm_validated,
                          subject="PM validated")
        return self.write({'is_pm_validated': True})


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_batch_payment = fields.Boolean(string='Is Batch Payment', default=False)


class ResCompany(models.Model):
    _inherit = 'res.company'

    dr_account_number = fields.Char(string='Dr Account Number')
    dr_branch_number = fields.Char(string='Dr Branch Number')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    chemv_batch_payment_id = fields.Many2one(
        'ix.batch.payment.ap',
        string='chemv Batch Payment',
        index=True,
    )
