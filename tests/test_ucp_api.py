from odoo.tests.common import HttpCase, tagged
import json

@tagged('post_install', '-at_install')
class TestUcpApiController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super(TestUcpApiController, cls).setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'API Test Product',
            'list_price': 150.0,
        })
        
        cls.api_key = 'test_secret_key_123'
        cls.test_user = cls.env['res.users'].create({
            'name': 'UCP Test User',
            'login': 'ucp_test_user_identity',
        })
        cls.env['ucp.bearer.token'].create({
            'name': 'Test Token',
            'token': cls.api_key,
            'user_id': cls.test_user.id
        })
        
        cls.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {cls.api_key}'
        }

    def test_01_create_checkout_session_api(self):
        payload = {
            'session_id': 'api_session_001',
            'lines': [{'id': self.product.id, 'quantity': 1}]
        }
        
        response = self.url_open(
            '/ucp/v1/checkout-sessions',
            data=json.dumps(payload),
            headers=self.headers,
            method='POST'
        )
        
        self.assertEqual(response.status_code, 201)
        result = response.json()
        self.assertEqual(result.get('session_id'), 'api_session_001')

    def test_01b_create_idempotent(self):
        payload = {
            'session_id': 'api_session_idem',
            'lines': [{'id': self.product.id, 'quantity': 1}]
        }
        
        headers = self.headers.copy()
        headers['Idempotency-Key'] = 'idem-123'
        
        # First call
        resp1 = self.url_open('/ucp/v1/checkout-sessions', data=json.dumps(payload), headers=headers, method='POST')
        self.assertEqual(resp1.status_code, 201)
        
        # Second call
        resp2 = self.url_open('/ucp/v1/checkout-sessions', data=json.dumps(payload), headers=headers, method='POST')
        self.assertEqual(resp2.status_code, 201)
        
        # Should be exactly 1 order
        orders = self.env['sale.order'].search([('ucp_session_id', '=', 'api_session_idem')])
        self.assertEqual(len(orders), 1)

    def test_02_update_checkout_session_api(self):
        order = self.env['sale.order'].create({
            'ucp_session_id': 'api_session_002',
            'partner_id': self.env.ref('base.public_partner').id,
        })
        
        payload = {
            'session_id': 'api_session_002',
            'lines': [{'id': self.product.id, 'quantity': 3}]
        }
        
        response = self.url_open(
            '/ucp/v1/checkout-sessions/api_session_002',
            data=json.dumps(payload),
            headers=self.headers,
            method='PUT'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.order_line[0].product_uom_qty, 3)

    def test_03_invalid_product_api(self):
        payload = {
            'session_id': 'api_session_bad',
            'lines': [{'id': 999999, 'quantity': 1}]
        }
        
        response = self.url_open(
            '/ucp/v1/checkout-sessions',
            data=json.dumps(payload),
            headers=self.headers,
            method='POST'
        )
        
        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertIn('error', result)
        self.assertIn('not found in catalog', result['error'])

    def test_04_discovery_profile(self):
        response = self.url_open('/.well-known/ucp')
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result.get('version'), '2026-01-23')
