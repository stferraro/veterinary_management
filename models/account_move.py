from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    pet_consultation_id = fields.Many2one(
        comodel_name='pet.consultation',
        string='Pet Consultation',
        help='Link to the pet consultation associated with this invoice'
    )

    pet_id = fields.Many2one(
        comodel_name='pet.pet',
        string='Pet',
        related='pet_consultation_id.pet_id',
        store=True,
        readonly=True,
        help='The pet associated with this invoice'
    )
