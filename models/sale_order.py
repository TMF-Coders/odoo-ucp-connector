import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ucp_session_id = fields.Char(string='UCP Session ID', copy=False, index=True)
    ucp_mandate_hash = fields.Char(string='UCP Mandate Hash', copy=False)

    @api.model
    def _create_from_ucp_payload(self, payload):
        """
        Creates a draft sale order from a UCP checkout payload.
        Expects payload struct: {'session_id': str, 'lines': [{'id': str, 'quantity': int}]}
        """
        session_id = payload.get('session_id')
        if not session_id:
            raise ValueError("UCP Payload missing session_id")

        # Find a default public partner or Agent Partner (MVP: take the first or create one)
        agent_partner = self.env['res.partner'].search([('name', '=', 'UCP Agent Guest')], limit=1)
        if not agent_partner:
            agent_partner = self.env['res.partner'].create({'name': 'UCP Agent Guest'})

        order_lines = []
        for line in payload.get('lines', []):
            product_id = int(line.get('id', 0))
            product = self.env['product.product'].browse(product_id)
            if not product.exists():
                raise ValueError(f"Product ID {product_id} not found in catalog")

            order_lines.append((0, 0, {
                'product_id': product.id,
                'product_uom_qty': line.get('quantity', 1),
            }))

        order = self.create({
            'ucp_session_id': session_id,
            'partner_id': agent_partner.id,
            'order_line': order_lines,
        })
        
        return order

    def _to_ucp_checkout_format(self):
        """
        Maps a Sale Order to the UCP Checkout format.
        """
        self.ensure_one()
        
        lines = []
        for line in self.order_line:
            lines.append({
                'id': str(line.product_id.id),
                'name': line.name,
                'quantity': line.product_uom_qty,
                'unit_price': line.price_unit,
                'total_price': line.price_subtotal,
            })
            
        return {
            'session_id': self.ucp_session_id,
            'status': self.state, # mapping would be needed (sale -> complete, draft -> incomplete)
            'lines': lines,
            'totals': {
                'subtotal': self.amount_untaxed,
                'tax': self.amount_tax,
                'total': self.amount_total,
                'currency': self.currency_id.name,
            }
        }

    def _process_ucp_payment(self, payment_data):
        """
        Integrates with Odoo's native payment system.
        """
        self.ensure_one()
        # Example Implementation Stub:
        # 1. Look up payment provider mapping 
        # 2. Extract external token from payment_data dict
        # 3. Create a payment.transaction in Odoo linked to the sale.order
        # 4. Confirm transaction which auto-confirms order.
        
        # For UCP MVP, we log the token and forcefully confirm the order.
        _logger.info(f"Processing UCP Payment for {self.name}: {payment_data}")
        self.action_confirm()
        return True

    def write(self, vals):
        """ Override write to trigger UCP Webhooks. """
        res = super(SaleOrder, self).write(vals)
        # Check if status changed and it's a UCP order
        if 'state' in vals:
            for order in self.filtered('ucp_session_id'):
                order._trigger_ucp_webhook('status_update', vals['state'])
        return res

    def _trigger_ucp_webhook(self, event_type, new_status):
        """
        Stub for firing outgoing requests.
        In a production module, this would enqueue a job using queue_job 
        or send a requests.post() immediately to the Partner webhook URL.
        """
        payload = {
            'session_id': self.ucp_session_id,
            'event': event_type,
            'order_state': new_status,
        }
        _logger.info(f"Triggering UCP Webhook: {payload}")
        # requests.post(partner_ucp_webhook_url, json=payload)

