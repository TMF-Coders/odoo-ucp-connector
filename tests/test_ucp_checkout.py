from odoo.tests.common import TransactionCase

class TestUcpCheckout(TransactionCase):

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
            'lines': [{'id': self.product.product_variant_id.id, 'quantity': 2}]
        }
        order = self.sale_order_model._create_from_ucp_payload(payload, idempotency_key='test-key')
        self.assertEqual(order.ucp_session_id, 'ucp_sess_123456')
        self.assertEqual(order.ucp_idempotency_key, 'test-key')
        self.assertEqual(order.state, 'draft')
        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.order_line[0].product_id, self.product.product_variant_id)
        self.assertEqual(order.order_line[0].product_uom_qty, 2)
        
    def test_03_create_order_invalid_product(self):
        """ Test that invalid products raise ValueError """
        payload = {
            'session_id': 'ucp_sess_invalid',
            'lines': [{'id': 999999, 'quantity': 1}]
        }
        with self.assertRaises(ValueError):
            self.sale_order_model._create_from_ucp_payload(payload)


