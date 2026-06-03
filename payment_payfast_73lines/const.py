# PayFast operates exclusively in South Africa and only accepts ZAR.
# See https://developers.payfast.co.za/docs#receiver_options
SUPPORTED_CURRENCIES = ['ZAR']

# Map PayFast's notification statuses to Odoo payment.transaction transitions.
PAYMENT_STATUS_MAPPING = {
    'done':   ('COMPLETE',),
    'cancel': ('CANCELLED', 'CANCEL'),
    'error':  ('FAILED',),
}

DEFAULT_PAYMENT_METHOD_CODES = {
    'card',
}
