from odoo import http
from .services import validate_request
from werkzeug.exceptions import NotFound
import uuid

class OrderController(http.Controller):

    cors = "*"

    @http.route('/api/orders',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def order(self, **kwargs):
        if kwargs.get('method') == 'GET':
            validate_request(kwargs)
            user_id = http.request.uid
            user = http.request.env['res.users'].sudo().search_read([('id','=',user_id)],fields=['partner_id'])            
            if 'state' in kwargs:
                orders = http.request.env['sale.order'].sudo().search_read([('user_id','=',user[0].get('id')),('state','!=','draft'),('state','=',kwargs.get('state'))],order="id desc")
            else:
                orders = http.request.env['sale.order'].sudo().search_read([('user_id','=',user[0].get('id')),('state','!=','draft')],order="id desc")
            response = {'status':200,'response':orders,'message':"success"}
            return response
        
        if kwargs.get('method') == 'POST':
            user_id = http.request.uid
            order_id = kwargs.get('order_id')
            vals = {'state':'sent','access_token':uuid.uuid4(),'payment_method':kwargs.get('payment_method'),'note':'Payment Method' + " " + ":" + " "+ kwargs.get('payment_method')}
            http.request.env['sale.order'].sudo().search([('id','=',order_id),('user_id','=',user_id),('state','=','draft')]).update(vals)
            return {'status':200,'response':"Updated",'message':"success"}
    
    @http.route('/api/orders/<int:order_id>',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_order(self, order_id,**kwargs):
        validate_request(kwargs)
        user_id = http.request.uid
        orders = http.request.env['sale.order'].sudo().search_read([('id','=',order_id),('user_id','=',user_id)])
        order_lines = http.request.env['sale.order.line'].sudo().search_read([('id','in',orders[0].get('website_order_line'))])
        orders[0]['order_lines'] = order_lines
        if not orders:
            raise NotFound('Not found')
        else:
            response = {'status':200,'response':orders,'message':"success"}
            return response
        