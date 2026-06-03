"""PayFast payment provider (v18 port of 73lines v16 module)."""
import logging
import urllib.parse
from hashlib import md5

from odoo import _, api, fields, models

from odoo.addons.payment_payfast_73lines import const

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('payfast_73lines', "PayFast")],
        ondelete={'payfast_73lines': 'set default'},
    )
    payfast_merchant_id = fields.Char(
        string="PayFast Merchant ID",
        required_if_provider='payfast_73lines',
    )
    payfast_secret = fields.Char(
        string="PayFast Merchant Key",
        required_if_provider='payfast_73lines',
        groups='base.group_system',
    )
    payfast_passphrase = fields.Char(
        string="PayFast Passphrase",
        help="Optional. If configured in your PayFast dashboard, it must be set here too "
             "so that signed payloads validate.",
        groups='base.group_system',
    )

    # === BUSINESS METHODS === #

    def _get_supported_currencies(self):
        """Override of `payment` to restrict PayFast to ZAR."""
        supported = super()._get_supported_currencies()
        if self.code == 'payfast_73lines':
            supported = supported.filtered(lambda c: c.name in const.SUPPORTED_CURRENCIES)
        return supported

    def _get_default_payment_method_codes(self):
        """Override of `payment` to surface PayFast's default payment method codes."""
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'payfast_73lines':
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES

    def _payfast_get_api_url(self):
        """Return the PayFast process URL for the current provider state."""
        self.ensure_one()
        if self.state == 'enabled':
            return 'https://www.payfast.co.za/eng/process'
        return 'https://sandbox.payfast.co.za/eng/process'

    def _payfast_generate_signature(self, data):
        """Build PayFast's md5 signature over the URL-encoded payload.

        PayFast's algorithm (https://developers.payfast.co.za/docs#step_2_sign_your_data):
        - Fields must appear in the exact order listed below.
        - Empty/None fields are EXCLUDED from the signing string.
        - Values are URL-encoded using urllib.parse.quote_plus (spaces become +).
        - If a passphrase is set it is URL-encoded and appended last.
        """
        self.ensure_one()
        ordered_keys = (
            'merchant_id', 'merchant_key',
            'return_url', 'cancel_url', 'notify_url',
            'name_first', 'name_last', 'email_address',
            'm_payment_id', 'amount', 'item_name', 'item_description',
            'custom_int1', 'custom_str1',
        )
        parts = []
        for key in ordered_keys:
            val = data.get(key)
            # PayFast skips fields that are empty/None/zero-length
            if val is None or str(val).strip() == '':
                continue
            encoded_val = urllib.parse.quote_plus(str(val))
            parts.append(f'{key}={encoded_val}')
        signing_string = '&'.join(parts)
        if self.payfast_passphrase:
            encoded_phrase = urllib.parse.quote_plus(self.payfast_passphrase)
            signing_string += f'&passphrase={encoded_phrase}'
        _logger.debug("PayFast signing string: %s", signing_string)
        return md5(signing_string.encode('utf-8')).hexdigest()
