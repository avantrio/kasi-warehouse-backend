from odoo import models, fields

class KasiUser(models.Model):
    _inherit="res.users"

    business_id = fields.Integer(string='Business Id', required=False)
