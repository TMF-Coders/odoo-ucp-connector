import json
from odoo import http
from odoo.http import request

class UcpApiController(http.Controller):

    @http.route('/.well-known/ucp', type='http', auth='public', methods=['GET'], csrf=False)
    def ucp_discovery_profile(self, **kw):
        """
        UCP Discovery Profile. Mandatory for Google Market Platform.
        Returns the capabilities of this Odoo instance.
        """
        # In a real module, these credentials and capabilities would be configurable in odoo settings (res.config.settings)
        profile = {
          "version": "2026-01-23",
          "services": {
            "dev.ucp.shopping": {
              "capabilities": ["dev.ucp.shopping.checkout", "dev.ucp.shopping.order"],
              "payment_handlers": [
                {
                  "id": "com.google.pay", # Example generic handler
                  "configuration": {}
                }
              ]
            }
          }
        }
        return request.make_response(
            json.dumps(profile),
            headers=[('Content-Type', 'application/json')]
        )

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
                # Integrate with Odoo payment.transaction logic defined in the model
                order._process_ucp_payment(payment_data)
                
            return order._to_ucp_checkout_format()
        except Exception as e:
            return {'error': 'Internal Server Error while completing UCP Session'}
