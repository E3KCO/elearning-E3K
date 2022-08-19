# -*- coding: utf-8 -*-

from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_print_report = fields.Selection(
        selection=[
            ('standard', 'Détaillé'),
            ('detail', 'Semi-détaillé'),
            ('summary', 'Summary')
        ],
        help='Default print invoice',
        default='detail'
    )
    invoice_text = fields.Html(string='Invoice text', translate=True)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        if self.partner_id:
            invoice_print_report = self.partner_id.invoice_print_report
            self.invoice_print_report = invoice_print_report and invoice_print_report or False

    def _prepare_invoice(self):
        """
            Override
            Add new value in dict of invoice value
        :return: dictionary of value
        """
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
            'invoice_print_report': self.invoice_print_report,
            'invoice_text': self.invoice_text
        })
        return res

    def generate_invoice_timesheets_at_date(self):
        self.ensure_one()
        action = self.env.ref('e3k_psa.action_timesheet_invoice_at_date').read()[0]
        ctx = dict(self.env.context or {})
        ctx.pop('group_by', None)
        action['context'] = ctx  # erase default filters
        return action

    def name_get(self):
        if self._context.get('sale_expense_all_order'):
            names = []
            for rec in self:
                analytic = rec.analytic_account_id and rec.analytic_account_id.name or ''
                namex = '%s - %s - %s ' % (rec.name, rec.partner_id.name, analytic)
                names.append((rec.id, namex))
            return names
        else:
            return super(SaleOrder, self).name_get()

    def _psa_create_invoices(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:
            pending_section = None

            # Invoice values.
            invoice_vals = order._prepare_invoice()

            # Invoice line values (keep only necessary sections).
            for line in order.order_line.filtered(lambda t: t.no_bill == False):
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision) and not line.product_id.can_be_expensed:
                    continue
                # if line.qty_psa > 0 or (line.qty_psa < 0 and final) or (line.qty_psa == 0 and line.product_id.can_be_expensed):
                line.no_bill = True
                if pending_section:
                    invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
                    pending_section = None
                invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))

            if not invoice_vals['invoice_line_ids']:
                raise UserError(_(
                    'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            for grouping_keys, invoices in groupby(invoice_vals_list,
                                                   key=lambda x: (x.get('partner_id'), x.get('currency_id'))):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    # payment_refs.add(invoice_vals['invoice_payment_ref'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    # 'invoice_payment_ref': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_type='out_invoice').create(invoice_vals_list)
        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                                        values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                                        subtype_id=self.env.ref('mail.mt_note').id
                                        )
        return moves
