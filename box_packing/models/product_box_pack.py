from odoo import fields, models


class ProductBoxPack(models.Model):
    _name = "product.box.pack"

    company_id = fields.Many2one(
        'res.company', string="Company", required=True,
        default=lambda self: self.env['res.company'].
        _company_default_get('product.box.pack'))
    product_id = fields.Many2one('product.product',
                                 string="Product", required=True,
                                 domain="[('box_pack', '=', False)]")
    product_qty = fields.Float(string="Product Quantity", required=True)
    product_tmpl_id = fields.Many2one('product.template',
                                      string="Product Template")
