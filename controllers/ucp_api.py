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
        
        # TODO: Advanced validation, Partner matching
        # MVP: Create order
        order = request.env['sale.order'].sudo()._create_from_ucp_payload(payload)
        
        return order._to_ucp_checkout_format()

    @http.route('/ucp/v1/checkout-sessions/<string:session_id>', type='json', auth='api_key', methods=['PUT'], csrf=False)
    def update_checkout_session(self, session_id, **post):
        """
        Update a UCP checkout session (e.g., shipping, items).
        """
        payload = request.get_json_data()
        order = request.env['sale.order'].sudo().search([('ucp_session_id', '=', session_id)], limit=1)
        
        if not order:
            return {'error': 'Session not found'}
            
        # TODO: update logic here based on payload
        
        return order._to_ucp_checkout_format()

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
        
        if payment_data:
            # TODO: Integrate with Odoo payment.transaction logic
            # order.action_confirm() as a stub for successful payment
            order.action_confirm()
            
        return order._to_ucp_checkout_format()
