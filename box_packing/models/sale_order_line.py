from odoo import models, api, _
from odoo.tools import float_compare
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def create(self, vals):
        print("\n\n", vals, "\n\n")
        return super(SaleOrderLine, self).create(vals)

    @api.onchange('product_id')
    def _onchange_product_id_set_customer_lead(self):
        self.customer_lead = self.product_id.sale_delay
        if self.product_id.box_pack:
            for box_product in self.product_id.box_product_ids:
                box_product_qty = box_product.product_qty
                if box_product.product_id.type == 'product':
                    precision = self.env['decimal.precision'].precision_get(
                        'Product Unit of Measure')
                    product = box_product.product_id.with_context(
                        warehouse=self.order_id.warehouse_id.id,
                        lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
                    )
                    product_qty = self.product_uom._compute_quantity(
                        box_product_qty, box_product.product_id.uom_id)
                    if float_compare(product.virtual_available, product_qty,
                                     precision_digits=precision) == -1:
                        is_available = self._check_routing()
                        if not is_available:
                            message = _('''You plan to sell %s %s %s but you \
                                only have %s %s available in %s\
                                 warehouse.''') % \
                                (box_product.product_id.name, box_product_qty,
                                    product.uom_id.name,
                                    product.virtual_available,
                                    product.uom_id.name,
                                    self.order_id.warehouse_id.name)
                            # We check if some products are available in other
                            # warehouses.
                            if float_compare(product.virtual_available,
                                             self.product_id.virtual_available,
                                             precision_digits=precision) == -1:
                                message += _('\nThere are %s %s available \
                                     accross all warehouses.') % \
                                    (self.product_id.virtual_available,
                                     product.uom_id.name)

                            warning_mess = {
                                'title': _('Not enough inventory!'),
                                'message': message
                            }
                            return {'warning': warning_mess}

    @api.multi
    def _action_launch_procurement_rule(self):
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        errors = []
        for line in self:
            if line.state != 'sale' or not line.product_id.type in ('consu', 'product'):
                continue
            qty = line._get_qty_procurement()
            if float_compare(qty, line.product_uom_qty,
                             precision_digits=precision) >= 0:
                continue

            group_id = line.order_id.procurement_group_id
            if not group_id:
                group_id = self.env['procurement.group'].create({
                    'name': line.order_id.name, 'move_type': line.order_id.picking_policy,
                    'sale_id': line.order_id.id,
                    'partner_id': line.order_id.partner_shipping_id.id,
                })
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update(
                        {'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update(
                        {'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            procurement_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if procurement_uom.id != quant_uom.id and get_param(
                    'stock.propagate_uom') != '1':
                product_qty = line.product_uom._compute_quantity(
                    product_qty, quant_uom, rounding_method='HALF-UP')
                procurement_uom = quant_uom

            try:
                if not line.product_id.box_pack:
                    self.env['procurement.group'].run(
                        line.product_id, product_qty, procurement_uom,
                        line.order_id.partner_shipping_id.property_stock_customer,
                        line.name, line.order_id.name, values)
                if line.product_id.box_pack:
                    self.env['procurement.group'].run(
                        line.product_id, product_qty, procurement_uom,
                        line.order_id.partner_shipping_id.property_stock_customer,
                        line.name, line.order_id.name, values)
                    for product in line.product_id.box_product_ids:
                        if product.product_id.type in ('consu', 'product'):
                            self.env['procurement.group'].run(
                                product.product_id,
                                product.product_qty * line.product_uom_qty,
                                procurement_uom,
                                line.order_id.partner_shipping_id.property_stock_customer,
                                line.name, line.order_id.name, values)
            except UserError as error:
                errors.append(error.name)
        if errors:
            raise UserError('\n'.join(errors))
        return True
