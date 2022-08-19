# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class Expense(models.Model):
    _inherit = "hr.expense"

    @api.model
    def _default_employee_id(self):
        return self.sudo().env.user.employee_id

    account_invoice_id = fields.Many2one('account.move', string='Account Invoice', readonly=True, copy=False)
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sales Order Line Item')
    include = fields.Boolean('Include', default=True)
