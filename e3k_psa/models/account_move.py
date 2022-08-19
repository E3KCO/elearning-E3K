# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_print_report = fields.Selection(
        selection=[
            ('standard', 'Détaillé'),
            ('detail', 'Semi-détaillé'),
            ('summary', 'Summary')
        ],
        help='Default print invoice',
        default='detail'
    )
    order_id = fields.Many2many(
        'sale.order',
        string='Order Reference',
        compute='_compute_orders',
        readonly=True,
        store=True,
        compute_sudo=True
    )
    expense_count = fields.Integer(
        "# of Expenses",
        compute='_compute_expense_count',
        compute_sudo=True,
        store=True,
    )
    expense_ids = fields.One2many(
        'hr.expense',
        'account_invoice_id',
        string='Expenses',
        readonly=True,
        copy=False
    )
    invoice_text = fields.Html(string='Invoice text', translate=True)
    invoice_payment_ref = fields.Char(string='Payment reference')

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        obj = self.env['account.analytic.line']
        timesheets = obj.search([('timesheet_invoice_id', 'in', self.ids)])
        timesheets.sudo().write({'timesheet_invoice_id': False})
        self.expense_ids.sudo().write({'account_invoice_id': False})
        return res

    @api.depends('line_ids')
    def _compute_orders(self):
        for order in self:
            line = order.line_ids.mapped('sale_line_ids')
            order.order_id = [o.order_id.id for o in line]

    @api.depends('expense_ids')
    def _compute_expense_count(self):
        for move in self:
            move.expense_count = len(move.expense_ids)

    def get_is_annex_timesheet_ids(self):
        is_annex_timesheet_ids = False
        if self.timesheet_ids:
            is_annex_timesheet_ids = self.env["account.analytic.line"].search(
                [('id', 'in', self.timesheet_ids.ids)], order='so_line, date'
            )
        return is_annex_timesheet_ids


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    order_lines = fields.Many2many(
        'sale.order.line',
        'sale_order_line_invoice_rel',
        'invoice_line_id', 'order_line_id',
        string='Invoice Lines',
        copy=False
    )

    # @api.model_create_multi
    # def create(self, vals_list):
    #     cxt = self._context
    #     res = super(AccountMoveLine, self).create(vals_list)
    #     import pdb; pdb.set_trace()
    #
    #     if cxt.get('active_model') == 'hr.expense':
    #         return res
    #
    #     if cxt.get('invoice_date'):
    #         invoice_date = cxt.get('invoice_date').strftime("%Y-%m-%d")
    #     else:
    #         invoice_date = date.today()
    #
    #     hr_expense_line_ids = []
    #
    #     for move in res:
    #         if move.product_id.can_be_expensed:
    #             order_ids = [o.order_id.id for o in move.sale_line_ids]
    #             if move.quantity >= 0:
    #                 expenses = self.env['hr.expense'].search([('sale_order_id', 'in', order_ids),
    #                                                           ('account_invoice_id', '=', False),
    #                                                           ('date', '<=', invoice_date),
    #                                                           ('id', 'not in', hr_expense_line_ids),
    #                                                           ('state', 'in', ['done', 'approved'])
    #                                                           ], limit=int(move.quantity))
    #                 hr_expense_line_ids += expenses.ids
    #
    #                 if expenses:
    #                     expenses.sudo().write({'account_invoice_id': move.move_id.id})
    #     return res

    @api.model
    def _timesheet_domain_get_invoiced_lines(self, sale_line_delivery):
        """ Get the domain for the timesheet to link to the created invoice
            :param sale_line_delivery: recordset of sale.order.line to invoice
            :return a normalized domain
        """

        timesheet_ids = sale_line_delivery.timesheet_ids
        ctx = self._context
        date = fields.date.today().strftime("%Y-%m-%d")
        if ctx.get('invoice_date'):
            date = ctx.get('invoice_date').strftime("%Y-%m-%d")

        if timesheet_ids:
            return ['&', ('so_line', 'in', sale_line_delivery.ids), '&', ('timesheet_invoice_id', '=', False),
                    '&', ('project_id', '!=', False), ('id', 'in', timesheet_ids.ids), ('date', '<=', date),
                    ('reported', '=', False)]
        else:
            return ['&', ('so_line', 'in', sale_line_delivery.ids), '&', ('timesheet_invoice_id', '=', False),
                    ('project_id', '!=', False), ('date', '<=', date), ('reported', '=', False)]

    def _sale_prepare_sale_line_values(self, order, price):
        """ Overied method of create expense in order line.
            To add additionnel percent
        """
        res = super(AccountMoveLine, self)._sale_prepare_sale_line_values(order, price)
        obj = self.env['project.expense']
        expense_id = obj.search([('expense_id.analytic_account_id', '=', self.analytic_account_id.id),
                                 ('product_id', '=', res['product_id'])])
        if expense_id:
            res['price_unit'] = (1 + expense_id.percent) * res['price_unit']
        return res
