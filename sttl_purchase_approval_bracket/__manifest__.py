# -*- coding: utf-8 -*-
{
    'name': 'Purchase Approval Bracket',
    'version': '16.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Multi-level purchase approval workflow with bracket-based thresholds',
    'description': 'static/description/index.html',
    'author': 'Bilal Benmerzoug - Adoctor Solutions',
    'website': 'https://adoctor.org',
    'depends': [
        'purchase',
        'stock',
        'mail',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/purchase_approval_security.xml',
        
        # Data
        'data/mail_activity_type.xml',
        
        # Views
        'views/purchase_approval_bracket_views.xml',
        'views/purchase_order_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    
    # Marketplace-specific fields
    'price': 69.00,
    'currency': 'EUR',
    'support_url': 'https://adoctor.org/support',
    'images': [
        'static/description/purchase_approval_bracket.jpg',
        'static/description/bracket-configuration.png',
        'static/description/bracketlist.jpg',
        'static/description/to-be-approved-purchases.jpg',
    ],
    'maintainer': 'Adoctor Solutions',
    'contributors': ['Bilal Benmerzoug'],
    'license': 'LGPL-3',
}