# -*- coding: utf-8 -*-

{
  "name" : "e3k Project",
  "summary" : "Suppléments pour gestion de projet interne.",
  "description" : "Modifications au module projet",
  "category" : "Operations/Project",
  'author': "E3k Solutions",
  "license" : "Other proprietary",
  "website" : "https://e3k.co",
  "sequence" : 1,
  "version" : "15.0.1.0.1",
  "depends" : [
    'project',
    # 'e3k_psa',
  ],
  "data" : [
    # 'data/data.xml',
    # 'data/ir_model_fields.xml',
    # 'data/ir_ui_view.xml',
    # 'data/project_cron.xml',
    'views/project_views.xml',
  ],
  "images" : [],
  "application" : False,
  "installable" : True,
  "auto_install" : False,
  # "pre_init_hook" : "pre_init_check",
}
