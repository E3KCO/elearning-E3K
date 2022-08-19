# -*- coding: utf-8 -*-

from odoo import api, fields, models, api, _, exceptions
from lxml import etree
from odoo.exceptions import UserError, ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    is_billable = fields.Boolean(
        string='Billable',
        default=True
    )
    reported = fields.Boolean(
        string='Reported',
        default=False
    )
    not_editable_line = fields.Boolean(
        string='Not editable line',
        compute='_get_connected_employee_id'
    )
    not_billable_project = fields.Boolean(
        string='Not Billable Project',
        compute='_not_billable_project', store=True
    )
    amount_billable = fields.Monetary(
        string='Amount Billable',
        compute='get_amount_from_so',
        store=True, default=0.0
    )
    team_id = fields.Many2one(
        related='so_line.order_id.team_id',
        store=True
    )
    include = fields.Boolean(
        string='Include',
        default=True
    )
    is_timesheet_line = fields.Boolean(
        string="Transaction Type",
        store=True,
        compute_sudo=True,
        compute='_compute_is_timesheet_line',
        search='_search_is_timesheet_line',
        help="Set if this analytic line represents a line of timesheet."
    )

    @api.depends('project_id')
    def _compute_is_timesheet_line(self):
        for line in self:
            line.is_timesheet_line = bool(line.project_id)

    def _search_is_timesheet_line(self, operator, value):
        if (operator, value) in [('=', True), ('!=', False)]:
            return [
                ('project_id', '!=', False)
            ]

        return [
            ('project_id', '=', False)
        ]

    def get_all_childs_employes_ids(self, user_employee_id):
        employee_ids = [user_employee_id.id]

        for child_employee in user_employee_id.child_ids:
            employee_ids += self.get_all_childs_employes_ids(child_employee)
        return employee_ids

    @api.depends('is_billable', 'so_line', 'so_line.price_unit', 'unit_amount')
    def get_amount_from_so(self):
        for rec in self:
            if rec.is_billable:
                rec.amount_billable = rec.unit_amount * rec.so_line.price_unit
            else:
                rec.amount_billable = 0.0

    def unlink(self):
        for line in self:
            if line.timesheet_invoice_id:
                raise UserError(_('You cannot delete a billed line.'))
        return super(AccountAnalyticLine, self).unlink()

    @api.depends('project_id', 'project_id.allow_billable')
    def _not_billable_project(self):
        for line in self:
            if line.project_id.allow_billable:
                line.not_billable_project = False
            else:
                line.not_billable_project = True

    def _get_connected_employee_id(self):
        connected_user = self.env['res.users'].browse(self.env.uid)
        group_manager_connected_user = connected_user.has_group(
            'hr_timesheet.group_timesheet_manager'
        )
        for line in self:
            if line.user_id != connected_user and not group_manager_connected_user:
                line.not_editable_line = True
            else:
                line.not_editable_line = False

    @api.model
    def default_get(self, field_list):
        analytic_line = super(AccountAnalyticLine, self).default_get(field_list)
        if 'project_id' in analytic_line and analytic_line['project_id']:
            project = self.env['project.project'].browse(analytic_line['project_id'])
            analytic_line['is_billable'] = project.allow_billable
        return analytic_line

    @api.onchange('project_id')
    def _onchange_is_billable(self):
        if self.project_id.allow_billable:
            self.is_billable = True

    @api.model
    def create(self, values):
        result = super(AccountAnalyticLine, self).create(values)

        if result.project_id and not result.work_line_id:
            result['is_billable'] = result.project_id.allow_billable

        return result

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(AccountAnalyticLine, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                                  submenu=submenu)
        view_account_analytic_line_pivot_time_billing = self.env.ref(
            'e3k_psa.view_account_analytic_line_pivot_time_billing').id

        if view_type in ['pivot', 'graph'] and view_id == view_account_analytic_line_pivot_time_billing:
            doc = etree.XML(result['arch'])

            for node in doc.xpath("//field[@name='amount']"):
                node.set('invisible', '1')
            result['arch'] = etree.tostring(doc, encoding='unicode')

        return result

    @api.model
    def get_amount_billable(self):
        for rec in self.env['account.analytic.line'].search([('is_billable', '=', True)]):
            rec.amount_billable = rec.unit_amount * rec.so_line.price_unit

    @api.model
    def _timesheet_determine_sale_line(self):
        if self.project_id.pricing_type == 'employee_rate':
            map_entry = self.project_id.sale_line_employee_ids.filtered(
                lambda map_entry:
                map_entry.employee_id == self.employee_id
                and map_entry.sale_line_id.order_partner_id.commercial_partner_id == self.task_id.commercial_partner_id
            )
            map_dep_entry = self.env['project.sale.line.department.map'].search(
                [('project_id', '=', self.task_id.project_id.id), ('department_id', '=', self.employee_id.department_id.id)])
            if map_entry:
                return map_entry.sale_line_id
            elif map_dep_entry:
                return map_dep_entry.sale_line_id
        return super(AccountAnalyticLine, self)._timesheet_determine_sale_line()

    @api.constrains('so_line', 'project_id')
    def _check_sale_line_in_project_map(self):
        for timesheet in self:
            if timesheet.project_id and timesheet.so_line and timesheet.so_line not in timesheet.project_id.mapped('sale_line_employee_ids.sale_line_id') | timesheet.project_id.mapped('sale_line_department_ids.sale_line_id') | timesheet.task_id.sale_line_id | timesheet.project_id.sale_line_id:
                    raise ValidationError(_("This timesheet line cannot be billed: there is no Sale Order Item defined on the task, nor on the project. Please define one to save your timesheet line."))
