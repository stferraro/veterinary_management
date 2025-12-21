from odoo import models, fields


class PetBreed(models.Model):
    _name = 'pet.breed'
    _description = 'The breed of the animal (e.g., Labrador, Siamese)'

    name = fields.Char(
        required=True,
        help ='Name of the breed, e.g., Labrador, Siamese'
    )

    sequence = fields.Integer(
        default=10,
        help='Sequence for ordering breeds'
    )

    description = fields.Char(
        help='Description of the breed'
    )

    species_id = fields.Many2one(
        comodel_name='pet.species',
        string='Species',
        required=True,
        help='The species to which this breed belongs'
    )

    _unique_name = models.Constraint(
        'unique(name)',
        'The species name must be unique.'
    )



