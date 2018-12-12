from odoo import fields, models


class MrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('box_pack', '=', False)],
        required=True,
        states={'done': [('readonly', True)]})
