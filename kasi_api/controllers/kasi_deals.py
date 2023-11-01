from odoo import http
from .services import validate_request

class KasiDealsController(http.Controller):

    cors = "*"

    fields = ['name','image','is_featured','is_active','start_date','end_date','category_id','display_name']

    @http.route('/api/deals',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_deals(self, **kwargs):
        validate_request(kwargs)
        deals = http.request.env['kasi.deals'].sudo().search_read([('is_active','=',True)],order="id asc",fields=self.fields)
        response = {'status':200,'response':deals,'message':"success"}
        return response
    
    @http.route('/api/deals/<int:deal_id>',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_deal(self, deal_id,**kwargs):
        validate_request(kwargs)
        deal = http.request.env['kasi.deals'].sudo().search_read([('id','=',deal_id)],fields=self.fields)
        response = {'status':200,'response':deal,'message':"success"}
        return response
    