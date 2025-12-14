from odoo import fields, models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    type = fields.Selection(
        selection_add=[
            ('veterinarian_service', 'Veterinarian Service'),
            ('veterinarian_medicament', 'Veterinarian Medicament'),
        ],
        ondelete={
            'veterinarian_service': 'set default',
            'veterinarian_medicament': 'set default',
        },
        help='Type of the product, including veterinary-specific types.'
    )
