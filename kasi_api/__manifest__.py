{
    'name': 'kasi_rest_api',
    'version': '2.1.1',
    'category': 'REST API',
    'sequence': 15,
    'summary': 'Kasi warehouse REST API',
    'description': "Kasi warehouse REST API",
    'website': 'https://www.odoo.com/',
    "depends": [
        "sale",
    ],
    "data":[
        'security/ir.model.access.csv',
        'views/kasi_deals.xml',
    ]
}