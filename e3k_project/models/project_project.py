# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from dateutil.relativedelta import relativedelta
from odoo import SUPERUSER_ID
import nltk
from nltk.corpus import stopwords
from spacy.lang.fr.stop_words import STOP_WORDS as fr_stop
import logging

_logger = logging.getLogger(__name__)
import unicodedata


class Task(models.Model):
    _inherit = 'project.task'

    # x_priority_field = fields.Selection([
    #   ('1', '1'),
    #   ('2', '2'),
    #   ('3', '3'),
    #   ('4', '4'),
    #   ('5', '5'),
    #   ('6', '6'),
    #   ('7', '7'),], string='Priority', default='4', tracking=True
    # )
    branch_name = fields.Char('Branch name', help="Branch name generated automatically from task name",
                              compute="_compute_branch_name")

    def strip_accents(self, s):
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                       if unicodedata.category(c) != 'Mn')

    def _compute_branch_name(self):
        for rec in self:
            stopwords = list(fr_stop)
            name = rec.name.lower()  # lowecase
            name = name.split()
            tab = []
            for char in name[0:7]:
                if char in stopwords: # remove stop words
                    continue
                res = ''.join(filter(str.isalnum, char))  # remove spacial caracters
                tab.append(res)
            name = '_'.join(tab)
            name = self.strip_accents(name)  # remove accents
            rec.branch_name = str(rec.id) + '_' + name

    #
    # def _create_message(self, task, name, users):
    #   Obj = self.env['mail.mail']
    #   for user in users:
    #     Obj.sudo().create({
    #       'email_from': self.env.company.email,
    #       'author_id': self.env.company.partner_id.id,
    #       'body_html': '%s: %s [%s]' % (task.name ,task.project_id.name, task.x_priority_field),
    #       'subject': '[%s]: %s' % (task.id, name),
    #       'email_to': self.env.user.email_formatted,
    #       'auto_delete': True,
    #     }).send()

    # def _x_priority_field(self, x_priority_field):
    #     if x_priority_field != '4':
    #         for task in self._origin:
    #             responsible_id = task.user_id
    #             manager_id = task.project_id.user_id
    #             users = [responsible_id]

    #             if manager_id and manager_id != responsible_id:
    #                 users = [responsible_id, manager_id]
    #             self._create_message(task, _('Property has been changed'), users)

    #
    #
    # def write(self, values):
    #   res = super().write(values)
    #   # if values.get('x_priority_field', False):
    #   #    self._x_priority_field(values.get('x_priority_field'))
#   #   return res
#
#
# class Project(models.Model):
#   _inherit = 'project.project'
#
#   activate_notification = fields.Boolean(string='Activate notifications', default=False)
#
#   first_reminder = fields.Integer(string='First Reminder Days', default=1)
#   second_reminder = fields.Integer(string='Second Reminder  Days', default=3)
#   send_to_responsible = fields.Boolean(string='Send To Responsible', default=True)
#   send_to_manager = fields.Boolean(string='Send To Manager', default=True)
#   stage_ids = fields.Many2many('project.task.type', string='Stages of the notification', domain="[('project_ids', '=', id)]")
#
#   def create_notification(self, task, name, users):
#     activity = self.env.ref('mail.mail_activity_data_todo')
#     Obj = self.env['mail.activity']
#
#     for user in users:
#       if not user:
#         continue
#       vals = {
#         'note': task.name,
#         'res_name': task.name,
#         'activity_type_id': activity.id,
#         'summary': name,
#         'date_deadline': fields.Date.today() + relativedelta(days=1),
#         'res_model': 'project.task',
#         'res_model_id': self.env['ir.model'].search([('model', '=', 'project.task')], limit=1).id,
#         'res_id': task.id,
#         'user_id': user.id
#       }
#       Obj.with_user(SUPERUSER_ID).create(vals)
#
#   def cron_method_to_notification_task(self):
#     users = []
#     Obj = self.env['project.project']
#     Date = fields.Date.today()
#     Projects = Obj.search([('activate_notification', '=', True)])
#     for project in Projects:
#       manager_id = project.user_id
#       first_reminder = project.first_reminder
#       second_reminder = project.second_reminder
#       Tasks = project.mapped('task_ids').filtered(
#         lambda l: l.stage_id.id in project.stage_ids.ids and l.date_deadline
#                 and (l.date_deadline + relativedelta(days=second_reminder) < Date
#                 or l.date_deadline + relativedelta(days=first_reminder) < Date)
#       )
#       for task in Tasks:
#         users = []
#         responsible_id = task.user_id
#         if project.send_to_responsible:
#           users = [responsible_id]
#         if project.send_to_manager and manager_id and manager_id != responsible_id:
#           users.append(manager_id)
#         if task.date_deadline + relativedelta(days=second_reminder) < Date:
#           self.create_notification(task, _('Second Reminder'), users)
#         else:
#           self.create_notification(task, _('First Reminder'), users)
