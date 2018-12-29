from odoo import models, api


class Product(models.Model):
    _inherit = "product.product"

    @api.onchange('box_product_ids')
    def calulate_cost_price(self):
        for product_rec in self:
            product_recs = product_rec.box_product_ids
            product_rec.standard_price = 0
            for product in product_recs:
                standard_price = product.product_id.standard_price
                product_rec.standard_price += product.product_qty * standard_price