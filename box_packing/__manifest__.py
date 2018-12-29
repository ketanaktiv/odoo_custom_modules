# -*- coding: utf-8 -*-
{
    'name': "Box Packing",
    'summary': """
    """,
    'description': """
        This module allows you to sell your product in box,
        once you put product in box,
        box will start to behave like separate product.
        And you can easily keep track of box.
    """,
    'author': "My Company",
    'website': "http://www.techultra.in",
    'category': 'Product',
    'version': '11.0.1.0.0',
    'license': 'OPL-1',
    'price': 44.00,
    'currency': "EUR",
    'depends': ['sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/box_product_security.xml',
        'wizard/add_box_product_view.xml',
        'views/product_template_views.xml',
        'views/sale_order_view.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
