# -*- coding: utf-8 -*-
{
    'name': "time_tracking",

    'summary': "Registro de fichajes de los empleados de la empresa",

    'description': """
        El objetivo de este módulo es el registro de los fichajes de los empleados de la empresa. Dicho registro
        podrá realizarse mediante tarjeta identificativa por parte de los trabajadores (a través de un lector NFC)
        o de forma manual por parte del responsable de administración.
        Este módulo servirá también como base para la revisión y control de los mismos a través de informes o consultas.
    """,

    'author': "Sergio Adell",
    'website': "https://github.com/Seradjor/PFC",

    # Indicamos que es una aplicación
    'application': True,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],

    # always loaded
    'data': [
        # Seguridad
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        # Datos de modelos
        'data/employees.xml',
        'data/records.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

