# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.stock.models.product import OPERATORS


class AccountMOveInherit(models.Model):
    _inherit = "account.move"

    margin = fields.Monetary("Margin", compute='_compute_margin', store=False, search='_search_margin')
    margin_percent = fields.Float("Margin (%)", compute='_compute_margin', store=False, aggregator="avg", search='_search_margin_percentage')
    
    
    
    def _search_margin(self, operator, value):
        if operator not in ['=', '!=', '>', '<', '>=', '<=']:  # Ensure the operator is valid
            raise ValueError("Unsupported operator for margin search")

        ids = []
        for move in self.search([]):
            if OPERATORS[operator](move.margin, value):
                ids.append(move.id)
        return [("id", "in", ids)]
    
    def _search_margin_percentage(self, operator, value):
        if operator not in ['=', '!=', '>', '<', '>=', '<=']:  # Ensure the operator is valid
            raise ValueError("Unsupported operator for margin search")

        ids = []
        for move in self.search([]):
            if OPERATORS[operator](move.margin_percent, value):
                ids.append(move.id)
        return [("id", "in", ids)]

    @api.depends('invoice_line_ids.margin', 'amount_untaxed')
    def _compute_margin(self):
        # if not all(self._ids):
        for order in self:
            order.margin = sum(order.invoice_line_ids.mapped('margin'))
            order.margin_percent = order.amount_untaxed and (order.margin/order.amount_untaxed) 
        # else:
        #     # On batch records recomputation (e.g. at install), compute the margins
        #     # with a single read_group query for better performance.
        #     # This isn't done in an onchange environment because (part of) the data
        #     # may not be stored in database (new records or unsaved modifications).
        #     grouped_order_lines_data = self.env['account.move.line'].read_group(
        #         [
        #             ('move_id', 'in', self.ids),
        #         ], ['margin', 'move_id'], ['move_id'])
        #     mapped_data = {m['move_id'][0]: m['margin'] for m in grouped_order_lines_data}
        #     for order in self:
        #         order.margin = mapped_data.get(order.id, 0.0)
        #         order.margin_percent = order.amount_untaxed and order.margin/order.amount_untaxed

class ap_invoice_margin(models.Model):
    _inherit = 'account.move.line'

    margin = fields.Float(
        "Margin", compute='_compute_margin', search='_search_margin',
        digits='Product Price', store=False)
    margin_percent = fields.Float(
        "Margin (%)", compute='_compute_margin', store=False, search='_search_margin_percentage')

    purchase_price = fields.Float(
        string="Cost", compute="_compute_purchase_price",
        digits='Product Price', store=False, readonly=False, copy=False)

    def _search_margin(self, operator, value):
        if operator not in ['=', '!=', '>', '<', '>=', '<=']:  # Ensure the operator is valid
            raise ValueError("Unsupported operator for margin search")

        ids = []
        for move in self.search([]):
            if OPERATORS[operator](move.margin, value):
                ids.append(move.id)
        return [("id", "in", ids)]
    
    def _search_margin_percentage(self, operator, value):
        if operator not in ['=', '!=', '>', '<', '>=', '<=']:  # Ensure the operator is valid
            raise ValueError("Unsupported operator for margin search")

        ids = []
        for move in self.search([]):
            if OPERATORS[operator](move.margin_percent, value):
                ids.append(move.id)
        return [("id", "in", ids)]

    @api.depends('product_id', 'company_id', 'currency_id', 'product_uom_id')
    def _compute_purchase_price(self):
        for line in self:
            if not line.product_id:
                line.purchase_price = 0.0
                continue
            line = line.with_company(line.company_id)
            product_cost = line.product_id.standard_price
            line.purchase_price = line._convert_price(product_cost, line.product_id.uom_id)

    @api.depends('price_subtotal', 'quantity', 'purchase_price')
    def _compute_margin(self):
        for line in self:
            line.margin = line.price_subtotal - (line.purchase_price * line.quantity)
            line.margin_percent = line.price_subtotal and (line.margin/line.price_subtotal) * 100

    def _convert_price(self, product_cost, from_uom):
        self.ensure_one()
        if not product_cost:
            # If the standard_price is 0
            # Avoid unnecessary computations
            # and currency conversions
            if not self.purchase_price:
                return product_cost
        from_currency = self.product_id.cost_currency_id
        to_cur = self.currency_id or self.move_id.currency_id
        to_uom = self.product_uom_id
        if to_uom and to_uom != from_uom:
            product_cost = from_uom._compute_price(
                product_cost,
                to_uom,
            )
        return from_currency._convert(
            from_amount=product_cost,
            to_currency=to_cur,
            company=self.company_id or self.env.company,
            date=self.move_id.date or fields.Date.today(),
            round=False,
        ) if to_cur and product_cost else product_cost
