import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ucp_session_id = fields.Char(string='UCP Session ID', copy=False, index=True)
    ucp_mandate_hash = fields.Char(string='UCP Mandate Hash', copy=False)
    ucp_idempotency_key = fields.Char(string='UCP Idempotency Key', copy=False, index=True)

    @api.model
    def _create_from_ucp_payload(self, payload, idempotency_key=None):
        if idempotency_key:
            existing = self.search([('ucp_idempotency_key', '=', idempotency_key)], limit=1)
            if existing:
                return existing

        session_id = payload.get('session_id')
        if not session_id:
            raise ValueError("UCP Payload missing session_id")

        # Identity Linking: the order belongs to the user authenticated via the UCP Bearer Token
        agent_partner = self.env.user.partner_id
        if not agent_partner:
            raise ValueError("Identity Linking Error: Authenticated user has no associated partner.")

        order_lines = []
        for line in payload.get('lines', []):
            product_id = int(line.get('id', 0))
            if not self.env['product.product'].browse(product_id).exists():
                raise ValueError(f"Product ID {product_id} not found in catalog")

            order_lines.append((0, 0, {
                'product_id': product_id,
                'product_uom_qty': line.get('quantity', 1),
            }))

        order = self.create({
            'ucp_session_id': session_id,
            'partner_id': agent_partner.id,
            'order_line': order_lines,
            'ucp_idempotency_key': idempotency_key,
        })
        
        return order

    def _update_from_ucp_payload(self, payload, idempotency_key=None):
        self.ensure_one()
        if idempotency_key and self.ucp_idempotency_key == idempotency_key:
            return self

        existing_lines = {line.product_id.id: line for line in self.order_line}
        
        processed_product_ids = set()
        
        for line in payload.get('lines', []):
            product_id = int(line.get('id', 0))
            qty = line.get('quantity', 1)
            processed_product_ids.add(product_id)
            
            if product_id in existing_lines:
                # Update existing line
                existing_lines[product_id].write({'product_uom_qty': qty})
            else:
                # Create new line
                if not self.env['product.product'].browse(product_id).exists():
                    raise ValueError(f"Product ID {product_id} not found in catalog")
                self.env['sale.order.line'].create({
                    'order_id': self.id,
                    'product_id': product_id,
                    'product_uom_qty': qty,
                })
        
        # Remove lines that were not in the payload
        for product_id, line in existing_lines.items():
            if product_id not in processed_product_ids:
                line.unlink()

        if idempotency_key:
            self.ucp_idempotency_key = idempotency_key

        return self

    def _to_ucp_checkout_format(self):
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
            'status': self.state,
            'lines': lines,
            'totals': {
                'subtotal': self.amount_untaxed,
                'tax': self.amount_tax,
                'total': self.amount_total,
                'currency': self.currency_id.name,
            }
        }

    def _process_ucp_payment(self, payment_data, idempotency_key=None):
        self.ensure_one()
        if idempotency_key and self.ucp_idempotency_key == idempotency_key:
            return True

        if self.state in ['sale', 'done']:
            return True

        _logger.info("Processing UCP Payment for %s: %s", self.name, payment_data)
        
        provider = self.env['payment.provider'].search([('code', '!=', False)], limit=1)
        if provider:
            tx = self.env['payment.transaction'].create({
                'amount': self.amount_total,
                'currency_id': self.currency_id.id,
                'provider_id': provider.id,
                'reference': self.name,
                'sale_order_ids': [(6, 0, self.ids)],
                'partner_id': self.partner_id.id,
            })
            tx._set_done()
            if self.state != 'sale':
                self.action_confirm()
        else:
            _logger.warning("No payment provider found, falling back to basic order confirm.")
            self.action_confirm()

        if idempotency_key:
            self.ucp_idempotency_key = idempotency_key
            
        return True

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'state' in vals:
            for order in self.filtered('ucp_session_id'):
                order._trigger_ucp_webhook('status_update', vals['state'])
        return res

    def _trigger_ucp_webhook(self, event_type, new_status):
        payload = {
            'session_id': self.ucp_session_id,
            'event': event_type,
            'order_state': new_status,
        }
        _logger.info("Triggering UCP Webhook: %s", payload)
