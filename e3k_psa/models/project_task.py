# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta


class Task(models.Model):
    _inherit = "project.task"

    recurrency = fields.Boolean(
        string='Recurrent',
    )
    repeat_period = fields.Selection(
        [('week', 'Week'), ('2week', 'Two weeks'), ('month', 'Month')],
        string='Repeat every',
        default='week'
    )
    repeat_end = fields.Selection(
        [('number', 'Repeat number')],
        string='To',
        default='number'
    )
    repeat_number = fields.Integer(
        string='Repeat number',
    )
    date_start = fields.Date(
        string='Date Start'
    )
    no_billable_hours = fields.Float(
        "Hours No Billable",
        compute='_compute_no_billable_hours',
        compute_sudo=True,
        store=True,
        help="Computed using the sum of no billable hours."
    )

    def _prepare_line_values(self, dates):
        res = []
        if not dates:
            dates = [self.date_start]
        if not self.date_start:
            dates = [fields.Datetime.now()]
        emp = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
        for date in dates:
            values = (0, 0, {
                'date': date,
                'account_id': self.project_id.analytic_account_id.id,
                'name': self.name,
                'product_uom_id': 6,
                'employee_id': emp.id,
                'so_line': self.sale_line_id.id,
                'project_id': self.project_id.id,
            })
            res.append(values)
        return res

    def _get_time_diff(self):
        self.ensure_one()
        diff = 0
        if self.repeat_period == 'week':
            diff = relativedelta(weeks=1)
        elif self.repeat_period == '2week':
            diff = relativedelta(weeks=2)
        elif self.repeat_period == 'month':
            diff = relativedelta(months=1)
        return diff

    def _get_dates(self):
        self.ensure_one()
        dates = []
        if self.repeat_number <= 0:
            dates.append(self.date_start)
        else:
            time_diff = time_diffs = self._get_time_diff()
            findate = self._find_last_date()
            mydate = findate and (findate + time_diffs) or self.date_start

            dates.append(mydate)
            for i in range(1, self.repeat_number):
                dates.append(mydate + time_diffs)
                time_diffs += time_diff
        return dates

    def update_recurrecy_lines(self):
        values = self._prepare_line_values(self._get_dates())
        self.update({'timesheet_ids': values})

    def _find_last_date(self):
        dates = self.timesheet_ids.sorted(key=lambda r: r.date)
        date = dates and dates[-1].date or False
        return date

    @api.model_create_multi
    def create(self, vals_list):
        records = super(Task, self).create(vals_list)
        # records.update_recurrecy_lines()
        return records

    def write(self, values):
        result = super(Task, self).write(values)
        if values.get('sale_line_id'):
            self.find_so_line(values['sale_line_id'])
        return result

    def find_so_line(self, sale_line_id):
        so_line = self.timesheet_ids.filtered(lambda x: not x.so_line and not x.timesheet_invoice_id)
        for line in so_line:
            line.sudo().write({
                'so_line': sale_line_id,
            })

    @api.depends('timesheet_ids.unit_amount', 'timesheet_ids.is_billable')
    def _compute_no_billable_hours(self):
        for task in self:
            no_billable_hours = 0
            for time_sheet in task.timesheet_ids:
                if not time_sheet.is_billable:
                    no_billable_hours += time_sheet.unit_amount
            task.no_billable_hours = no_billable_hours

    @api.depends('timesheet_ids.unit_amount', 'no_billable_hours')
    def _compute_effective_hours(self):
        for task in self:
            task.effective_hours = round(sum(task.timesheet_ids.mapped('unit_amount')), 2)
            task.effective_hours = task.effective_hours - task.no_billable_hours
