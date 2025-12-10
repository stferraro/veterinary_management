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
        'stock',
        'account',
        'hr',
        'product',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Views
        'views/pet_pet_views.xml',
        'views/pet_species_views.xml',
        'views/hr_employee_views.xml',

        # menus
        'data/veterinary_management_menus.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': True,
}
