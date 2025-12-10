from odoo import models, fields


class PetSpecies(models.Model):
    _name = 'pet.species'
    _description = 'The species of animal (e.g., Dog, Cat, Bird)'

    name = fields.Char(
        required=True,
        help ='Name of the species, e.g., Dog, Cat, Bird'
    )

    description = fields.Char(
        help='Description of the species'
    )

    breeds_ids = fields.One2many(
        comodel_name='pet.breed',
        inverse_name='species_id',
        string='Breeds',
        help='The breeds associated with this species'
    )

    active = fields.Boolean(
        default=True,
        help='Indicates whether the species is active'
    )

    _unique_name = models.Constraint(
        'unique(name)',
        'The species name must be unique.'
    )


