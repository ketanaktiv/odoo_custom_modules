from odoo import models, fields, api


class AddBoxProduct(models.TransientModel):
    _name = "add.box.product"

    product_id = fields.Many2one('product.product',
                                 string="Product", required=True,
                                 domain="[('box_pack', '=', True)]")
    product_qty = fields.Float(string="Quantity", required=True)

    @api.multi
    def create_box_order_line(self):
        order_id = self._context.get('active_id')
        order_rec = self.env['sale.order'].browse([order_id])
        order_rec.order_line = [(0, 0,
                                 {'product_id': self.product_id.id,
                                  'product_uom_qty': self.product_qty,
                                  'order_id': order_id,
                                  'name': self.product_id.name,
                                  'price_unit': self.product_id.list_price})]
