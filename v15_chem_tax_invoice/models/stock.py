from odoo import api, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def action_view_inventory(self):
        action = super().action_view_inventory()
        form_view = self.env.ref('stock.view_stock_quant_form_editable').id

        action['view_mode'] = 'list,form'
        action['views'] = [
            (view_id, view_type)
            for view_id, view_type in action.get('views', [])
            if view_type != 'form'
        ]
        action['views'].append((form_view, 'form'))
        return action
