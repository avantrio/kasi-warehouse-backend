from odoo import models, fields, api

class MobileVerification(models.Model):
    _name = "mobile.verification"
    _description = "mobile verification data"

    token = fields.Char( string='Token', required=True)
    mobile_verified = fields.Boolean(string='Mobile Verified', default=False)
    mobile_number = fields.Char(string='Mobile Number', required=True)
    created_date = fields.Datetime(string="Created Date", readonly=True)

    @api.model
    def create(self, vals):
        vals['created_date'] = fields.Datetime.now()
        return super(MobileVerification, self).create(vals)

    