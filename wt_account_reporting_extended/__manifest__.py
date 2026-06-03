# -*- coding: utf-8 -*-
{
    "name": "wt account reporting",
    "version": "18.0.0.1.0",
    "category": "Accounting",
    "summary": "Account trial balance extended with sales-person (invoice_user_id) filter",
    "description": """
Adds a 'Sales Person' filter to account.report (Trial Balance, Partner Ledger,
General Ledger, etc.). Lines are restricted to journal entries whose
invoice user (invoice_user_id) matches the selected users.

The filter is opt-in per report: set ``filter_account`` on the
``account.report`` record (default True for newly-created variants).
The dropdown is exposed via an OWL component patched into
``AccountReportFiltersCustomizable``.
    """,
    "author": "Warlock Technologies Pvt Ltd.",
    "website": "http://warlocktechnologies.com",
    "license": "LGPL-3",
    "depends": ["account_reports"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "wt_account_reporting_extended/static/src/scss/custom.scss",
            "wt_account_reporting_extended/static/src/components/**/*",
        ],
    },
    "auto_install": False,
    "installable": True,
}
