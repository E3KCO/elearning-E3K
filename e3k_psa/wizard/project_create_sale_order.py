# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectCreateSalesOrder(models.TransientModel):
    _inherit = 'project.create.sale.order'

    tarification_id = fields.Many2one('project.tarification', "Tariffication")
    line_dep_ids = fields.One2many('project.create.sale.order.dep.line', 'wizard_id', string='Department Lines')
    pricing_type = fields.Selection(related="project_id.pricing_type")

    @api.onchange('tarification_id')
    def _onchange_tarification_id(self):
        if self.tarification_id:
            for tarification in self.tarification_id.tarification_ids:
                project_sale_order_line = [(0, 0, {'employee_id': tarification.employee_id.id,
                                                   'product_id': tarification.product_id.id,
                                                   'price_unit': tarification.price_unit,
                                                   'currency_id': tarification.currency_id.id,
                                                   })]
                self.line_ids = project_sale_order_line
            for dep_tarif in self.tarification_id.department_tarification_ids:
                project_sale_order_dep_line = [(0, 0, {'department_id': dep_tarif.department_id.id,
                                                       'product_id': dep_tarif.product_id.id,
                                                       'price_unit': dep_tarif.price_unit,
                                                       'currency_id': dep_tarif.currency_id.id,
                                                       })]
                self.line_dep_ids = project_sale_order_dep_line

    def _make_billable(self, sale_order):
        if not self.line_dep_ids:  # Then we configure the project with pricing type is equal to project rate
            self._make_billable_at_project_rate(sale_order)
        else:  # Then we configure the project with pricing type is equal to employee rate
            self._make_billable_at_employee_rate(sale_order)

    def _make_billable_at_employee_rate(self, sale_order):
        # trying to simulate the SO line created a task, according to the product configuration
        # To avoid, generating a task when confirming the SO
        task_id = self.env['project.task'].search([('project_id', '=', self.project_id.id)], order='create_date DESC',
                                                  limit=1).id
        project_id = self.project_id.id

        non_billable_tasks = self.project_id.tasks.filtered(lambda task: task.allow_billable == False)

        map_entries = self.env['project.sale.line.employee.map']
        map_dep_entries = self.env['project.sale.line.department.map']
        EmployeeMap = self.env['project.sale.line.employee.map'].sudo()
        DepartmentMap = self.env['project.sale.line.department.map'].sudo()

        # create SO lines: create on SOL per product/price. So many employee can be linked to the same SOL
        map_product_price_sol = {}  # (product_id, price) --> SOL
        for wizard_line in self.line_ids:
            map_key = (wizard_line.product_id.id, wizard_line.price_unit)
            if map_key not in map_product_price_sol:
                values = {
                    'order_id': sale_order.id,
                    'product_id': wizard_line.product_id.id,
                    'price_unit': wizard_line.price_unit,
                    'product_uom_qty': 0.0,
                }
                if wizard_line.product_id.service_tracking in ['task_in_project', 'task_global_project']:
                    values['task_id'] = task_id
                if wizard_line.product_id.service_tracking in ['task_in_project', 'project_only']:
                    values['project_id'] = project_id

                sale_order_line = self.env['sale.order.line'].create(values)
                map_product_price_sol[map_key] = sale_order_line

            map_entries |= EmployeeMap.create({
                'project_id': self.project_id.id,
                'sale_line_id': map_product_price_sol[map_key].id,
                'employee_id': wizard_line.employee_id.id,
            })

            # custom code: add department code
        for wizard_line in self.line_dep_ids:
            map_key = (wizard_line.product_id.id, wizard_line.price_unit)
            if map_key not in map_product_price_sol:
                values = {
                    'order_id': sale_order.id,
                    'product_id': wizard_line.product_id.id,
                    'price_unit': wizard_line.price_unit,
                    'product_uom_qty': 0.0,
                }
                if wizard_line.product_id.service_tracking in ['task_in_project', 'task_global_project']:
                    values['task_id'] = task_id
                if wizard_line.product_id.service_tracking in ['task_in_project', 'project_only']:
                    values['project_id'] = project_id

                sale_order_line = self.env['sale.order.line'].create(values)
                map_product_price_sol[map_key] = sale_order_line

            map_dep_entries |= DepartmentMap.create({
                'project_id': self.project_id.id,
                'sale_line_id': map_product_price_sol[map_key].id,
                'department_id': wizard_line.department_id.id,
            })
        # link the project to the SO
        self.project_id.write({
            'sale_order_id': sale_order.id,
            'sale_line_id': sale_order.order_line[0].id,
            'partner_id': self.partner_id.id,
        })
        non_billable_tasks.write({
            'sale_line_id': sale_order.order_line[0].id,
            'partner_id': sale_order.partner_id.id,
            'email_from': sale_order.partner_id.email,
        })

        # assign SOL to timesheets
        for map_entry in map_entries:
            self.env['account.analytic.line'].search(
                [('task_id', 'in', self.project_id.tasks.ids), ('employee_id', '=', map_entry.employee_id.id),
                 ('so_line', '=', False)]).write({'so_line': map_entry.sale_line_id.id})

    def action_create_sale_order(self):
        # if project linked to SO line or at least on tasks with SO line, then we consider project as billable.
        if self.project_id.sale_line_id:
            raise UserError(_("The project is already linked to a sales order item."))
        # at least one line
        if not self.line_ids and not self.line_dep_ids:
            raise UserError(_("At least one line should be filled."))

        if self.line_ids.employee_id:
            # all employee having timesheet should be in the wizard map
            timesheet_employees = self.env['account.analytic.line'].search([('task_id', 'in', self.project_id.tasks.ids)]).mapped('employee_id')
            map_employees = self.line_ids.mapped('employee_id')
            missing_meployees = timesheet_employees - map_employees
            if missing_meployees:
                raise UserError(_('The Sales Order cannot be created because you did not enter some employees that entered timesheets on this project. Please list all the relevant employees before creating the Sales Order.\nMissing employee(s): %s') % (', '.join(missing_meployees.mapped('name'))))

        # check here if timesheet already linked to SO line
        timesheet_with_so_line = self.env['account.analytic.line'].search_count([('task_id', 'in', self.project_id.tasks.ids), ('so_line', '!=', False)])
        if timesheet_with_so_line:
            raise UserError(_('The sales order cannot be created because some timesheets of this project are already linked to another sales order.'))

        # create SO according to the chosen billable type
        sale_order = self._create_sale_order()

        view_form_id = self.env.ref('sale.view_order_form').id
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action.update({
            'views': [(view_form_id, 'form')],
            'view_mode': 'form',
            'name': sale_order.name,
            'res_id': sale_order.id,
        })
        return action


class ProjectCreateSalesOrderDepartmentLine(models.TransientModel):
    _name = 'project.create.sale.order.dep.line'
    _description = 'Create SO Line from project'
    _order = 'id,create_date'

    wizard_id = fields.Many2one('project.create.sale.order', required=True)
    product_id = fields.Many2one('product.product',
                                 domain=[('type', '=', 'service'), ('invoice_policy', '=', 'delivery'),
                                         ('service_type', '=', 'timesheet')], string="Service", required=True,
                                 help="Product of the sales order item. Must be a service invoiced based on timesheets on tasks.")
    price_unit = fields.Float("Unit Price", default=1.0, help="Unit price of the sales order item.")
    currency_id = fields.Many2one('res.currency', string="Currency", related='product_id.currency_id', readonly=False)
    department_id = fields.Many2one('hr.department', string="Department", required=True,
                                    help="Department in tarification.")

    _sql_constraints = [
        ('unique_department_per_wizard', 'UNIQUE(wizard_id, department_id)',
         "A Department cannot be selected more than once in the mapping. Please remove duplicate(s) and try again."),
    ]

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.lst_price
