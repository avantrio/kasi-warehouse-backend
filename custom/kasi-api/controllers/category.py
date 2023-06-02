from odoo import http

class CategoryController(http.Controller):

    @http.route('/api/categories',auth='public',type='json')
    def get_categories(self, **kwargs):
        categories = http.request.env['product.category'].sudo().search_read([],order="id asc")
        response = {'status':200,'response':categories,'message':"success"}
        return response
    
    @http.route('/api/categories/<int:category_id>',auth='public',type='json')
    def get_category(self, category_id,**kwargs):
        category = http.request.env['product.category'].sudo().search_read([('id','=',category_id)])
        response = {'status':200,'response':category,'message':"success"}
        return response
    