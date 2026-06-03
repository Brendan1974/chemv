# `partner_statement` — one-screen cheatsheet (v18, with chemv extensions)

```
╔══════════════════════════════════════════════════════════════════════════╗
║  PARTNER STATEMENT — Odoo 18 (OCA + chemv)                               ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  3 REPORTS         Activity · Outstanding · Detailed Activity            ║
║  3 FORMATS         PDF · HTML preview · XLSX                             ║
║  3 WIZARDS         Bound on res.partner (single or multi-select)         ║
║                                                                          ║
║  WIZARD BUTTONS    [View] [Export PDF] [Export XLSX] [Send Email⁺]       ║
║                    [SEND BY EMAIL⁺] (queues to cron)                     ║
║                                                                          ║
║  FILTERS                                                                 ║
║    Date Start · Date End · Company · Account Type (Recv/Pay)             ║
║    Accounts to Exclude (code patterns) · Show Only Overdue               ║
║    Aging Method (Days/Months) · Show Aging Buckets                       ║
║    Don't show partners w/no due · Exclude Negative Balances              ║
║                                                                          ║
║  AGING BUCKETS                                                           ║
║    Days:   Current · 1-30 · 31-60 · 61-90 · 91-120 · 121+                ║
║    Months: Current · 1 · 2 · 3 · 4 · Older                               ║
║    chemv:  Current · 30+ · 60+ · 90+ · 120+ · 121+ Days · Total          ║
║                                                                          ║
║  MULTI-CURRENCY   Per-currency lines · buckets · balance fwd · due       ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  ⁺  CHEMV ADDITIONS (on top of OCA)                                      ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  ROLLUP RULE       Statement for X also pulls lines from descendants     ║
║                    up to 4 levels deep (via partner_parent_id field      ║
║                    on account.move / .line / .payment / .bank.stmt.line) ║
║                                                                          ║
║  PARTNER FIELDS    customer · is_vendor · statement_email                ║
║                    statement_period · statement_sent                     ║
║                    excl_fully_allocated_invoices                         ║
║                                                                          ║
║  MOVE LINE FIELD   account_internal_type (stored shadow of account_type) ║
║                                                                          ║
║  SETTINGS (11)     Settings → Accounting → Partner Statements            ║
║    automatic_statement · cron_next_call_date · send_to_options           ║
║    new_default_statement_period · statement_period_setting               ║
║    mode (Prod/Test) · test_email_address                                 ║
║    excl_fully_allocated_invoices                                         ║
║    automatic_payment_reminder · payment_reminder_date                    ║
║    payment_reminder_email_template_ids                                   ║
║    All under ir.config_parameter key: partner_statement.*                ║
║                                                                          ║
║  EMAIL DELIVERY                                                          ║
║    [Send Email]      Sync. Renders PDF → mail.mail → sends now           ║
║                      Templates: email_template_{activity,outstanding}_ap ║
║                                                                          ║
║    [SEND BY EMAIL]   Async. Queues activity.statement.record             ║
║                      Cron: 'Partner: Activity Statement Email Sent'      ║
║                      Runs every 5 min · batches of 20                    ║
║                      Templates: email_template_partner_{,_outstanding_}  ║
║                                       statement                          ║
║                      Falls back to invoice-type child's email            ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  EXTENSION POINTS                                                        ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  Inherit  statement.common         → override SQL & label helpers        ║
║  Inherit  statement.common.wizard  → add wizard fields                   ║
║  Override _get_bucket_labels_{days,months}                               ║
║  Override _show_buckets_sql_q{1,2,3,4}                                   ║
║  Override _get_account_display_lines / _get_account_initial_balance      ║
║  XPath    partner_statement.outstanding_balance (line table)             ║
║  XPath    partner_statement.aging_buckets                                ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  SECURITY GROUPS                                                         ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  partner_statement.group_activity_statement      → Activity + Detailed   ║
║  partner_statement.group_outstanding_statement   → Outstanding           ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  KEY MODELS / XML-IDS                                                    ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  Models   statement.common · statement.common.wizard                     ║
║           activity.statement.wizard · outstanding.statement.wizard       ║
║           detailed.activity.statement.wizard                             ║
║           activity.statement.record   (chemv queue)                      ║
║                                                                          ║
║  Reports  partner_statement.action_print_activity_statement{,_xlsx,_html}║
║           partner_statement.action_print_outstanding_statement{,_xlsx,_..║
║           partner_statement.action_print_detailed_activity_statement{...}║
║                                                                          ║
║  Cron     ap_partner_statment_extended.partner_activity_statement_       ║
║                                            cron_email_sent  (5 min)      ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```
