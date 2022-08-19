# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProjectProductDepartmentMap(models.Model):
    _name = 'project.sale.line.department.map'
    _description = 'Project Sales line, department mapping'

    @api.model
    def _default_project_id(self):
        if self._context.get('active_id'):
            return self._context['active_id']
        return False

    project_id = fields.Many2one('project.project', "Project", domain=[('allow_billable', '!=', False)], required=True,
                                 default=_default_project_id)
    department_id = fields.Many2one('hr.department', "Départment", required=True)
    sale_line_id = fields.Many2one('sale.order.line', "Ligne de bon de commande", domain=[('is_service', '=', True)],
                                   required=True)
    price_unit = fields.Float(related='sale_line_id.price_unit', readonly=True)

    _sql_constraints = [
        ('uniqueness_department', 'UNIQUE(project_id,department_id)',
         'A department cannot be selected more than once in the mapping. Please remove duplicate(s) and try again.'),
    ]
