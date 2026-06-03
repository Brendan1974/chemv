# -*- coding: utf-8 -*-

from odoo import api, models


class ReportBatchPayment(models.AbstractModel):
    _name = 'report.batch_payment.report_ap_batch_payment_pdf'
    _description = 'Batch Payment PDF Report Renderer'

    def _get_partner(self, docs):
        partner_list = []
        for data in docs.vendor_bill_ids:
            partner_list.append(data.invoice_id.partner_id)
        return list(set(partner_list))

    def _get_partner_invoice_line(self, o, partner):
        return self.env['vendor.invoice.ap'].search([
            ('invoice_id.partner_id', '=', partner.id),
            ('vendor_id', '=', o.id),
        ])

    def _get_total_pay_to_date(self, lines):
        return lines.invoice_id.amount_total - lines.invoice_id.amount_residual

    def _get_total_amount_to_be_paid(self, lines):
        return lines.pay_amount

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['ix.batch.payment.ap'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'ix.batch.payment.ap',
            'data': data,
            'docs': docs,
            'get_partner': self._get_partner,
            'get_partner_invoice_line': self._get_partner_invoice_line,
            'get_total_pay_to_date': self._get_total_pay_to_date,
            'get_total_amount_to_be_paid': self._get_total_amount_to_be_paid,
        }
