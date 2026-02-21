from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ucp_session_id = fields.Char(string='UCP Session ID', copy=False, index=True)
    ucp_mandate_hash = fields.Char(string='UCP Mandate Hash', copy=False)

    @api.model
    def _create_from_ucp_payload(self, payload):
        """
        Creates a draft sale order from a UCP checkout payload.
        """
        # Logic to map UCP payload to Odoo order lines, etc.
        # This is an MVP stub for now, expecting a dictionary.
        
        # Simplified example
        order = self.env['sale.order'].create({
            'ucp_session_id': payload.get('session_id'),
            # Partner ID would need to be determined from payload or a generic AI Agent partner
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
