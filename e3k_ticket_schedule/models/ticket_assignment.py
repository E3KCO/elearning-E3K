from odoo import fields, models, api, _
from datetime import datetime
import pytz

# from odoo.exceptions import ValidationError

CANADA_TIME_ZN = pytz.timezone('America/Montreal')
CANADA_CURRENT_TIME = datetime.now(CANADA_TIME_ZN).hour * 60 + datetime.now(CANADA_TIME_ZN).minute


def get_time_in_mins(time):
    hours = int('{0:02.0f}'.format(*divmod(time * 60, 60))) * 60
    mins = int('{1:02.0f}'.format(*divmod(time * 60, 60)))
    return hours + mins


class TicketAssignment(models.Model):
    _name = 'ticket.assignment'
    _description = 'Ticket Assigment'
    _rec_name = 'assign_ref'

    assign_ref = fields.Char(
        string='Reference Assignation', required=True, copy=False,
        readonly=True,
        index=True)
    ticket_assignment_ids = fields.One2many('ticket.assignment.line', 'ticket_assignment_id')


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

    """@api.constrains('start_date', 'end_date')
    def _check_date_monday(self):
        for line in self:
            if line.filtered(lambda item: item.day == 'Monday') and (line.start_date <= line.end_date and line.end_date >= line.start_date):
                raise ValidationError(_("L'assignation automatique que vous tentez de configurer est en conflit avec une autre assignation automatique existante pour la même période."))

            if line.filtered(lambda item: item.day == 'Tuesday') and (line.start_date <= line.end_date and line.end_date >= line.start_date):
                raise ValidationError(_("L'assignation automatique que vous tentez de configurer est en conflit avec une autre assignation automatique existante pour la même période."))"""


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
        day = datetime.now(CANADA_TIME_ZN).strftime('%A')
        if self.ticket_assign_id:
            for line in self.ticket_assign_id.mapped('ticket_assignment_ids'):
                start_time = get_time_in_mins(line.start_date)
                end_time = get_time_in_mins(line.end_date)
                if day == line.day and (start_time <= CANADA_CURRENT_TIME and end_time >= CANADA_CURRENT_TIME):
                    self.user_id = line.responsible_id
                else:
                    self.user_id = False

    @api.model
    def create(self, vals):
        res = super(HelpdeskTicket, self).create(vals)
        res.assign_user()
        return res
