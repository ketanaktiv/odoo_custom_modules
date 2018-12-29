# -*- coding: utf-8 -*-
{
    'name': "Box Manufacturing",
    'summary': """
        It will restrict unnecessary manufacturing order of box product.""",
    'description': """
        This module is auto installed when you install
        manufacturing module and Box packaging Module.
    """,
    'author': "TechUltra",
    'website': "http://www.techultra.in",
    'category': 'Product',
    'version': '11.0.1.0.0',
    'license': 'OPL-1',
    'depends': ['box_packing', 'mrp'],
    'data': [
        'views/product_view.xml',
    ],
    'auto_install': True,
    'installable': True,
    'application': False,
}
