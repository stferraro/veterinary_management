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

    reference = fields.Char(
        string='Consultation',
        readonly=True,
        default=lambda self: _('New'),
        required=True
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
            raise ValidationError(_('Cannot invoice a canceled consultation.'))

        invoice_lines = []
        for treatment in self.treatment_ids.filtered(lambda t: t.product_id):
            line_vals = {
                'name': f"Consultation: {self.reference}",
                'product_id': treatment.product_id.product_variant_id.id,
                'quantity': treatment.quantity or 1.0,
                'price_unit': treatment.unit_price or 0.0,
                'tax_ids': [(6, 0, treatment.tax_ids.ids)] if treatment.tax_ids else [],
            }
            invoice_lines.append((0, 0, line_vals))

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.owner_id.id,
            'pet_consultation_id': self.id,
            'pet_id': self.pet_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'currency_id': self.currency_id.id,
            'invoice_origin': f"Consultation {self.reference}",
        }
        invoice = self.env['account.move'].create(invoice_vals)

        self.invoice_id = invoice.id
        if self.state == 'scheduled':
            self.state = 'completed'
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
