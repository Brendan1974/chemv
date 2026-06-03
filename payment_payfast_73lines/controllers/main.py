"""PayFast HTTP callbacks (v18)."""
import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PayFastController(http.Controller):
    _notify_url = '/payment/payfast/notify'
    _return_url = '/payment/payfast/return'
    _cancel_url = '/payment/payfast/cancel'

    @http.route(_notify_url, type='http', auth='public', methods=['POST'],
                csrf=False, save_session=False)
    def payfast_notify(self, **post):
        """Server-to-server ITN (Instant Transaction Notification) from PayFast.

        PayFast posts the final transaction status here. We acknowledge with an empty body
        regardless of whether the transaction can be located, otherwise PayFast retries.
        """
        _logger.info("PayFast: notify with data:\n%s", pprint.pformat(post))
        try:
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'payfast_73lines', post,
            )
            tx_sudo._handle_notification_data('payfast_73lines', post)
        except Exception:
            _logger.exception("PayFast: failed to handle notify payload; swallowing")
        return ''

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'],
                csrf=False, save_session=False, website=True)
    def payfast_return(self, **post):
        """Customer returns here after completing payment on PayFast.

        In production, PayFast also POSTs to ``/payment/payfast/notify`` server-to-server
        (ITN), and that path handles the transaction transition. On localhost / behind a
        firewall, the notify URL is unreachable, so we synthesize the same transition
        here from the session-tracked transaction. This matches the v16 controller's
        behaviour so localhost testing works end-to-end.
        """
        _logger.info("PayFast: return with data:\n%s", pprint.pformat(post))
        payload = dict(post) if post else {}
        # Browser redirect from PayFast often carries no body (GET). Fall back to the
        # in-flight tx tracked in session — same trick as v16's `payfast_return`.
        if not payload.get('m_payment_id') and not payload.get('reference'):
            tx_id = request.session.get('__website_sale_last_tx_id')
            if tx_id:
                tx = request.env['payment.transaction'].sudo().browse(int(tx_id)).exists()
                if tx and tx.provider_code == 'payfast_73lines':
                    payload['m_payment_id'] = tx.reference
                    payload.setdefault('payment_status', 'COMPLETE')
        if payload.get('m_payment_id') or payload.get('reference'):
            try:
                tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                    'payfast_73lines', payload,
                )
                tx_sudo._handle_notification_data('payfast_73lines', payload)
            except Exception:
                _logger.exception("PayFast: failed to handle return payload; redirecting anyway")
        return request.redirect('/payment/status')

    @http.route(_cancel_url, type='http', auth='public', methods=['GET', 'POST'],
                csrf=False, save_session=False, website=True)
    def payfast_cancel(self, **post):
        """Customer cancelled the payment on PayFast.

        PayFast may post back with no body when the user clicks Cancel. In that
        case fall back to the in-flight transaction tracked in the session so
        the customer doesn't see a stuck "processing" status page.
        """
        _logger.info("PayFast: cancel with data:\n%s", pprint.pformat(post))
        payload = dict(post) if post else {}
        payload.setdefault('payment_status', 'CANCELLED')
        if not payload.get('m_payment_id') and not payload.get('reference'):
            tx_id = request.session.get('__website_sale_last_tx_id')
            if tx_id:
                tx = request.env['payment.transaction'].sudo().browse(int(tx_id)).exists()
                if tx and tx.provider_code == 'payfast_73lines':
                    payload['m_payment_id'] = tx.reference
        try:
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'payfast_73lines', payload,
            )
            tx_sudo._handle_notification_data('payfast_73lines', payload)
        except Exception:
            _logger.exception("PayFast: failed to handle cancel payload; redirecting anyway")
        return request.redirect('/payment/status')
