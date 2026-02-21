from odoo.tests.common import SavepointCase

class TestUcpCheckout(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestUcpCheckout, cls).setUpClass()
        cls.sale_order_model = cls.env['sale.order']
        # Set up a test product
        cls.product = cls.env['product.template'].create({
            'name': 'UCP Test Product',
            'list_price': 100.0,
        })

    def test_01_product_capabilities_mapping(self):
        """ Test that a product template exposes the required UCP structure """
        caps = self.product._get_ucp_capabilities()
        self.assertEqual(caps['name'], 'UCP Test Product')
        self.assertEqual(caps['price'], 100.0)
        
    def test_02_create_order_from_ucp(self):
        """ Test that a UCP payload generates a valid Sale Order draft """
        payload = {
            'session_id': 'ucp_sess_123456',
            'lines': [{'id': self.product.id, 'quantity': 1}]
        }
        order = self.sale_order_model._create_from_ucp_payload(payload)
        self.assertEqual(order.ucp_session_id, 'ucp_sess_123456')
        self.assertEqual(order.state, 'draft')
