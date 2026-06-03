# -*- coding: utf-8 -*-

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _has_sale_invoice_confirmation_group(self):
        """Check if the user (or current user) has the custom invoice confirmation group."""
        users = self or self.env.user
        sale_invoice_group = self.env.ref(
            "v15_invoice_creation.sale_invoice_creation",
            raise_if_not_found=False,
        )
        if not sale_invoice_group:
            return False
            
        
        return any(sale_invoice_group in user.groups_id for user in users)

    def _is_accounting_group(self, group_ext_id: str) -> bool:
        """Centralized list of accounting groups we wish to mimic."""
        return group_ext_id in {
            "account.group_account_invoice",
            "account.group_account_manager",
        }

    @api.readonly
    def has_group(self, group_ext_id: str) -> bool:
        """Override has_group to grant accounting access to Sale Invoice Confirmation users."""
        if self._is_accounting_group(group_ext_id) and self._has_sale_invoice_confirmation_group():
            return True
        return super().has_group(group_ext_id)

    @api.readonly
    def _has_group(self, group_ext_id: str) -> bool:
        """Internal override to ensure backend/security checks also pass."""
        if self._is_accounting_group(group_ext_id) and self._has_sale_invoice_confirmation_group():
            return True
        return super()._has_group(group_ext_id)
