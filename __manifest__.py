# Veterinary Management Module for Odoo
# © 2025 Gerardo Alí Ferraro Schelijasch
# License OPL-1 (Odoo Proprietary License v1.0)
# www.soltecferr.com

{
    'name': 'Veterinary Management',
    'version': '19.0.1.0.0',
    'summary': 'Comprehensive Veterinary Clinic Management System',
    'category': 'Other',
    'author': 'Gerardo Alí Ferraro Schelijasch',
    'website': 'https://soltecferr.com',
    'license': 'OPL-1',
    'depends': [
        'base',
        'contacts',
        'sale',
        'stock',
        'account',
        'hr',
        'product',
    ],
    'data': [
        # Security
        'security/users.xml',
        'security/ir.model.access.csv',

        # sequences
        'data/sequence_consultation.xml',

        # Views
        'views/product_actions.xml',
        'views/account_move_views.xml',
        'views/pet_consultation_views.xml',
        'views/pet_pet_views.xml',
        'views/pet_species_views.xml',
        'views/hr_employee_views.xml',
        'views/res_partner_views.xml',

        # menus
        'data/veterinary_management_menus.xml',
        'views/hr_employee_views.xml',

],
    'installable': True,
    'application': True,
}
