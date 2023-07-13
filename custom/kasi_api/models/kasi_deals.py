from odoo import models, fields, api

class KasiDeals(models.Model):
    _name = "kasi.deals"
    _description = "kasi deals"

    name = fields.Char(string='Name',required=False)
    image = fields.Image("Image", max_width=1920, max_height=1920)
    is_featured = fields.Boolean(string='Is Featured', default=False)
    is_active = fields.Boolean(string='Is Active', default=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    category_id = fields.Many2one('product.category', 'Product Category', index=True, ondelete='cascade',required=False)

