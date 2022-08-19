from odoo import fields, models, api, _


class TicketAssignment(models.Model):
    _name = 'ticket.assignment'
    _description = 'Ticket Assigment'
    _rec_name = 'assign_ref'

    assign_ref = fields.Char(
        string='Reference Assignation', required=True, copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New'))
    ticket_assignment_ids = fields.One2many('ticket.assignment.line',
                                            'ticket_assignment_id')

    @api.model
    def create(self, vals):
        if vals.get('assign_ref', 'New') == 'New':
            vals['assign_ref'] = self.env['ir.sequence'].next_by_code('ticket.assignment') or 'New'
            return super(TicketAssignment, self).create(vals)


class TicketAssignmentLine(models.Model):
    _name = 'ticket.assignment.line'

    responsible_id = fields.Many2one(comodel_name='res.users',
                                     string="Responsable")
    day = fields.Selection([('Monday', 'Lundi'),
                            ('Tuesday', 'Mardi'),
                            ('Wednesday', 'Mercredi'),
                            ('Thursday', 'Jeudi'),
                            ('Friday', 'Vendredi')],
                           string="Jour")
    start_date = fields.Float(string='Heure Début')
    end_date = fields.Float(string='Heure de Fin')
    ticket_assignment_id = fields.Many2one('ticket.assignment')


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def _get_unique_ticket_assignment_value(self):
        ticket_assignment_obj = self.env['ticket.assignment'].search([], limit=1)
        for item in ticket_assignment_obj:
            return item.id

    ticket_assign_id = fields.Many2one(
        'ticket.assignment',
        string='Ref. Assignation',
        default=_get_unique_ticket_assignment_value
    )

    def assign_user(self):
        from datetime import datetime
        import pytz
        CANADA_TIME_ZN = pytz.timezone('America/Montreal')
        current_time = datetime.now(CANADA_TIME_ZN).hour*60 + datetime.now(CANADA_TIME_ZN).minute
        day = datetime.now(CANADA_TIME_ZN).strftime('%A')
        if not self.ticket_assign_id:
            self.ticket_assign_id = self._get_unique_ticket_assignment_value()

        if self.ticket_assign_id:
            for line in self.ticket_assign_id.mapped('ticket_assignment_ids'):
                start_time = int('{0:02.0f}'.format(*divmod(line.start_date * 60, 60)))*60 + int('{1:02.0f}'.format(*divmod(line.start_date * 60, 60)))
                end_time = int('{0:02.0f}'.format(*divmod(line.end_date * 60, 60)))*60 + int('{1:02.0f}'.format(*divmod(line.end_date * 60, 60)))
                if day == line.day and (start_time <= current_time and end_time >= end_time):
                    self.user_id = line.responsible_id
                else:
                    self.user_id = False
                return
