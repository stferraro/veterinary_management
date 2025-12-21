from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pets_ids = fields.One2many(
        comodel_name='pet.pet',
        inverse_name='owner_id',
        string='Pets',
    )

    pets_count = fields.Integer(
        string='Number of Pets',
        compute='_compute_pets_count',
    )

    @api.depends('pets_ids')
    def _compute_pets_count(self):
        for rec in self:
            rec.pets_count = len(rec.pets_ids)

    def action_view_pets(self):
        self.ensure_one()
        return {
            'name': 'Pets',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,list,form',
            'res_model': 'pet.pet',
            'domain': [('owner_id', '=', self.id)],
            'context': {'default_owner_id': self.id},
        }

