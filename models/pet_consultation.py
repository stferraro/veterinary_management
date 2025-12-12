from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class PetConsultation(models.Model):
    _name = 'pet.consultation'
    _description = 'The consultation types for pets (e.g., General Checkup, Vaccination, Surgery)'

    name = fields.Char(
        required=True,
        help='Name of the consultation type, e.g., General Checkup, Vaccination, Surgery'
    )

    reference = fields.Char(
        string='Reference',
        required=True,
        help='Unique reference code for the consultation'
    )

    pet_id = fields.Many2one(
        comodel_name='pet.pet',
        string='Pet',
        required=True,
        help='The pet for which the consultation is scheduled'
    )

    veterinarian_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Veterinarian',
        domain=[('is_veterinarian', '=', True)],
        required=True,
        help='The veterinarian conducting the consultation'
    )

    owner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Owner',
        related='pet_id.owner_id',
        store=True,
        readonly=True,
        help='The owner of the pet'
    )

    date = fields.Datetime(
        required=True,
        help='Date and time of the consultation'
    )

    duration = fields.Float(
        help='Duration of the consultation in hours'
    )

    state = fields.Selection(
        selection=[
            ('scheduled', 'Scheduled'),
            ('completed', 'Completed'),
            ('canceled', 'Canceled')
        ],
        default='scheduled',
        required=True,
        help='Status of the consultation'
    )

    notes = fields.Text(
        help='Additional notes or observations from the consultation'
    )

    active = fields.Boolean(
        default=True,
        help='Indicates whether the consultation record is active'
    )


    treatment_ids = fields.One2many(
        comodel_name='pet.treatment',
        inverse_name='consultation_id',
        string='Treatments',
        help='List of treatments administered during the consultation'
    )


    @api.constrains('date', 'veterinary_id')
    def _check_date(self):
        for rec in self:
            if rec.date and rec.date < fields.Datetime.now():
                raise ValidationError(_('The consultation date cannot be in the past.'))
            if rec.veterinarian_id and rec.duration:
                overlapping = self.search([
                    ('veterinarian_id', '=', rec.veterinarian_id.id),
                    ('id', '!=', rec.id),
                    ('state', '!=', 'canceled'),
                    ('date', '<', rec.date + timedelta(hours=rec.duration)),
                    ('date', '>=', rec.date)
                ])
                if overlapping:
                    raise ValidationError(_('The veterinarian already has a consultation scheduled at this time.'))

    @api.constrains('duration')
    def _check_duration(self):
        for rec in self:
            if rec.duration and rec.duration <= 0:
                raise ValidationError(_('The consultation duration must be greater than zero.'))

    @api.constrains('product_ids')
    def _check_products_active(self):
        for rec in self:
            inactive_products = rec.product_ids.filtered(lambda p: not p.active)
            if inactive_products:
                raise ValidationError(_('Some products in this consultation are inactive.'))

    _pet_date_unique = models.Constraint(
        'UNIQUE(pet_id, date)',
        'A pet cannot have two consultations at the same date and time.'
    )

    _duration_positive = models.Constraint(
        'CHECK(duration > 0)',
        'The duration must be greater than zero.'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'reference' not in vals or not vals['reference']:
                vals['reference'] = self.env['ir.sequence'].next_by_code('pet.consultation') or _('New') # type: ignore[attr-defined]
        records = super(PetConsultation, self).create(vals_list)
        return records







