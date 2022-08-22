# -*- coding: utf-8 -*-

{
  "name" : "e3k Project Search",
  "summary" : "Ajout de la recherche par client.",
  "description" : "Ajout de la recherche par client.",
  "category" : "Operations/Project",
  'author': "E3k Solutions",
  "license" : "Other proprietary",
  "website" : "https://e3k.co",
  "sequence" : 1,
  "version" : "15.0.1.0.0",
  "depends" : [
    'project',
    'sale_timesheet',
  ],
  "data" : [
    'views/project_views.xml',
  ],
  "images" : [],
  "application" : False,
  "installable" : True,
  "auto_install" : False,
  "pre_init_hook" : "pre_init_check",
}