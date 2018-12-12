from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    product_tmpl_id = fields.Many2one(
        'product.template', 'Product',
        domain="[('type', 'in', ['product', 'consu']),\
                 ('box_pack', '=', False)]",
        required=True)

    @api.model
    def create(self, vals):
        product_rec = self.env['product.template'].browse(
            [vals.get('product_tmpl_id')])
        if product_rec.box_pack:
            raise ValidationError(_("Cann't create bom of box\
                products."))
        return super(MrpBom, self).create(vals)


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('box_pack', '=', False)]",
        required=True)

    @api.model
    def create(self, vals):
        product_rec = self.env['product.product'].browse(
            [vals.get('product_id')])
        if product_rec.box_pack:
            raise ValidationError(_("Cann't create bom of box\
                products."))
        return super(MrpBomLine, self).create(vals)
