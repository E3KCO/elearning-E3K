# -*- coding: utf-8 -*-

{
    "name": "e3k Helpdesk",
    "summary": "Improvements",
    "description": "Improvements",
    "category": "Operations/Helpdesk",
    'author': "E3k Solutions",
    "license": "Other proprietary",
    "website": "https://e3k.co",
    "sequence": 1,
    "version": "15.0.1.0.0",
    "depends": [
        'helpdesk_sale',
        'helpdesk_timesheet',
        'sale_timesheet',
    ],
    "data": [
        'views/helpdesk.xml',
    ],
    "images": [],
    "application": False,
    "installable": True,
    "auto_install": False,
    "pre_init_hook": "pre_init_check",
}
