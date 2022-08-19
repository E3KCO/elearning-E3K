# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.constrains('task_id', 'helpdesk_ticket_id')
    def _check_no_link_task_and_ticket(self):
        # Check if any timesheets are not linked to a ticket and a task at the same time
        if any(timesheet.task_id and timesheet.helpdesk_ticket_id for timesheet in self):
            return True

    @api.model
    def default_get(self, fields):
        res = super(AccountAnalyticLine, self).default_get(fields)
        param = self._context.get('params', False)
        if param and param.get('model'):
            if param.get('model') == 'helpdesk.ticket':
                res['name'] = self.ticket_name(param.get('id'))
        else:
            ticket_id = self._context.get('ticket_id', False)
            if ticket_id:
                res['name'] = "%s:" % (ticket_id['display_name'])
        return res

    def ticket_name(self, ticket_id):
        ticket = self.env['helpdesk.ticket'].browse(ticket_id)
        name = "%s (#%d):" % (ticket.name, ticket_id)
        return name
