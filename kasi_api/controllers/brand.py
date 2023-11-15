from odoo import http
from .services import validate_request

class BrandController(http.Controller):

    cors = "*"

    @http.route('/api/brands',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_brands(self, **kwargs):
        validate_request(kwargs)
        brands = http.request.env['product.brand'].sudo().search_read([],order="id asc")
        response = {'status':200,'response':brands,'message':"success"}
        return response
    
    @http.route('/api/brands/<int:brand_id>',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_brand(self, brand_id,**kwargs):
        validate_request(kwargs)
        brand = http.request.env['product.brand'].sudo().search_read([('id','=',brand_id)])
        response = {'status':200,'response':brand,'message':"success"}
        return response
    