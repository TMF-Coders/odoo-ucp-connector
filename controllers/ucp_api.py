import json
from odoo import http
from odoo.http import request

class UcpApiController(http.Controller):

    @http.route('/ucp/v1/checkout-sessions', type='json', auth='api_key', methods=['POST'], csrf=False)
    def create_checkout_session(self, **post):
        """
        Initialize a UCP checkout session.
        Authentication: api_key (Odoo 18 native / custom module)
        """
        payload = request.get_json_data()
        
        try:
            # MVP: Create order
            order = request.env['sale.order'].sudo()._create_from_ucp_payload(payload)
            return order._to_ucp_checkout_format()
        except ValueError as e:
            return {'error': str(e)}
        except Exception as e:
            return {'error': 'Internal Server Error while creating UCP Session'}

    @http.route('/ucp/v1/checkout-sessions/<string:session_id>', type='json', auth='api_key', methods=['PUT'], csrf=False)
    def update_checkout_session(self, session_id, **post):
        """
        Update a UCP checkout session (e.g., shipping, items).
        """
        payload = request.get_json_data()
        order = request.env['sale.order'].sudo().search([('ucp_session_id', '=', session_id)], limit=1)
        
        if not order:
            return {'error': 'Session not found'}
            
        try:
            # Clear existing lines to replace with new payload (Full Cart sync)
            order.order_line.unlink()
            
            # Map new lines
            order_lines = []
            for line in payload.get('lines', []):
                product_id = int(line.get('id', 0))
                product = request.env['product.product'].sudo().browse(product_id)
                if not product.exists():
                    raise ValueError(f"Product ID {product_id} not found in catalog")
    
                order_lines.append((0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': line.get('quantity', 1),
                }))
                
            order.write({'order_line': order_lines})
            return order._to_ucp_checkout_format()
        except ValueError as e:
            return {'error': str(e)}
        except Exception as e:
            return {'error': 'Internal Server Error while updating UCP Session'}

    @http.route('/ucp/v1/checkout-sessions/<string:session_id>/complete', type='json', auth='api_key', methods=['POST'], csrf=False)
    def complete_checkout_session(self, session_id, **post):
        """
        Finalize order and process payment_data.
        """
        payload = request.get_json_data()
        order = request.env['sale.order'].sudo().search([('ucp_session_id', '=', session_id)], limit=1)
        
        if not order:
            return {'error': 'Session not found'}
            
        payment_data = payload.get('payment_data')
        
        try:
            if payment_data:
                # TODO: Integrate with Odoo payment.transaction logic
                # For an Agent MVP, we trust the agent's payment_data string to represent an authorized mandate
                order.action_confirm()
                
            return order._to_ucp_checkout_format()
        except Exception as e:
            return {'error': 'Internal Server Error while completing UCP Session'}
