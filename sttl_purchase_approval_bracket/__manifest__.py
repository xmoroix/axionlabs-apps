# -*- coding: utf-8 -*-
{
    'name': 'Purchase Approval Bracket',
    'version': '16.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Multi-level purchase approval workflow with bracket-based thresholds',
    'description': """
Purchase Approval Bracket
========================

This module implements a flexible multi-level approval system for purchase orders
based on configurable amount brackets. Each bracket can have different approvers
and can be optionally linked to specific locations.

Features
--------
* Extends Odoo's built-in purchase approval with bracket-based conditions
* Configurable approval brackets with min/max amounts
* Multiple approvers per bracket
* Optional location-specific brackets based on picking type destination location
* Automatic notification to approvers via activities and chatter
* Validates approver authorization
* Notifications sent on approval and cancellation
* Supports all currencies
* Sequential bracket matching (highest priority first)

Support
-------
Email: admin@adoctor.org
Response time: Within 48 hours
    """,
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
    'images': ['/sttl_purchase_approval_bracket/static/description/icon.png'],
    'icon': '/sttl_purchase_approval_bracket/static/description/icon.png',
    'maintainer': 'Adoctor Solutions',
    'contributors': ['Bilal Benmerzoug'],
    'license': 'LGPL-3',
}