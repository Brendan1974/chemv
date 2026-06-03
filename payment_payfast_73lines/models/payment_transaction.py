"""PayFast transaction lifecycle (v18 port of 73lines v16 module)."""
import logging
import pprint
import re

from werkzeug import urls

from odoo import _, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_payfast_73lines import const
from odoo.addons.payment_payfast_73lines.controllers.main import PayFastController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # ---- Outgoing: build the redirect-form payload ----
    def _get_specific_rendering_values(self, processing_values):
        """Override of `payment` to return PayFast-specific rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'payfast_73lines':
            return res

        first_name, last_name = payment_utils.split_partner_name(self.partner_name)
        base_url = self.provider_id.get_base_url()
        custom_int1 = re.sub(r'[^0-9]', '', self.partner_phone or '') or ''

        data = {
            'merchant_id': self.provider_id.payfast_merchant_id or '',
            'merchant_key': self.provider_id.payfast_secret or '',
            'return_url':  urls.url_join(base_url, PayFastController._return_url),
            'cancel_url':  urls.url_join(base_url, PayFastController._cancel_url),
            'notify_url':  urls.url_join(base_url, PayFastController._notify_url),
            'name_first':  first_name,
            'name_last':   last_name,
            'email_address': self.partner_email or '',
            'm_payment_id': processing_values['reference'],
            'amount': f'{processing_values["amount"]:.2f}',
            'item_name': processing_values['reference'],
            'item_description': f'{self.company_id.name}:{processing_values["reference"]}',
            'custom_int1': custom_int1,
            'custom_str1': processing_values['reference'],
        }
        data['signature'] = self.provider_id._payfast_generate_signature(data)
        data['api_url'] = self.provider_id._payfast_get_api_url()
        return data

    # ---- Incoming: find the transaction from notification payload ----
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of `payment` to locate the transaction from PayFast notification data.

        Tolerates Odoo's `<ref>-<n>` retry-suffix convention: if no exact match,
        falls back to matching transactions whose reference starts with the supplied
        token. Mirrors the v16 behaviour of `tx.reference.split('-')[0] == ref`.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'payfast_73lines' or tx:
            return tx

        reference = notification_data.get('m_payment_id') or notification_data.get('reference')
        if not reference:
            raise ValidationError(
                "PayFast: " + _("Received notification data with no reference.")
            )
        tx = self.search([
            ('reference', '=', reference),
            ('provider_code', '=', 'payfast_73lines'),
        ], limit=1)
        if not tx:
            tx = self.search([
                ('reference', '=like', f'{reference}-%'),
                ('provider_code', '=', 'payfast_73lines'),
            ], order='id desc', limit=1)
        if not tx:
            raise ValidationError(
                "PayFast: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    # ---- Incoming: apply the notification to the transaction ----
    def _process_notification_data(self, notification_data):
        """Override of `payment` to transition the transaction based on PayFast status."""
        super()._process_notification_data(notification_data)
        if self.provider_code != 'payfast_73lines':
            return

        if not notification_data:
            self._set_canceled(state_message=_("The customer left the PayFast checkout."))
            return

        pf_payment_id = notification_data.get('pf_payment_id')
        if pf_payment_id:
            self.provider_reference = pf_payment_id

        status = (notification_data.get('payment_status') or '').upper()
        if status in const.PAYMENT_STATUS_MAPPING['done']:
            self._set_done()
        elif status in const.PAYMENT_STATUS_MAPPING['cancel']:
            self._set_canceled()
        elif status in const.PAYMENT_STATUS_MAPPING['error']:
            self._set_error(
                "PayFast: " + _("Payment failed with status: %s", status)
            )
        else:
            _logger.warning(
                "PayFast: received unknown payment_status=%r for reference=%s; full payload:\n%s",
                status, self.reference, pprint.pformat(notification_data),
            )
            self._set_error(
                "PayFast: " + _("Received notification with invalid payment status: %s", status)
            )
