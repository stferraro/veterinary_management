from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PetTreatment(models.Model):
    _name = 'pet.treatment'
    _description = 'The treatment or procedure for pets'

    name = fields.Char(
        required=True,
        help='Name of the treatment or procedure, e.g., Vaccination, Surgery, Deworming'
    )

    consultation_id = fields.Many2one(
        comodel_name='pet.consultation',
        string='Consultation',
        required=True,
        ondelete='cascade',
        help='Consultation this treatment belongs to'
    )

    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        domain=[('type', 'in', ['veterinarian_service', 'veterinarian_medicament'])],
        help='Product used in this treatment'
    )

    start_date = fields.Datetime(
        required=True,
        help='Start date and time of the treatment'
    )

    end_date = fields.Datetime(
        help='End date and time of the treatment'
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        string='Currency'
    )

    quantity = fields.Float(
        default=1.0,
        help='Quantity of the product used in this treatment'
    )

    unit_price = fields.Float(
        string='Unit Price',
        related='product_id.list_price',
        help='Unit price of the product used in this treatment'
    )

    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True
    )

    @api.depends('product_id')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.unit_price * rec.quantity if rec.product_id else 0.0

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






