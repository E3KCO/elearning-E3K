# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_print_report = fields.Selection(
        selection=[
            ('standard', 'Standard'),
            ('detail', 'Detail')
        ],
        help='Default print invoice',
        default='detail'
    )
