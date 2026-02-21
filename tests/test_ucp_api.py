from odoo.tests.common import HttpCase, tagged
import json

@tagged('post_install', '-at_install')
class TestUcpApiController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super(TestUcpApiController, cls).setUpClass()
        # Create a test product
        cls.product = cls.env['product.product'].create({
            'name': 'API Test Product',
            'list_price': 150.0,
        })
        
        # We need a user with an API key for auth (simplified mapping for HttpCase)
        # In a real Odoo environment, you'd configure an ir.profile or specific auth token.
        # For this test, we assume the Odoo instance handles the auth routing.

    def test_01_create_checkout_session_api(self):
        """ Integration Test: POST /ucp/v1/checkout-sessions """
        payload = {
            'session_id': 'api_session_001',
            'lines': [{'id': self.product.id, 'quantity': 1}]
        }
        
        # Use url_open to simulate the HTTP POST request (must pass JSON)
        headers = {'Content-Type': 'application/json'}
        data = {'params': payload} # Odoo JSON-RPC wraps payloads in 'params' optionally, or direct get_json_data
        
        # Note: Depending on Odoo's exact JSON routing, we use json.dumps
        response = self.url_open(
            '/ucp/v1/checkout-sessions',
            data=json.dumps(payload).encode('utf-8'),
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, "API should return 200 OK")
        result = response.json()
        
        # Check if the API returned the expected UCP checkout format
        self.assertEqual(result.get('session_id'), 'api_session_001')
        self.assertEqual(result.get('result', {}).get('session_id') or result.get('session_id'), 'api_session_001')

    def test_02_update_checkout_session_api(self):
        """ Integration Test: PUT /ucp/v1/checkout-sessions/<id> """
        # 1. Create it first directly in ORM to simulate existing session
        order = self.env['sale.order'].create({
            'ucp_session_id': 'api_session_002',
            'partner_id': self.env.ref('base.public_partner').id,
        })
        
        payload = {
            'session_id': 'api_session_002',
            'lines': [{'id': self.product.id, 'quantity': 3}]
        }
        
        headers = {'Content-Type': 'application/json'}
        response = self.url_open(
            f'/ucp/v1/checkout-sessions/api_session_002',
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='PUT'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.order_line[0].product_uom_qty, 3)

    def test_03_invalid_product_api(self):
        """ Integration Test: Error handling for bad payload """
        payload = {
            'session_id': 'api_session_bad',
            'lines': [{'id': 999999, 'quantity': 1}]
        }
        
        response = self.url_open(
            '/ucp/v1/checkout-sessions',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 200) # Odoo json handlers often return 200 with error in body
        result = response.json()
        self.assertIn('error', result)
        self.assertIn('not found in catalog', result['error'])
