# -*- coding: utf-8 -*-
{
    'name': "batch_payment",
    'summary': "Vendor batch payment: aggregate bills → create reconciled payments",
    'description': """
chemv batch payment workflow:
- Select multiple vendor bills (account.move) → create a batch
- Aggregate per partner, approve workflow
- On approval: create account.payment per partner, post and reconcile against bills
- Reject workflow: cancels related payments
- PDF report + per-period XLSX export
- Bank-detail approval on res.partner
- Per-bank batch eligibility flag (account.journal.is_batch_payment)
- Per-company drawer account/branch fields
    """,
    'author': "AP Systems",
    'website': "https://ap-systems.co.za",
    'category': 'Accounting/Accounting',
    'version': '18.0.0.4.0',
    'license': 'LGPL-3',
    'depends': ['base', 'account', 'mail'],
    'data': [
        'security/res_security.xml',
        'data/sequence.xml',
        'views/batch_payment.xml',
        'reports/batch_payment_pdf.xml',
        'wizard/ix_batch_payment_xls.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
}
