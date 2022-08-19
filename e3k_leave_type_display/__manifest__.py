{
    'name': "e3k_leave_type_display",
    'summary': """
         This module allows to displaying Leave type in gant view popup
         and when user move mouse on a leave as well""",
    'author': "E3KO",
    'website': "https://www.e3k.co",
    'category': 'Human Resources/Time Off',
    'version': '0.1',
    'depends': ['hr_holidays', 'hr_holidays_gantt'],
    'data': [
        'views/hr_leave_report_calendar_view.xml'
    ],
}
