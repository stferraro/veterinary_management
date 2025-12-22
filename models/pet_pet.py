from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PetPet(models.Model):
    _name = 'pet.pet'
    _description = 'Information about the pet animal'

    name = fields.Char(
        required=True,
        help='Name of the pet animal'
    )

    image = fields.Binary(
        help='Image of the pet animal'
    )

    species_id = fields.Many2one(
        comodel_name='pet.species',
        string='Species',
        help='The species of the pet animal'
    )

    breed_id = fields.Many2one(
        comodel_name='pet.breed',
        string='Breed',
        help='The breed of the pet animal'
    )

    gender = fields.Selection(
        selection=[
            ('male', 'Male'),
            ('female', 'Female')
        ],
        required=True,
        help='Gender of the pet animal'
    )

    birth_date = fields.Date(
        help='Birth date of the pet animal'
    )

    age = fields.Integer(
        compute='_compute_age',
        store=True,
        depends=['birth_date'],
        help='Age of the pet animal in years'
    )

    owner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Owner',
        required=True,
        help='The owner of the pet animal'
    )

    weight = fields.Float(
        help='Weight of the pet animal in kilograms'
    )

    color = fields.Char(
        help='Color of the pet animal'
    )

    veterinarian_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Veterinarian',
        domain=[('is_veterinarian', '=', True)],
        help='The veterinarian assigned to the pet animal'
    )

    consultations_ids = fields.One2many(
        comodel_name='pet.consultation',
        inverse_name='pet_id',
        string='Consultations',
        help='Consultations related to the pet animal'
    )

    consultations_count = fields.Integer(
        string='Number of Consultations',
        compute='_compute_consultations_count',
        help='Total number of consultations for the pet animal'
    )

    def _compute_age(self):
        for rec in self:
            if rec.birth_date:
                today = fields.Date.today()
                rec.age = today.year - rec.birth_date.year - (
                    (today.month, today.day) < (rec.birth_date.month, rec.birth_date.day)
                )
            else:
                rec.age = 0

    @api.constrains('birth_date')
    def _check_birth_date(self):
        for rec in self:
            if rec.birth_date and rec.birth_date > fields.Date.today():
                raise ValidationError(_('The birth date cannot be in the future.'))

    def _compute_consultations_count(self):
        for rec in self:
            rec.consultations_count = len(rec.consultations_ids)
