import logging

from odoo import http
from .services import validate_request

_logger = logging.getLogger(__name__)

class CartController(http.Controller):

    cors = "*"

    @http.route('/api/cart',auth='user',type='json',methods=['DELETE','POST','OPTIONS'],cors=cors)
    def cart(self, **kwargs):
        user_id = http.request.uid
        user = http.request.env['res.users'].sudo().search_read([('id','=',user_id)],fields=['partner_id'])
        partner_id = user[0].get('partner_id')[0]


        if kwargs.get('method') == 'GET':
            abandoned_order = http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('state','=','draft')])
            
            if abandoned_order:
                order_lines = http.request.env['sale.order.line'].sudo().search_read([('id','in',abandoned_order[0].get('website_order_line'))])
                abandoned_order[0]['order_lines'] = order_lines
                response = {'status':200,'response':abandoned_order,'message':"success"}
            else:
                print("no caart")
                response = {'status':200,'response':"Your cart is empty!",'message':"success"}

            return response
        

        if kwargs.get('method') == 'POST':
            try:
                abandoned_order = http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('state','=','draft')])
            
                if not abandoned_order:
                    print("no abnadon cart found craeting new")
                    vals = {'partner_id':partner_id}
                    order = http.request.env['sale.order'].sudo().create(vals)
                    abandoned_order = http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('state','=','draft')])
                    print("careated")
                    print(order)

                print(abandoned_order[0].get('id'))
                is_added = self.add_order_lines(kwargs.get('products'),abandoned_order[0].get('id'))
                print(is_added)
                if not is_added:
                    response = {'status':400,'response':{"error": "insufficient quantity"},'message':"validation error"}
                    return response


            except Exception as e:
                _logger.error("%s", e)
                response = {'status':400,'response':{"error": e},'message':"validation error"}

            response = {'status':200,'response':abandoned_order,'message':"success"}
            return response
        
        if kwargs.get('method') == 'DELETE':
            abandoned_order = http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('state','=','draft')])
            if not abandoned_order:
                response = {'status':200,'response':"Nothing to delete",'message':"success"}
                return response
            else:
                http.request.env['sale.order.line'].sudo().search([('id','in',kwargs.get('order_line_ids')),('order_id','=',abandoned_order[0].get('id'))]).unlink()
                response = {'status':200,'response':"Deleted",'message':"success"}
                return response


    def add_order_lines(self,products,order_id):
        is_available_quantity = self.is_available_quantity(products)
        if not is_available_quantity:
            return False
        
        for product in products:
            vals = {

                    'order_id':order_id,
                    "product_uom_qty":product.get('quantity'),
                    "product_id":product.get('id')
                }
            order = http.request.env['sale.order.line'].sudo().create(vals)
        return True

    def is_available_quantity(self,products):
        for product in products:
            product_data = http.request.env['product.product'].sudo().search_read([('id','=',product.get('id'))],fields=['free_qty'])
            if product_data[0].get('free_qty') < product.get('quantity'):
                return False
            else:
                return True


    def add_order_lines_with_discounts(self,products,order_id):
        pass

    