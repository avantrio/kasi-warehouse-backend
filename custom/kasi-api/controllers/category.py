from odoo import http
from .services import validate_request

class CategoryController(http.Controller):

    cors = "*"

    @http.route('/api/categories',auth='public',type='json',methods=['POST'],cors=cors)
    def get_categories(self, **kwargs):
        validate_request()
        categories = http.request.env['product.category'].sudo().search_read([],order="id asc")
        response = {'status':200,'response':categories,'message':"success"}
        return response
    
    @http.route('/api/categories/<int:category_id>',auth='public',type='json',methods=['POST'],cors=cors)
    def get_category(self, category_id,**kwargs):
        validate_request()
        category = http.request.env['product.category'].sudo().search_read([('id','=',category_id)])
        response = {'status':200,'response':category,'message':"success"}
        return response
    