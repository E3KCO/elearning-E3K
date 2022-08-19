# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model
    def _get_default_note(self):
        result = """
        <div>
            <h6>Description du probleme:</h6><br/><br/><br/><br/>
            <h6>Resolution:</h6>
        </div>"""
        return result

    task_id = fields.Many2one("project.task", string="Task",
                              domain="[('project_id', '=', project_id), ('company_id', '=', company_id)]",
                              tracking=True,
                              help="The task must have the same customer as this ticket.")
    description = fields.Html(default=_get_default_note)

    @api.onchange('sale_order_id')
    def onchange_sale_order_id(self):
        Obj = self.env['project.project']

        if self.sale_order_id:
            project_id = Obj.sudo().search(
                [('sale_order_id', '=', self.sale_order_id.id)], order='id asc',
                limit=1)
            if project_id:
                self.project_id = project_id.id
            if self.project_id:
                self.sale_line_id = self.project_id.sale_line_id.id
