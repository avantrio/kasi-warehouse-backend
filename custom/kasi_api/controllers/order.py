from odoo import http
from .services import validate_request
from werkzeug.exceptions import NotFound

class OrderController(http.Controller):

    cors = "*"

    @http.route('/api/orders',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def order(self, **kwargs):
        print("came")
        if kwargs.get('method') == 'GET':
            user_id = http.request.uid
            validate_request(kwargs)
            
            user = http.request.env['res.users'].sudo().search_read([('id','=',user_id)],fields=['partner_id'])
            orders = http.request.env['sale.order'].sudo().search_read([('partner_id','=',user[0].get('partner_id')[0])],order="id desc")

            response = {'status':200,'response':orders,'message':"success"}
            return response
        
        if kwargs.get('method') == 'POST':
            user_id = http.request.uid

            user = http.request.env['res.users'].sudo().search_read([('id','=',user_id)],fields=['partner_id'])
            partner_id = user[0].get('partner_id')[0]

            #TODO invoice creation logic
            vals = {
                'partner_id': partner_id
            }
            order = http.request.env['sale.order'].sudo().create(vals)

            return {'status':200,'response':order,'message':"success"}
    
    @http.route('/api/orders/<int:order_id>',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_order(self, order_id,**kwargs):
        validate_request(kwargs)
        user_id = http.request.uid
        
        user = http.request.env['res.users'].sudo().search_read([('id','=',user_id)],fields=['partner_id'])
        orders = http.request.env['sale.order'].sudo().search_read([('id','=',order_id),('partner_id','=',user[0].get('partner_id')[0])])

        if not orders:
            raise NotFound('Not found')
        else:
            response = {'status':200,'response':orders,'message':"success"}
            return response
        