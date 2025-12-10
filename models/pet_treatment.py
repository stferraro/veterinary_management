from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PetTreatment(models.Model):
    _name = 'pet.treatment'
    _description = 'The treatment or procedure for pets'

    name = fields.Char(
        required=True,
        help='Name of the treatment or procedure, e.g., Vaccination, Surgery, Deworming'
    )

    pet_id = fields.Many2one(
        comodel_name='pet.pet',
        string='Pet',
        required=True,
        help='The pet receiving the treatment'
    )

    consultation_id = fields.Many2one(
        comodel_name='pet.consultation',
        string='Consultation',
        required=True,
        help='The consultation during which the treatment was administered'
    )

    products_ids = fields.Many2many(
        comodel_name='product.product',
        string='Products/Medications',
        help='Products or medications used during the treatment'
    )

    veterinary_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Veterinarian',
        domain=[('is_veterinarian', '=', True)],
        required=True,
        help='The veterinarian administering the treatment'
    )

    start_date = fields.Datetime(
        required=True,
        help='Start date and time of the treatment'
    )

    end_date = fields.Datetime(
        help='End date and time of the treatment'
    )

    notes = fields.Text(
        help='Additional notes or observations about the treatment'
    )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date <= rec.start_date:
                raise ValidationError(_('The end date must be after the start date.'))

    @api.constrains('start_date')
    def _check_start_date(self):
        for rec in self:
            if rec.start_date and rec.start_date < fields.Datetime.now():
                raise ValidationError(_('The start date cannot be in the past.'))




