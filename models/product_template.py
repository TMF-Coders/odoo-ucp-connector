from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_ucp_capabilities(self):
        """
        Returns UCP capabilities for this product.
        Can be extended by other modules to add more capabilities.
        """
        self.ensure_one()
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description_sale or self.name,
            "price": self.list_price,
            "currency": self.currency_id.name,
            "availability": "in_stock" if getattr(self, 'qty_available', 1) > 0 else "out_of_stock",
        }
