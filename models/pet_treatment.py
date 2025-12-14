from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PetTreatment(models.Model):
    _name = 'pet.treatment'
    _description = 'The treatment or procedure for pets'

    consultation_id = fields.Many2one(
        comodel_name='pet.consultation',
        string='Consultation',
        required=True,
        ondelete='cascade',
        help='Consultation this treatment belongs to'
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
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

    tax_ids = fields.Many2one(
        comodel_name='account.tax',
        string='Tax',
        help='Tax applied to this treatment'
    )

    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True
    )

    sequence = fields.Integer(
        default=1,
        help='Sequence for ordering treatments within a consultation'
    )

    @api.depends('product_id', 'unit_price', 'quantity', 'tax_ids', 'currency_id')
    def _compute_subtotal(self):
        for rec in self:
            if not rec.product_id or not rec.unit_price or not rec.quantity:
                rec.subtotal = 0.0
                continue
            price = rec.unit_price or 0.0
            qty = rec.quantity or 0.0
            if rec.tax_ids:
                vals = rec.tax_ids.compute_all(price_unit=price, currency=rec.currency_id, quantity=qty,
                                           product=rec.product_id, partner=None)
                rec.subtotal = vals.get('total_excluded', price * qty)
            else:
                rec.subtotal = price * qty

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






