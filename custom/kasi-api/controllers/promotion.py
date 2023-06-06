from odoo import http
from .services import validate_request

class PromotionController(http.Controller):

    cros = "*"
    
    @http.route('/api/promotions',auth='public',type='json',methods=['POST'],cros=cros)
    def get_promotions(self, **kwargs):
        validate_request()
        if 'program_type' in kwargs:
            promotions = http.request.env['coupon.program'].sudo().search_read([('program_type','=',kwargs.get('program_type'))],order="id asc")
        else:
            promotions = http.request.env['coupon.program'].sudo().search_read([],order="id asc")
        response = {'status':200,'response':promotions,'message':"success"}
        return response
     
    @http.route('/api/promotions/<int:id>/',auth='public',type='json',methods=['POST'],cros=cros)
    def get_promotion(self,id,**kwargs):
        validate_request()
        promotion = http.request.env['coupon.program'].sudo().search_read([('id', '=', id)])
        response = {'status':200,'response':promotion,'message':"success"}
        return response
    
    