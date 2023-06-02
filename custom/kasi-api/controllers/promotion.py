from odoo import http

class PromotionController(http.Controller):

    @http.route('/api/promotions',auth='public',type='json')
    def get_promotions(self, **kwargs):
        if 'program_type' in kwargs:
            promotions = http.request.env['coupon.program'].sudo().search_read([('program_type','=',kwargs.get('program_type'))],order="id asc")
        else:
            promotions = http.request.env['coupon.program'].sudo().search_read([],order="id asc")
        response = {'status':200,'response':promotions,'message':"success"}
        return response
     
    @http.route('/api/promotions/<int:id>/',auth='public',type='json')
    def get_promotion(self,id,**kwargs):
        promotion = http.request.env['coupon.program'].sudo().search_read([('id', '=', id)])
        response = {'status':200,'response':promotion,'message':"success"}
        return response
    
    