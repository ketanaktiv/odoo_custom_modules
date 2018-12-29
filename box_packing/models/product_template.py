from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    box_pack = fields.Boolean(string="Is Box Packing",
                              help="To create a box of multiple products.\
                              User can't create variants of this type of\
                              product.")
    box_product_ids = fields.One2many('product.box.pack', 'product_tmpl_id',
                                      string="Box Products")

    @api.onchange('box_pack')
    def _onchange_box_pack(self):
        if self.box_pack:
            self.type = 'consu'
            self.purchase_ok = False

    @api.model
    def create(self, vals):
        if vals.get('box_product_ids') and not vals.get('box_pack'):
            del vals['box_product_ids']
        if vals.get('box_pack') and vals.get('attribute_line_ids'):
            raise ValidationError(_('''It is not possible to create \
                variants of Box product.'''))
        if vals.get('box_pack') and vals.get('type') != 'consu':
            raise ValidationError(_('''Set Box products type consumable.'''))
        if vals.get('box_pack') and vals.get('purchase_ok'):
            raise ValidationError(_('''Box products cann't purchased.'''))
        return super(ProductTemplate, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        for product_temp_rec in self:
            if product_temp_rec.box_pack and \
                    product_temp_rec.attribute_line_ids:
                raise ValidationError(_('''It is not possible to create \
                variants of Box product.'''))
            if product_temp_rec.box_pack and product_temp_rec.purchase_ok:
                raise ValidationError(_('''Box products cann't purchased.'''))
            if product_temp_rec.box_pack and product_temp_rec.type != 'consu':
                raise ValidationError(_(
                    '''Set Box products type consumable.'''))
        return res

    @api.onchange('box_pack')
    def clear_box_products(self):
        for pro_temp_rec in self:
            pro_temp_rec.box_product_ids = [[2, 6, False]]

    @api.onchange('box_product_ids')
    def calulate_cost_price(self):
        for pro_temp_rec in self:
            product_recs = pro_temp_rec.box_product_ids
            pro_temp_rec.standard_price = 0
            for product in product_recs:
                standard_price = product.product_id.standard_price
                pro_temp_rec.standard_price += product.product_qty * standard_price
