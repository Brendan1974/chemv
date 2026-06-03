# -*- coding: utf-8 -*-

import base64
from io import BytesIO

import xlsxwriter

from odoo import _, fields, models


class BatchPaymentCsvWizard(models.TransientModel):
    _name = 'batch.payment.csv.wizrd'
    _description = 'Batch Payment XLSX Result (chemv)'

    exported = fields.Boolean(string="Exported", default=False)
    file = fields.Binary(string="File")
    file_name = fields.Char(string="File Name", size=64, default='Batch Payment.xlsx')


class IxBatchPaymentVendorReport(models.TransientModel):
    _name = 'ix.batch.payment.vendor.report'
    _description = 'Batch Payment Vendor XLSX Report Wizard (chemv)'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    file = fields.Binary(string="File")
    file_name = fields.Char(string="File Name", size=64, default='Batch Payment.xls')
    exported = fields.Boolean(string="Exported", default=False)

    def print_batch_payment_vendor_wizard(self):
        fl = BytesIO()
        wb = xlsxwriter.Workbook(fl)
        style0 = wb.add_format({'font_name': 'Times New Roman', 'bold': False,
                                'num_format': '#,##0.00;-#,##0.00;"-"'})
        style1 = wb.add_format({'font_name': 'Times New Roman', 'bold': True,
                                'num_format': '#,##0.00;-#,##0.00;"-"'})
        ws = []
        j = 0
        i = 1
        batch_payments = self.env['ix.batch.payment.ap'].search([
            ('payment_date', '>=', self.start_date),
            ('payment_date', '<=', self.end_date),
        ])

        ws.append(wb.add_worksheet('Consolidated Summary'))
        for data in batch_payments:
            ws[j].set_column('A:C', 20.25)
            ws[j].set_column('D:Z', 15.25)

            headers = ['Batch Date', 'Supplier', 'Invoice Number', 'Invoice Date',
                       'Transaction Reference', 'Transaction Description', 'Transaction Amount',
                       'Approved Amount', 'Paid to Date', 'Discount Received',
                       'Amount to be Paid', 'Branch', 'Account Number', 'Bank', 'Run Date']
            for col, h in enumerate(headers):
                ws[j].write(0, col, h, style1)

            for lines in data.vendor_bill_ids:
                ws[j].write(i, 0, data.create_date, style0)
                ws[j].write(i, 1, lines.partner_id.name or '', style0)
                ws[j].write(i, 2, lines.invoice_id.number or '', style0)
                ws[j].write(i, 3, lines.invoice_id.invoice_date or '', style0)
                ws[j].write(i, 4, data.memo or '', style0)
                ws[j].write(i, 5, 'Vendor Payment', style0)
                ws[j].write(i, 6, lines.invoice_id.amount_total, style0)
                ws[j].write(i, 7, lines.pay_amount, style0)
                ws[j].write(i, 8, data.payment_date, style0)
                ws[j].write(i, 10, lines.pay_amount, style0)
                ws[j].write(i, 11, lines.partner_id.branch_name_code or '', style0)
                ws[j].write(i, 12, lines.partner_id.acc_no_ap or '', style0)
                ws[j].write(i, 13, lines.partner_id.bank_financial_inst or '', style0)
                ws[j].write(i, 14, data.run_date, style0)
                i += 1

        j = 1
        for data in batch_payments:
            ws.append(wb.add_worksheet())
            ws[j].set_column('A:C', 20.25)
            ws[j].set_column('D:Z', 15.25)
            i = 2

            headers = ['Batch Date', 'Supplier', 'Invoice Number', 'Invoice Date',
                       'Transaction Reference', 'Transaction Description', 'Transaction Amount',
                       'Approved Amount', 'Paid to Date', 'Discount Received',
                       'Amount to be Paid', 'Branch', 'Account Number', 'Bank', 'Run Date']
            for col, h in enumerate(headers):
                ws[j].write(0, col, h, style1)

            total_approved = 0.0
            total_amount_total = 0.0
            for record in self.env['vendor.invoice.ap'].search([('vendor_id', '=', data.id)]):
                total_approved += record.pay_amount
                total_amount_total += record.invoice_id.amount_total
                ws[j].write(i, 0, data.create_date, style0)
                ws[j].write(i, 1, record.partner_id.name or '', style0)
                ws[j].write(i, 2, record.invoice_id.number or '', style0)
                ws[j].write(i, 3, record.invoice_id.invoice_date or '', style0)
                ws[j].write(i, 4, data.memo or '', style0)
                ws[j].write(i, 5, 'Vendor Payment', style0)
                ws[j].write(i, 6, record.invoice_id.amount_total, style0)
                ws[j].write(i, 7, record.pay_amount, style0)
                ws[j].write(i, 8, data.payment_date, style0)
                ws[j].write(i, 10, record.pay_amount, style0)
                ws[j].write(i, 11, record.partner_id.branch_name_code or '', style0)
                ws[j].write(i, 12, record.partner_id.acc_no_ap or '', style0)
                ws[j].write(i, 13, record.partner_id.bank_financial_inst or '', style0)
                ws[j].write(i, 14, data.run_date, style0)
                i += 1

            ws[j].write(i, 0, 'Total', style1)
            ws[j].write(i, 6, total_amount_total, style1)
            ws[j].write(i, 7, total_approved, style1)
            ws[j].write(i, 10, total_approved, style1)
            j += 1

        wb.close()
        fl.seek(0)
        buf = base64.encodebytes(fl.read())
        fl.close()
        self.file = buf
        self.exported = True
        return {
            'name': _("Batch Payment XLS"),
            'view_mode': 'form',
            'res_model': 'ix.batch.payment.vendor.report',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }
