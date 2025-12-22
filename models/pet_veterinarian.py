from odoo import models, fields, api


class PetVeterinarian(models.Model):
    _inherit = 'hr.employee'
    _description = 'Veterinarian Information'

    is_veterinarian = fields.Boolean(
        string='Is Veterinarian',
        default=True,
        help='Indicates whether the employee is a veterinarian'
    )

