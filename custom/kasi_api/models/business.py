from odoo import models, fields

class Business(models.Model):
    _inherit="res.company"

    Types = [
        ('BC', 'Beauty & Cosmetic stores'),
        ('SL', 'Salons'),
        ('SP', 'Spazarettes'),
        ('MW', 'Midi Wholesale'),
        ('MP', 'Market Place'),
    ]

    business_type = fields.Selection(Types, string='Business Type', required=False)



