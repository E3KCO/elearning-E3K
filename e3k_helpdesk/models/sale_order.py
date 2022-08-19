# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression

class SaleOrder(models.Model):
  _inherit = 'sale.order'

  def name_get(self):
    result = []
    ticket = self._context.get('ticket', False)
    if not ticket:
      return super().name_get()
    for order in self:
      name = order.name
      if order.analytic_account_id:
        name = '%s %s' % (name, order.analytic_account_id.name)
      result.append((order.id, name))
    return result

  @api.model
  def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    ticket = self._context.get('ticket', False)
    if not ticket:
      return super()._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)
    args = args or []
    domain = []
    if name:
      domain = ['|', ('analytic_account_id', operator, name), ('name', operator, name)]
      if operator in expression.NEGATIVE_TERM_OPERATORS:
        domain = ['&', '!'] + domain[1:]
    account_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
    return models.lazy_name_get(self.browse(account_ids).with_user(name_get_uid))
