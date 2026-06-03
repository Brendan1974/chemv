# chemv customisation ported from v16: extra config-parameter-backed settings
# for the automatic statement / payment-reminder schedulers.

from odoo import fields, models


class ActivityStatementConfigSetting(models.TransientModel):
    _inherit = "res.config.settings"

    automatic_statement = fields.Boolean(string="Turn On automatic statements")
    cron_next_call_date = fields.Integer(string="Cron Next Call Date")
    send_to_options = fields.Selection(
        [
            ("send_to_all", "Send to All"),
            ("outstanding_balance_only", "Outstanding Balance Only"),
        ],
        string="Send Options",
    )
    new_default_statement_period = fields.Selection(
        [
            ("current_fiscal_year", "Current Fiscal Year"),
            ("current_quarter", "Current Quarter"),
            ("current_month", "Current Month"),
            ("last_fiscal_year", "Last Fiscal Year"),
            ("last_quarter", "Last Quarter"),
            ("last_month", "Last Month"),
        ],
        string="Default Statement Period",
        default="current_month",
    )
    mode = fields.Selection(
        [("Production", "Production"), ("Test", "Test")]
    )
    test_email_address = fields.Char(string="Test Email Address")
    excl_fully_allocated_invoices = fields.Boolean(
        string="Exclude Fully Allocated Invoices"
    )
    statement_period_setting = fields.Selection(
        [
            ("partner_setting", "Partner Setting"),
            ("global_setting", "Global Setting"),
        ],
        string="Statement Period Setting",
    )
    automatic_payment_reminder = fields.Boolean()
    payment_reminder_date = fields.Integer(string="Payment Reminder Date")
    payment_reminder_email_template_ids = fields.Many2one(
        "mail.template",
        string="Payment Reminder Email Template",
    )

    def get_values(self):
        res = super().get_values()
        ICP = self.env["ir.config_parameter"].sudo()
        res.update(
            {
                "automatic_statement": ICP.get_param("partner_statement.automatic_statement"),
                "send_to_options": ICP.get_param("partner_statement.send_to_options"),
                "new_default_statement_period": ICP.get_param(
                    "partner_statement.new_default_statement_period"
                ),
                "statement_period_setting": ICP.get_param(
                    "partner_statement.statement_period_setting"
                ),
                "mode": ICP.get_param("partner_statement.mode"),
                "test_email_address": ICP.get_param("partner_statement.test_email_address"),
                "cron_next_call_date": int(
                    ICP.get_param("partner_statement.cron_next_call_date") or 0
                ),
                "excl_fully_allocated_invoices": ICP.get_param(
                    "partner_statement.excl_fully_allocated_invoices"
                ),
                "automatic_payment_reminder": ICP.get_param(
                    "partner_statement.automatic_payment_reminder"
                ),
                "payment_reminder_date": int(
                    ICP.get_param("partner_statement.payment_reminder_date") or 0
                ),
                "payment_reminder_email_template_ids": int(
                    ICP.get_param(
                        "partner_statement.payment_reminder_email_template_ids1"
                    )
                    or 0
                ),
            }
        )
        return res

    def set_values(self):
        res = super().set_values()
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("partner_statement.automatic_statement", self.automatic_statement)
        ICP.set_param("partner_statement.cron_next_call_date", self.cron_next_call_date)
        ICP.set_param("partner_statement.send_to_options", self.send_to_options)
        ICP.set_param("partner_statement.mode", self.mode)
        ICP.set_param("partner_statement.test_email_address", self.test_email_address)
        ICP.set_param(
            "partner_statement.new_default_statement_period",
            self.new_default_statement_period,
        )
        ICP.set_param(
            "partner_statement.automatic_payment_reminder",
            self.automatic_payment_reminder,
        )
        ICP.set_param(
            "partner_statement.payment_reminder_date", self.payment_reminder_date
        )
        ICP.set_param(
            "partner_statement.payment_reminder_email_template_ids1",
            self.payment_reminder_email_template_ids.id,
        )
        ICP.set_param(
            "partner_statement.statement_period_setting",
            self.statement_period_setting,
        )
        ICP.set_param(
            "partner_statement.excl_fully_allocated_invoices",
            self.excl_fully_allocated_invoices,
        )
        return res
