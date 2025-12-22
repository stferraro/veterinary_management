from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class PetConsultation(models.Model):
    _name = 'pet.consultation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'The consultation types for pets'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Name of the consultation'
    )

    consultation_ref = fields.Char(
        readonly=True,
        copy=False,
        default=lambda self: _('New'),
        required=True,
        string='Consultation',
        states={'scheduled': [('readonly', False)]}
    )

    pet_id = fields.Many2one(
        comodel_name='pet.pet',
        string='Pet',
        required=True,
        tracking=True
    )

    veterinarian_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Veterinarian',
        domain=[('is_veterinarian', '=', True)],
        required=True,
        tracking=True
    )

    owner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Owner',
        related='pet_id.owner_id',
        store=True,
        readonly=True
    )

    date = fields.Datetime(required=True, tracking=True)
    duration = fields.Float(help='Duration in hours')

    state = fields.Selection(
        selection=[
            ('scheduled', 'Scheduled'),
            ('completed', 'Completed'),
            ('canceled', 'Canceled')
        ],
        default='scheduled',
        tracking=True
    )

    notes = fields.Text()
    active = fields.Boolean(default=True)

    treatment_ids = fields.One2many(
        comodel_name='pet.treatment',
        inverse_name='consultation_id',
        string='Treatments'
    )

    subtotal = fields.Monetary(
        compute='_compute_subtotal',
        store=True
    )

    tax_amount = fields.Monetary(
        compute='_compute_amounts',
        store=True
    )

    total = fields.Monetary(
        compute='_compute_amounts',
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice'
    )

    # -------------------
    # CONSTRAINTS
    # -------------------

    @api.constrains('date', 'state')
    def _check_date(self):
        for rec in self:
            if rec.state == 'scheduled' and rec.date and rec.date < fields.Datetime.now():
                raise ValidationError(
                    _('Scheduled consultations cannot have a past date.')
                )

    @api.constrains('duration')
    def _check_duration(self):
        for rec in self:
            if rec.duration is not None and rec.duration <= 0:
                raise ValidationError(
                    _('Consultation duration must be greater than zero.')
                )

    @api.constrains('state', 'treatment_ids')
    def _check_completed_has_treatments(self):
        for rec in self:
            if rec.state == 'completed' and not rec.treatment_ids:
                raise ValidationError(
                    _('You cannot complete a consultation without treatments.')
                )

    @api.constrains('state', 'veterinarian_id')
    def _check_veterinarian_required(self):
        for rec in self:
            if rec.state == 'completed' and not rec.veterinarian_id:
                raise ValidationError(
                    _('A veterinarian is required to complete the consultation.')
                )

    # -------------------
    # OVERRIDES
    # -------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'consultation_ref' not in vals or not vals['consultation_ref']:
                vals['consultation_ref'] = self.env['ir.sequence'].next_by_code('pet.consultation') or _('New')
        return super(PetConsultation, self).create(vals_list)

    # -------------------
    # COMPUTE METHODS
    # -------------------
    @api.depends('consultation_ref', 'pet_id')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.consultation_ref} - {rec.pet_id.name}" if rec.pet_id else rec.consultation_ref

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
    # STATE ACTIONS
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

        if self.state == 'canceled':
            raise ValidationError(
                _('Cannot invoice a canceled consultation.')
            )

        if self.invoice_id:
            raise ValidationError(
                _('This consultation has already been invoiced.')
            )

        if not self.owner_id:
            raise ValidationError(
                _('The pet must have an owner to create an invoice.')
            )
        treatments = self.treatment_ids.filtered(lambda t: t.product_id)
        if not treatments:
            raise ValidationError(
                _('You must add at least one treatment with a product to invoice.')
            )
        invoice_lines = []
        for treatment in treatments:
            invoice_lines.append((0, 0, {
                'name': f"{treatment.product_id.name} (Consultation: {self.consultation_ref})",
                'product_id': treatment.product_id.id,
                'quantity': treatment.quantity or 1.0,
                'price_unit': treatment.unit_price or 0.0,
                'tax_ids': [(6, 0, treatment.tax_ids.ids)],
            }))

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.owner_id.id,
            'pet_consultation_id': self.id,
            'pet_id': self.pet_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'currency_id': self.currency_id.id,
            'invoice_origin': f"Consultation {self.consultation_ref}",
        }

        invoice = self.env['account.move'].create(invoice_vals)

        self.invoice_id = invoice.id

        if self.state == 'scheduled':
            self.state = 'completed'

        self.message_post(
            body=_('Invoice <b>%s</b> created successfully.') % invoice.name,
            subject=_('Invoice Created')
        )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def unlink(self):
        for rec in self:
            if rec.invoice_id:
                raise ValidationError(
                    _('You cannot delete a consultation that has an invoice.')
                )
        return super(PetConsultation, self).unlink()

