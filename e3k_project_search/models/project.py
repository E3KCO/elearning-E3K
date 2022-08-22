# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ProjectProject(models.Model):
  _name = 'project.project'
  _inherit = 'project.project'

  @api.depends('name', 'partner_id')
  def name_get(self):
    res = []
    for record in self:
      name = record.name
      if record.partner_id.name:
        name = record.partner_id.name + ' - ' + name
      res.append((record.id, name))
    return res

  @api.model
  def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    args = args or []
    recs = self.browse()
    if not recs:
      recs = self.search(['|', ('partner_id', operator, name), ('name', operator, name)] + args, limit=limit)
    return recs.name_get()

  def action_view_timesheet(self):
    self.ensure_one()
    if self.allow_timesheets:
      return self.action_view_timesheet_plan()

    return {
      'type': 'ir.actions.act_window',
      'name': _('Timesheets of %s') % self.name,
      'domain': [('project_id', '!=', False)],
      'res_model': 'account.analytic.line',
      'view_id': False,
      'view_mode': 'tree,form',
      'help': _("""
        <p class="o_view_nocontent_smiling_face">
          Record timesheets
        </p><p>
          You can register and track your workings hours by project every
          day. Every time spent on a project will become a cost and can be re-invoiced to
          customers if required.
        </p>
      """),
      'limit': 80,
      'context': {
        'default_project_id': self.id,
        'search_default_project_id': [self.id]
      }
    }

  def action_view_timesheet_plan(self):
    action = self.env.ref('sale_timesheet.project_timesheet_action_client_timesheet_plan').read()[0]
    action['params'] = {
      'project_ids': self.ids,
    }
    action['context'] = {
      'active_id': self.id,
      'active_ids': self.ids,
      'search_default_name': self.name,
      'search_default_partner_id': self.partner_id.id,
    }
    return action
