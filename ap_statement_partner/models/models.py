    # -*- coding: utf-8 -*-

from odoo import _, models


class ApStatementPartner(models.AbstractModel):
    _inherit = "statement.common"

    def _get_bucket_labels_days(self, date_end):
        return [
            _("Current"),
            _("30 + Days"),
            _("60 + Days"),
            _("90 + Days"),
            _("120 + Days"),
            _("121 Days +"),
            _("Total"),
        ]
#     @api.model
#     def _get_report_values(self, docids, data=None):

#         company_id = data["company_id"]
#         partner_ids = data["partner_ids"]
#         date_start = data.get("date_start")
#         if date_start and isinstance(date_start, str):
#             date_start = datetime.strptime(
#                 date_start, DEFAULT_SERVER_DATE_FORMAT
#             ).date()
#         date_end = data["date_end"]
#         if isinstance(date_end, str):
#             date_end = datetime.strptime(date_end, DEFAULT_SERVER_DATE_FORMAT).date()
#         account_type = data["account_type"]
#         aging_type = data["aging_type"]
#         today = fields.Date.today()
#         amount_field = data.get("amount_field", "amount")

#         # There should be relatively few of these, so to speed performance
#         # we cache them - default needed if partner lang not set
#         self._cr.execute(
#             """
#             SELECT p.id, l.date_format
#             FROM res_partner p LEFT JOIN res_lang l ON p.lang=l.code
#             WHERE p.id IN %(partner_ids)s
#             """,
#             {"partner_ids": tuple(partner_ids)},
#         )
#         date_formats = {r[0]: r[1] for r in self._cr.fetchall()}
#         default_fmt = self.env["res.lang"]._lang_get(self.env.user.lang).date_format
#         currencies = {x.id: x for x in self.env["res.currency"].search([])}

#         res = {}
#         # get base data
#         lines = self._get_account_display_lines(
#             company_id, partner_ids, date_start, date_end, account_type
#         )
#         balances_forward = self._get_account_initial_balance(
#             company_id, partner_ids, date_start, account_type
#         )

#         if data["show_aging_buckets"]:
#             buckets = self._get_account_show_buckets(
#                 company_id, partner_ids, date_end, account_type, aging_type
#             )
#             bucket_labels = self._get_bucket_labels(date_end, aging_type)
#         else:
#             bucket_labels = {}

#         # organise and format for report
#         format_date = self._format_date_to_partner_lang
#         partners_to_remove = set()
#         for partner_id in partner_ids:
#             res[partner_id] = {
#                 "today": format_date(today, date_formats.get(partner_id, default_fmt)),
#                 "start": format_date(
#                     date_start, date_formats.get(partner_id, default_fmt)
#                 ),
#                 "end": format_date(date_end, date_formats.get(partner_id, default_fmt)),
#                 "currencies": {},
#             }
#             currency_dict = res[partner_id]["currencies"]

#             for line in balances_forward.get(partner_id, []):
#                 (
#                     currency_dict[line["currency_id"]],
#                     currencies,
#                 ) = self._get_line_currency_defaults(
#                     line["currency_id"], currencies, line["balance"]
#                 )

#             for line in lines[partner_id]:
#                 if line["currency_id"] not in currency_dict:
#                     (
#                         currency_dict[line["currency_id"]],
#                         currencies,
#                     ) = self._get_line_currency_defaults(
#                         line["currency_id"], currencies, 0.0
#                     )
#                 line_currency = currency_dict[line["currency_id"]]
#                 if not line["blocked"]:
#                     line_currency["amount_due"] += line[amount_field]
#                 line["balance"] = line_currency["amount_due"]
#                 line["date"] = format_date(
#                     line["date"], date_formats.get(partner_id, default_fmt)
#                 )
#                 line["date_maturity"] = format_date(
#                     line["date_maturity"], date_formats.get(partner_id, default_fmt)
#                 )
#                 if line['balance'] != 0.0:
#                     print('111111111111111111111111111',line['balance'])
#                     line_currency["lines"].append(line)

#             if data["show_aging_buckets"]:
#                 for line in buckets[partner_id]:
#                     if line["currency_id"] not in currency_dict:
#                         (
#                             currency_dict[line["currency_id"]],
#                             currencies,
#                         ) = self._get_line_currency_defaults(
#                             line["currency_id"], currencies, 0.0
#                         )
#                     line_currency = currency_dict[line["currency_id"]]
#                     line_currency["buckets"] = line

#             if len(partner_ids) > 1:
#                 values = currency_dict.values()
#                 if not any([v["lines"] or v["balance_forward"] for v in values]):
#                     if data["filter_non_due_partners"]:
#                         partners_to_remove.add(partner_id)
#                         continue
#                     else:
#                         res[partner_id]["no_entries"] = True
#                 if data["filter_negative_balances"]:
#                     if not all([v["amount_due"] >= 0.0 for v in values]):
#                         partners_to_remove.add(partner_id)

#         for partner in partners_to_remove:
#             del res[partner]
#             partner_ids.remove(partner)
#         return super()._get_report_values(docids, data)
