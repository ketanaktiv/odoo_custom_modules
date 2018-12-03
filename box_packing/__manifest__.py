# -*- coding: utf-8 -*-
{
    'name': "Box Packing",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Product',
    'version': '0.1',
    'depends': ['sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/box_product_security.xml',
        'wizard/add_box_product_view.xml',
        'views/product_template_views.xml',
        'views/sale_order_view.xml',
    ],
}
