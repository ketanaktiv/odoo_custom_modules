from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('type', 'in', ['product', 'consu']),
                ('box_pack', '=', False)],
        readonly=True, required=True,
        states={'confirmed': [('readonly', False)]})

    @api.model
    def create(self, vals):
        product_id = self.env['product.product'].browse(
            [vals.get('product_id')])
        if product_id.box_pack:
            raise ValidationError(_("Can't create box product production."))
        return super(MrpProduction, self).create(vals)
