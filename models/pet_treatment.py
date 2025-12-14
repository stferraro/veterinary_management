from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


# ==============================
# MODEL: PET TREATMENT
# ==============================
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

    tax_ids = fields.Many2many(
        'account.tax',
        'pet_treatment_tax_rel',
        'treatment_id',
        'tax_id',
        string='Taxes',
        help='Taxes applied to this treatment'
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

    # -------------------
    # COMPUTE SUBTOTAL
    # -------------------
    @api.depends('product_id', 'unit_price', 'quantity', 'tax_ids', 'currency_id')
    def _compute_subtotal(self):
        for rec in self:
            if not rec.product_id or not rec.unit_price or not rec.quantity:
                rec.subtotal = 0.0
                continue
            price = rec.unit_price or 0.0
            qty = rec.quantity or 0.0
            if rec.tax_ids:
                vals = rec.tax_ids.compute_all(
                    price_unit=price,
                    currency=rec.currency_id,
                    quantity=qty,
                    product=rec.product_id,
                    partner=None
                )
                rec.subtotal = vals.get('total_excluded', price * qty)
            else:
                rec.subtotal = price * qty

    # -------------------
    # CONSTRAINTS
    # -------------------
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

    # -------------------
    # HOOK CREATE: añadir impuestos por defecto del producto
    # -------------------
    @api.model
    def create(self, vals):
        if 'product_id' in vals and not vals.get('tax_ids'):
            product = self.env['product.product'].browse(vals['product_id'])
            if product.taxes_id:
                vals['tax_ids'] = [(6, 0, product.taxes_id.ids)]
        return super(PetTreatment, self).create(vals)


# ==============================
# MODEL: PET CONSULTATION
# ==============================
class PetConsultation(models.Model):
    _name = 'pet.consultation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Consultation for pets'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True
    )

    reference = fields.Char(
        string='Consultation Reference',
        readonly=True,
        default=lambda self: _('New'),
        required=True
    )

    pet_id = fields.Many2one(
        comodel_name='pet.pet',
        string='Pet',
        required=True
    )

    veterinarian_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Veterinarian',
        domain=[('is_veterinarian', '=', True)],
        required=True
    )

    owner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Owner',
        related='pet_id.owner_id',
        store=True,
        readonly=True
    )

    date = fields.Datetime(required=True)
    duration = fields.Float(help='Duration in hours')

    state = fields.Selection(
        [('scheduled', 'Scheduled'),
         ('completed', 'Completed'),
         ('canceled', 'Canceled')],
        default='scheduled',
        required=True
    )

    notes = fields.Text()
    active = fields.Boolean(default=True)

    treatment_ids = fields.One2many(
        'pet.treatment',
        'consultation_id',
        string='Treatments'
    )

    subtotal = fields.Monetary(compute='_compute_subtotal', store=True)
    tax_amount = fields.Monetary(compute='_compute_amounts', store=True)
    total = fields.Monetary(compute='_compute_amounts', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    invoice_id = fields.Many2one('account.move', string='Invoice')

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

    # -------------------
    # OVERRIDES
    # -------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'reference' not in vals or not vals['reference']:
                vals['reference'] = self.env['ir.sequence'].next_by_code('pet.consultation') or _('New')
        return super(PetConsultation, self).create(vals_list)

    # -------------------
    # STATE METHODS
    # -------------------
    def action_set_state(self, new_state):
        for rec in self:
            old_state = rec.state
            rec.state = new_state
            rec.message_post(
                body=f"State changed from {old_state} to {new_state}",
                subject="State Change"
            )

    def action_mark_completed(self):
        self.action_set_state('completed')

    def action_cancel(self):
        self.action_set_state('canceled')

    # -------------------
    # CREATE INVOICE
    # -------------------
    def action_create_invoice(self):
        self.ensure_one()
        if self.state != 'completed':
            raise ValidationError(_('Only completed consultations can be invoiced.'))

        invoice_lines = []
        for treatment in self.treatment_ids.filtered(lambda t: t.product_id):
            line_vals = {
                'name': f"Consultation: {self.reference}",
                'product_id': treatment.product_id.id,
                'quantity': treatment.quantity or 1.0,
                'price_unit': treatment.unit_price or 0.0,
                'tax_ids': [(6, 0, treatment.tax_ids.ids)] if treatment.tax_ids else [],
            }
            invoice_lines.append((0, 0, line_vals))

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.owner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'currency_id': self.currency_id.id,
            'invoice_origin': f"Consultation {self.reference}",
        }
        invoice = self.env['account.move'].create(invoice_vals)

        self.invoice_id = invoice.id
        self.message_post(
            body=f"Invoice {invoice.name} created for this consultation.",
            subject="Invoice Creation"
        )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }








