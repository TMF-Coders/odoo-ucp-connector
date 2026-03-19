import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class UcpApiController(http.Controller):

    def _authenticate(self):
        """
        Validates the 'Authorization: Bearer <TOKEN>' header.
        Returns False if invalid, True if valid.
        """
        auth_header = request.httprequest.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return False
            
        token_string = auth_header.split('Bearer ')[1]
        
        TokenModel = request.env['ucp.bearer.token'].sudo()
        token_record = TokenModel.search([('token', '=', token_string)], limit=1)
        
        if not token_record:
            return False
            
        from odoo import fields
        if token_record.expiration and token_record.expiration < fields.Datetime.now():
            return False
            
        # Switch the active request environment to run as the mapped user
        request.update_env(user=token_record.user_id.id)
        return True

    def _json_response(self, data, status=200):
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')],
            status=status
        )

    @http.route('/.well-known/ucp', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def ucp_discovery_profile(self, **kw):
        """
        UCP Discovery Profile.
        """
        profile = {
          "version": "2026-01-23",
          "services": {
            "dev.ucp.shopping": {
              "capabilities": ["dev.ucp.shopping.checkout", "dev.ucp.shopping.order"],
              "payment_handlers": [
                {
                  "id": "com.google.pay", 
                  "configuration": {}
                }
              ]
            }
          }
        }
        return self._json_response(profile)

    @http.route('/ucp/v1/checkout-sessions', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_checkout_session(self, **kw):
        """
        Initialize a UCP checkout session (REST).
        """
        if not self._authenticate():
            return self._json_response({'error': 'Unauthorized'}, 401)
            
        try:
            payload = json.loads(request.httprequest.data)
        except Exception:
            return self._json_response({'error': 'Invalid JSON'}, 400)
            
        try:
            idempotency_key = request.httprequest.headers.get('Idempotency-Key')
            # We use a targeted sudo only for the specific operation model
            SaleOrder = request.env['sale.order'].sudo()
            order = SaleOrder._create_from_ucp_payload(payload, idempotency_key=idempotency_key)
            return self._json_response(order._to_ucp_checkout_format(), 201)
        except ValueError as e:
            return self._json_response({'error': str(e)}, 400)
        except Exception as e:
            _logger.error("Failed creating UCP session: %s", str(e))
            return self._json_response({'error': 'Internal Server Error'}, 500)

    @http.route('/ucp/v1/checkout-sessions/<string:session_id>', type='http', auth='public', methods=['PUT'], csrf=False, cors='*')
    def update_checkout_session(self, session_id, **kw):
        """
        Update a UCP checkout session (REST).
        """
        if not self._authenticate():
            return self._json_response({'error': 'Unauthorized'}, 401)
            
        try:
            payload = json.loads(request.httprequest.data)
        except Exception:
            return self._json_response({'error': 'Invalid JSON'}, 400)

        SaleOrder = request.env['sale.order'].sudo()
        order = SaleOrder.search([('ucp_session_id', '=', session_id)], limit=1)
        
        if not order:
            return self._json_response({'error': 'Session not found'}, 404)
            
        try:
            idempotency_key = request.httprequest.headers.get('Idempotency-Key')
            # Reconcile lines happens in the model now
            order._update_from_ucp_payload(payload, idempotency_key=idempotency_key)
            return self._json_response(order._to_ucp_checkout_format())
        except ValueError as e:
            return self._json_response({'error': str(e)}, 400)
        except Exception as e:
             _logger.error("Failed updating UCP session: %s", str(e))
             return self._json_response({'error': 'Internal Server Error'}, 500)

    @http.route('/ucp/v1/checkout-sessions/<string:session_id>/complete', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def complete_checkout_session(self, session_id, **kw):
        """
        Finalize order and process payment_data.
        """
        if not self._authenticate():
            return self._json_response({'error': 'Unauthorized'}, 401)
            
        try:
            payload = json.loads(request.httprequest.data)
        except Exception:
            return self._json_response({'error': 'Invalid JSON'}, 400)

        SaleOrder = request.env['sale.order'].sudo()
        order = SaleOrder.search([('ucp_session_id', '=', session_id)], limit=1)
        
        if not order:
            return self._json_response({'error': 'Session not found'}, 404)
            
        idempotency_key = request.httprequest.headers.get('Idempotency-Key')
        payment_data = payload.get('payment_data')
        
        try:
            if payment_data:
                order._process_ucp_payment(payment_data, idempotency_key)
                
            return self._json_response(order._to_ucp_checkout_format())
        except Exception as e:
             _logger.error("Failed completing UCP session: %s", str(e))
             return self._json_response({'error': 'Internal Server Error'}, 500)
