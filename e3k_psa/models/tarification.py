# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Tariffication(models.Model):
    _name = 'project.tarification'
    _description = "Tariffication"

    name = fields.Char(
        string='Tariffication Name',
        required=True,
        translate=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company'
    )
    tarification_ids = fields.One2many(
        'project.tarification.line',
        'tarification_id',
        string='Tariffication Lines'
    )
    department_tarification_ids = fields.One2many(
        'project.department.tarification',
        'tarification_id',
        string='Tariffication department Lines'
    )


class TarifficationLine(models.Model):
    _name = 'project.tarification.line'
    _description = 'Project Tarification Line'

    tarification_id = fields.Many2one(
        'project.tarification'
    )
    product_id = fields.Many2one(
        'product.product',
        domain=[
            ('type', '=', 'service'), ('invoice_policy', '=', 'delivery'),
            ('service_type', '=', 'timesheet')
        ], string="Service", required=True
    )
    price_unit = fields.Float(
        string="Unit Price",
        default=1.0
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        related='product_id.currency_id',
        readonly=False
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True
    )

    _sql_constraints = [
        ('unique_employee_tarif', 'unique(id)', 'Tariffication already exists for this employee.'),
    ]

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.lst_price


class TarifficationDepartmentLine(models.Model):
    _name = 'project.department.tarification'
    _description = 'Project Department Tarification '

    tarification_id = fields.Many2one(
        'project.tarification'
    )
    product_id = fields.Many2one(
        'product.product',
        domain=[
            ('type', '=', 'service'), ('invoice_policy', '=', 'delivery'),
            ('service_type', '=', 'timesheet')
        ], string="Service", required=True
    )
    price_unit = fields.Float(
        string="Unit Price",
        default=1.0
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        related='product_id.currency_id',
        readonly=False
    )
    department_id = fields.Many2one(
        'hr.department',
        string="Department",
        required=True
    )

    _sql_constraints = [
        ('unique_department_tarif', 'unique(id)', 'Tariffication already exists for this department.'),
    ]

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.lst_price