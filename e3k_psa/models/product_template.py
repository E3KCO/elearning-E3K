# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    department_id = fields.Many2one('hr.department', string="Département")
