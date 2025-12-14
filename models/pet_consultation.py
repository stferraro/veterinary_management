from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class PetConsultation(models.Model):
    _name = 'pet.consultation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'The consultation types for pets (e.g., General Checkup, Vaccination, Surgery)'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Name of the consultation, typically the reference and pet name'
    )

    reference = fields.Char(
        string='Consultation',
        readonly=True,
        default=lambda self: _('New'),
        required=True,
        help='Unique reference code for the consultation'
    )

    pet_id = fields.Many2one(
        comodel_name='pet.pet',
        string='Pet',
        required=True,
        help='The pet for which the consultation is scheduled',
        tracking=True
    )

    veterinarian_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Veterinarian',
        domain=[('is_veterinarian', '=', True)],
        required=True,
        help='The veterinarian conducting the consultation',
        tracking=True
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
        help='Date and time of the consultation',
        tracking=True
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
        help='Status of the consultation',
        tracking=True
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

    subtotal = fields.Monetary(
        compute='_compute_subtotal',
        store=True,
        help='Subtotal cost of the consultation before tax',
        tracking=True
    )

    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string='Taxes',
        help='Taxes applied to the consultation'
    )

    tax_amount = fields.Monetary(
        string='Tax Amount',
        compute='_compute_amounts',
        store=True,
        help='Total tax amount applied to the consultation',
        tracking=True
    )

    total = fields.Monetary(
        string='Total Cost',
        compute='_compute_amounts',
        store=True,
        help='Total cost of the consultation including all treatments',
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        string='Currency'
    )

    # -------------------
    # CONSTRAINTS
    # -------------------
    @api.constrains('date', 'veterinarian_id')
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

    # -------------------
    # COMPUTE METHODS
    # -------------------
    @api.depends('reference', 'pet_id')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.reference} - {rec.pet_id.name}" if rec.pet_id else rec.reference

    @api.depends('treatment_ids.subtotal')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = sum(rec.treatment_ids.mapped('subtotal'))

    @api.depends('treatment_ids.subtotal', 'treatment_ids.tax_ids')
    def _compute_amounts(self):
        for rec in self:
            subtotal = sum(rec.treatment_ids.mapped('subtotal'))
            tax_amount = 0.0
            for line in rec.treatment_ids:
                if line.tax_ids:
                    vals = line.tax_ids.compute_all(
                        price_unit=line.subtotal,
                        currency=rec.currency_id,
                        quantity=1,
                        product=None,
                        partner=None
                    )
                    tax_amount += sum(t['amount'] for t in vals.get('taxes', []))
            rec.subtotal = subtotal
            rec.tax_amount = tax_amount
            rec.total = subtotal + tax_amount

    # -------------------
    # OVERRIDES
    # -------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'reference' not in vals or not vals['reference']:
                vals['reference'] = self.env['ir.sequence'].next_by_code('pet.consultation') or _('New')
        records = super(PetConsultation, self).create(vals_list)
        return records

    # -------------------
    # STATE CHANGE HELPER
    # -------------------
    def action_set_state(self, new_state):
        for rec in self:
            old_state = rec.state
            rec.state = new_state
            rec.message_post(
                body=f"State changed from {old_state} to {new_state}",
                subject="State Change"
            )

    # -------------------
    # STATE CHANGE ACTIONS
    # -------------------

    def action_mark_completed(self):
        self.action_set_state('completed')

    def action_cancel(self):
        self.action_set_state('canceled')

    def action_create_invoice(self):
        for rec in self:
            for treatment in rec.treatment_ids:
                if treatment.product_id and treatment.quantity > 0:
                    move_vals = {
                        'product_id': treatment.product_id.id,
                        'product_uom_qty': treatment.quantity,
                        'product_uom': treatment.product_id.uom_id.id,
                        'location_id': self.env.ref('stock.stock_location_stock').id,
                        'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                        'name': f'Treatment for {rec.pet_id.name} - {treatment.product_id.name}',
                    }
                    self.env['stock.move'].create(move_vals).action_confirm().action_done()
        rec.message_post(body="Stock moves created for treatments.", subject="Stock Move Creation")








