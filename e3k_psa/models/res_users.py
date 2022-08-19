# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    employee_id = fields.Many2one(
        'hr.employee',
        compute='_compute_employee'
    )

    def _compute_employee(self):
        """Checks employee relaed to user
        """
        empl = self.env['hr.employee']
        for res in self:
            empl_id = empl.search( [('user_id', '=', res.id)], limit=1)
            res.employee_id = empl_id and empl_id.id
