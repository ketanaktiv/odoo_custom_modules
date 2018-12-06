# -*- coding: utf-8 -*-
{
    'name': "Aged Partner Balance Report",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'category': 'Accounting',
    'author': "Knowledge Bases",
    'website': "https://www.knowledge-bases.com",
    'company': 'Knowledge Bases',
    'depends': ['account', 'account_reports'],
    'version': '11.0.1.0.0',
    'license': 'LGPL-3',
    'data': [
        'reports/aged_partner_balance_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
