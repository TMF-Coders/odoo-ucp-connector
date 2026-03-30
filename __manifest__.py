{
    'name': 'Universal Commerce Protocol (UCP) Connector',
    'version': '19.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Integrate Odoo eCommerce with Google Universal Commerce Protocol (UCP)',
    'description': """
Universal Commerce Protocol (UCP) Connector
===========================================
This module enables generative AI agents (like Google Gemini) to seamlessly interact with your Odoo eCommerce backend.

Key Features:
-------------
- Exposes UCP REST Endpoints (/ucp/v1/checkout-sessions)
- Maps UCP schemas to Odoo Sales Orders
- Enables AI agents to negotiate prices, check inventory, and complete orders.
    """,
    'author': 'TMFCoders SL',
    'website': 'https://tmfcoders.com',
    'price': 99.00,
    'currency': 'EUR',
    'license': 'OPL-1',
    'depends': [
        'base',
        'sale',
        'sale_management',
        'website_sale',
        'payment'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ucp_bearer_token_views.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
