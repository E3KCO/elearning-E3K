# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_timesheet_user = fields.Boolean('Timesheet User', compute='_compute_is_timesheet_user')

    def _compute_is_timesheet_user(self):
        self.is_timesheet_user = self.user_id.has_group('hr_timesheet.group_hr_timesheet_user')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if self._context.get('connected_user'):
            args = [('user_id', '=', self.env.uid)]
        return super(HrEmployee, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)
