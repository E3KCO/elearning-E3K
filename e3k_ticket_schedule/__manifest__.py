{
    'name': "e3k_ticket_schedule",
    'description': """
        this module allows to define a user for a Ticket according the hours 
        entered in the Ticket Assignment view.""",
    'author': "E3K",
    'website': "https://www.e3k.co",
    'category': 'Services/Helpdesk',
    'version': '0.1',
    'depends': ['helpdesk'],
    'data': [
        'views/ticket_assignment_view.xml',
        'views/helpdesk_ticket_form_view.xml',
        'data/ticket_assignment_sequence.xml',
        'security/ir.model.access.csv'
    ],
}
