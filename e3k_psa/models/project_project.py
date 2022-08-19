# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression
from collections import defaultdict


class ProjectExpense(models.Model):
    _name = 'project.expense'
    _description = 'Project expense'

    expense_id = fields.Many2one(
        'project.project',
        name='Expense',
        required=True,
        ondelete='cascade',
        index=True,
        copy=False
    )
    product_id = fields.Many2one(
        'product.product',
        name='Product'
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='expense_id.partner_id',
        store=True
    )
    percent = fields.Float(
        name='Percent'
    )
    oldpercent = fields.Float(
        name='Percent'
    )


class Project(models.Model):
    _inherit = 'project.project'

    @api.depends('sale_line_id', 'sale_line_department_ids', 'sale_line_employee_ids', 'allow_billable')
    def _compute_pricing_type(self):
        billable_projects = self.filtered('allow_billable')
        for project in billable_projects:
            if project.sale_line_employee_ids or project.sale_line_department_ids:
                project.pricing_type = 'employee_rate'
            elif project.sale_line_id:
                project.pricing_type = 'fixed_rate'
            else:
                project.pricing_type = 'task_rate'
        (self - billable_projects).update({'pricing_type': False})

    def action_reset_percent(self):
        """ Write `percent` to zero on the selected records. """
        self.expense_ids.write({'percent': 0})

    def update_expense(self):
        """ Update `percent`. """
        obj = self.env['product.product']
        # Search product with boolean can_be_expensed
        products = obj.search([('can_be_expensed', '=', True)])
        # Check whether the existing expenditure lines
        project_product = self.expense_ids
        res = []
        expense_percent = 0.0
        for product in products:
            line = project_product.filtered(lambda l: l.product_id.id == product.id)
            expense_percent = (self.expense_percent - self.oldexpense_percent)
            if line:
                expense_percent = line.percent + expense_percent

            values = (0, 0, {
                'product_id': product.id,
                'percent': expense_percent,
            })
            res.append(values)

        self.expense_ids.unlink()
        self.update({'expense_ids': res, 'oldexpense_percent': expense_percent})

    non_billable_project = fields.Boolean(
        'Non Billable Project',
        default=False
    )
    expense_percent = fields.Float(
        name='Additional percentage expenses'
    )
    oldexpense_percent = fields.Float(
        name='old Additional percentage expenses'
    )
    expense_ids = fields.One2many(
        comodel_name="project.expense",
        inverse_name="expense_id",
        string="Expense",
        required=False
    )

    sale_line_department_ids = fields.One2many('project.sale.line.department.map', 'project_id',
                                               "Sale line/Department map",
                                               copy=False)

    # TO DO : TO REVIEW THIS FUNCTION
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            project_ids = []
            if operator in positive_operators:
                partners = self.env['res.partner']._search([('name', 'ilike', name)], access_rights_uid=name_get_uid)
                project_ids = list(
                    self._search([('partner_id.id', 'in', partners)] + args, limit=limit, access_rights_uid=name_get_uid))
            if not project_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                if not limit or len(project_ids) < limit:
                    limit2 = (limit - len(project_ids)) if limit else False
                    project2_ids = self._search(args + [('name', operator, name), ('id', 'not in', project_ids)],
                                                limit=limit2, access_rights_uid=name_get_uid)
                    project_ids.extend(project2_ids)
            elif not project_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    [('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                project_ids = list(self._search(domain, limit=limit, access_rights_uid=name_get_uid))

        else:
            project_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return project_ids

    @api.depends('analytic_account_id', 'timesheet_ids')
    def _compute_billable_percentage(self):
        timesheets_read_group = self.env['account.analytic.line'].read_group([('project_id', 'in', self.ids)],
                                                                             ['project_id', 'so_line', 'unit_amount', 'is_billable'],
                                                                             ['project_id', 'so_line', 'is_billable'], lazy=False)
        timesheets_by_project = defaultdict(list)
        for res in timesheets_read_group:
            timesheets_by_project[res['project_id'][0]].append((res['unit_amount'], bool(res['so_line']), res['is_billable']))
        for project in self:
            timesheet_total = timesheet_billable = 0.0
            for unit_amount, is_billable_timesheet, is_billable in timesheets_by_project[project.id]:
                timesheet_total += unit_amount
                if is_billable and is_billable_timesheet:
                    timesheet_billable += unit_amount
            billable_percentage = timesheet_billable / timesheet_total * 100 if timesheet_total > 0 else 0
            project.billable_percentage = round(billable_percentage)
