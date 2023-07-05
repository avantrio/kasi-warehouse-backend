import logging
import math
from odoo import http
from .services import validate_request

_logger = logging.getLogger(__name__)

class CartController(http.Controller):

    cors = "*"

    @http.route('/api/cart',auth='public',type='json',methods=['PUT','DELETE','POST','OPTIONS'],cors=cors)
    def cart(self, **kwargs):
        user_id = http.request.uid
        if user_id == 4:
            partner_id = 4
            public_user = True
        else:
            public_user = False
            user = http.request.env['res.users'].sudo().search_read([('id','=',user_id)],fields=['partner_id'])
            partner_id = user[0].get('partner_id')[0]


        if kwargs.get('method') == 'GET':
            if public_user:
                if 'order_id' in kwargs:
                    abandoned_order = http.request.env['sale.order'].sudo().search_read([('id','=',kwargs.get('order_id')),('state','=','draft'),('partner_id','=',partner_id)])
                    if abandoned_order:
                        order_lines = http.request.env['sale.order.line'].sudo().search_read([('id','in',abandoned_order[0].get('website_order_line'))])
                        abandoned_order[0]['order_lines'] = order_lines
                        response = {'status':200,'response':abandoned_order,'message':"success"}
                        return {'status':200,'response':abandoned_order,'message':"success"}
                    else:
                        return  {'status':200,'response':"Your cart is empty!",'message':"success"}
                else:
                    return  {'status':200,'response':"Your cart is empty!",'message':"success"}

            else:
                abandoned_order = http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('state','=','draft')])
                
                if abandoned_order:
                    order_lines = http.request.env['sale.order.line'].sudo().search_read([('id','in',abandoned_order[0].get('website_order_line'))])
                    abandoned_order[0]['order_lines'] = order_lines
                    response = {'status':200,'response':abandoned_order,'message':"success"}
                else:
                    response = {'status':200,'response':"Your cart is empty!",'message':"success"}

                return response
        

        if kwargs.get('method') == 'POST':
            if public_user:
                try:
                    if 'order_id' in kwargs:
                        abandoned_order = http.request.env['sale.order'].sudo().search_read([('id','=',kwargs.get('order_id')),('partner_id','=',partner_id),('state','=','draft')])                        
                    else:
                        vals = {'partner_id':partner_id}
                        order = http.request.env['sale.order'].sudo().create(vals)
                        abandoned_order = http.request.env['sale.order'].sudo().search_read([('id','=',order.id),('state','=','draft')])
                    response = {'status':200,'response':abandoned_order,'message':"success"}
                except Exception as e:
                    _logger.error("%s", e)
                    response = {'status':400,'response':{"error": e},'message':"validation error"}
                    return response
            else:
                try:
                    abandoned_order = http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('state','=','draft')])
                
                    if not abandoned_order:
                        vals = {'partner_id':partner_id}
                        http.request.env['sale.order'].sudo().create(vals)
                        abandoned_order = http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('state','=','draft')])
                    response = {'status':200,'response':abandoned_order,'message':"success"}
                except Exception as e:
                    _logger.error("%s", e)
                    response = {'status':400,'response':{"error": e},'message':"validation error"}
                    return response

            is_added = self.add_order_lines(kwargs.get('products'),abandoned_order[0].get('id'))
            if not is_added:
                response = {'status':400,'response':{"error": "insufficient quantity"},'message':"validation error"}
            return response

        
        if kwargs.get('method') == 'PUT':
            if public_user:
                if 'order_id' in kwargs:
                    abandoned_order = http.request.env['sale.order'].sudo().search_read([('id','=',kwargs.get('order_id')),('state','=','draft')])
                else:
                    return {'status':200,'response':"Nothing to update",'message':"success"}
            else:
                abandoned_order = http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('state','=','draft')])
            
            vals = {'product_uom_qty':kwargs.get('quantity')}
            if not abandoned_order:
                response = {'status':200,'response':"Nothing to update",'message':"success"}
                return response
            else:
                order_line = http.request.env['sale.order.line'].sudo().search([('id','=',kwargs.get('order_line_id')),('order_id','=',abandoned_order[0].get('id'))])
                if order_line:
                    order_line.sudo().update(vals)
                    response = {'status':200,'response':"Updated",'message':"success"}
                    return response
                else:
                    response = {'status':200,'response':"Nothing to update",'message':"success"}
                    return response
        
        if kwargs.get('method') == 'DELETE':
            if public_user:
                if 'order_id' in kwargs:
                    abandoned_order = http.request.env['sale.order'].sudo().search_read([('id','=',kwargs.get('order_id')),('state','=','draft')])
                else:
                    return {'status':200,'response':"Nothing to delete",'message':"success"}
            else:
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
            if 'pricelist_id' not in product:
                vals = {

                        'order_id':order_id,
                        "product_uom_qty":product.get('quantity'),
                        "product_id":product.get('id')
                    }
                http.request.env['sale.order.line'].sudo().create(vals)
            else:
                self.add_order_lines_with_discounts(product,order_id)
        return True

    def is_available_quantity(self,products):
        for product in products:
            product_data = http.request.env['product.product'].sudo().search_read([('id','=',product.get('id'))],fields=['free_qty'])
            if product_data[0].get('free_qty') < product.get('quantity'):
                return False
            else:
                return True


    def add_order_lines_with_discounts(self,product,order_id):
        product_data = http.request.env['product.product'].sudo().search_read([('id','=',product.get('id'))],fields=['name','list_price'])
        pricelist_items =  http.request.env['product.pricelist.item'].sudo().search_read([('product_id','=',product.get('id'))],fields=['min_quantity','pricelist_id','fixed_price','compute_price','percent_price'])

        if any(pricelist_item['pricelist_id'][0] == product.get('pricelist_id') for pricelist_item in pricelist_items):
            #getting the applicable price list item from the list
            for pricelist_item in pricelist_items:
                if pricelist_item.get('pricelist_id')[0] == product.get('pricelist_id'):
                    prircelist_item_of_prodct = pricelist_item
            if prircelist_item_of_prodct.get('min_quantity') > product.get('quantity'):
                _logger.error("Minimun quantity must be" + " " + str(prircelist_item_of_prodct.get('min_quantity')) + "discount not applied")
                vals = {
                        'order_id':order_id,
                        "product_uom_qty":product.get('quantity'),
                        "product_id":product.get('id'),
                    }
                http.request.env['sale.order.line'].sudo().create(vals)
            else:
                if prircelist_item_of_prodct.get('compute_price') == 'fixed':
                    discount_percentage = self.calculate_discount_percentage(product_data[0].get('list_price'),prircelist_item_of_prodct.get('fixed_price'))
                elif prircelist_item_of_prodct.get('compute_price') == 'percentage':
                    discount_percentage = prircelist_item_of_prodct.get('percent_price')
                vals = {
                        'order_id':order_id,
                        "product_uom_qty":product.get('quantity'),
                        "product_id":product.get('id'),
                        "discount":discount_percentage
                    }
                http.request.env['sale.order.line'].sudo().create(vals)

        else:
            _logger.error("Invalid pricelist id")

    def calculate_discount_percentage(self,product_price,discounted_fixed_price):
        discount = ((product_price - discounted_fixed_price)/product_price) * 100
        discount_percentage = math.floor(discount*100)/100
        return discount_percentage
        
        


    