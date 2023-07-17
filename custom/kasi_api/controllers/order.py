from odoo import http
from .services import validate_request
from werkzeug.exceptions import NotFound
import uuid

class OrderController(http.Controller):

    cors = "*"

    @http.route('/api/orders',auth='user',type='json',methods=['POST','OPTIONS','PUT'],cors=cors)
    def order(self, **kwargs):
        user_id = http.request.uid
        user = http.request.env['res.users'].sudo().search_read([('id','=',user_id)],fields=['partner_id'])
        partner_id = user[0].get('partner_id')[0]

        if kwargs.get('method') == 'GET':
            validate_request(kwargs)
            if 'state' in kwargs:
                orders = http.request.env['sale.order'].sudo().search_read([('user_id','=',user[0].get('id')),('state','!=','draft'),('state','=',kwargs.get('state'))],order="id desc")
            else:
                orders = http.request.env['sale.order'].sudo().search_read([('user_id','=',user[0].get('id')),('state','!=','draft')],order="id desc")
            response = {'status':200,'response':orders,'message':"success"}
            return response
        
        if kwargs.get('method') == 'POST':
            order_id = kwargs.get('order_id')
            order_to_be_updated = http.request.env['sale.order'].sudo().search_read([('id','=',order_id),('state','=','draft')],fields=['user_id','website_order_line'])
            order_lines = http.request.env['sale.order.line'].sudo().search_read([('id','in',order_to_be_updated[0].get('website_order_line'))],fields=['free_qty_today','product_id','product_uom_qty'])
            invalid_order_lines = self.check_free_quantity(order_lines)
            if invalid_order_lines:
                response = {'status':400,'response':"Item quantity should be less than the available stock quantity. Please re-adjust the quantity","invalid_order_lines":invalid_order_lines,'message':"success"} 
            else:
                vals = {'state':'sent','access_token':uuid.uuid4(),'payment_method':kwargs.get('payment_method'),'note':'Payment Method' + " " + ":" + " "+ kwargs.get('payment_method')}
                if order_to_be_updated[0].get('user_id') == False or order_to_be_updated[0].get('user_id')[0] == 4:
                    vals['user_id'] = user_id
                    vals['partner_id'] = partner_id
                    vals['partner_invoice_id'] = partner_id
                    vals['partner_shipping_id'] = partner_id
                    http.request.env['sale.order'].sudo().search([('id','=',order_id),('state','=','draft')]).update(vals)
                    response =  {'status':200,'response':"Order created successfully",'message':"success"}
                elif order_to_be_updated[0].get('user_id')[0] == user_id:
                    http.request.env['sale.order'].sudo().search([('id','=',order_id),('state','=','draft')]).update(vals)
                    response =  {'status':200,'response':"Order created successfully",'message':"success"}
                else:
                   response = {'status':400,'response':"Invalid order",'message':"success"} 

            return response
    
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
    
    @http.route('/api/orders/<int:order_id>',auth='user',type='json',methods=['PUT','OPTIONS'],cors=cors)
    def update_order(self, order_id,**kwargs):
        user_id = http.request.uid
        user = http.request.env['res.users'].sudo().search_read([('id','=',user_id)],fields=['partner_id'])
        partner_id = user[0].get('partner_id')[0]
        public_order = kwargs.get('public_order')

        if public_order and kwargs.get('method') == 'PUT':
            abandoned_order =  http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('state','=','draft')])
            order_to_be_updated = http.request.env['sale.order'].sudo().search_read([('id','=',order_id),('state','=','draft'),('user_id','=',4)],fields=['user_id','website_order_line'])
            if order_to_be_updated:
                abandoned_order =  http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('state','=','draft')])
                if abandoned_order:
                    order_lines = http.request.env['sale.order.line'].sudo().search([('id','in',order_to_be_updated[0].get('website_order_line'))])
                    order_lines.sudo().update({'order_id':abandoned_order[0].get('id')})
                else:
                    vals = {
                    'user_id':user_id,
                    'partner_id':partner_id,
                    'partner_invoice_id':partner_id,
                    'partner_shipping_id':partner_id
                    }
                    http.request.env['sale.order'].sudo().search([('id','=',order_id),('state','=','draft')]).update(vals)

                respose = {'status':200,'response':"Updated",'message':"success"}
            else:
                respose = {'status':200,'response':"Nothing to Update",'message':"success"}
        else:
            respose = {'status':400,'response':"Invalid order",'message':"success"}

        return respose
        
    @http.route('/api/orders/<int:order_id>/promotions',auth='user',type='json',methods=['POST'],cors=cors)
    def apply_promo_code(self,order_id, **kwargs):
        user_id = http.request.uid
        if kwargs.get('method') == 'POST':
            order = http.request.env['sale.order'].sudo().search_read([('id','=',order_id),('user_id','=',user_id),('state','=','draft')])
            if order:
                promotion = http.request.env['coupon.program'].sudo().search_read([('program_type','=','promotion_program'),('promo_code','=',kwargs.get('promo_code'))])
                if promotion:
                    if promotion[0].get('rule_minimum_amount') > order[0].get('amount_total') or promotion[0].get('active') == False:
                        return {'status':400,'response':"code is invalid",'message':"success"}
                    else:
                        if promotion[0].get('discount_type') == 'percentage':
                            discount_price = self.calculate_percentage_promo_code_discount(promotion[0].get('discount_percentage'),order[0].get('amount_untaxed'))
                        
                        if promotion[0].get('discount_type') == 'fixed_amount':
                            discount_price = promotion[0].get('discount_fixed_amount')
                        
                        vals = self.generate_discount_order_line_values(promotion[0].get('discount_line_product_id')[0],order[0].get('id'),discount_price)
                        http.request.env['sale.order.line'].sudo().create(vals)
                        promotion_values = {"code_promo_program_id":promotion[0].get('id'),"promo_code":kwargs.get('promo_code')}
                        http.request.env['sale.order'].sudo().search([('id','=',order_id),('state','=','draft')]).update(promotion_values)
                        return {'status':200,'response':"code applied",'message':"success"}
                else:
                    return {'status':400,'response':"Invalid code",'message':"success"}
                
            else:
                return {'status':400,'response':"Invalid order",'message':"success"}
            
    @http.route('/api/reorders',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def reorder(self,**kwargs):
        user_id = http.request.uid
        user = http.request.env['res.users'].sudo().search_read([('id','=',user_id)],fields=['partner_id'])
        partner_id = user[0].get('partner_id')[0]
        order_id = kwargs.get('order_id')
        order = http.request.env['sale.order'].sudo().search_read([('id','=',order_id),('user_id','=',user_id),('state','!=','draft')])

        if not order:
            return {'status':400,'response':"Invalid order",'message':"success"}
        else:
            order_lines = http.request.env['sale.order.line'].sudo().search_read([('order_id','=',order[0].get('id'))],fields=['product_uom_qty','product_id'])
            abandoned_order = http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('state','=','draft'),('partner_id','=',partner_id)])

            if abandoned_order:
                # removing existing cart order items
                http.request.env['sale.order.line'].sudo().search([('order_id','=',abandoned_order[0].get('id'))]).unlink()
                #assigning new products to cart order
                for order_line in order_lines:
                    vals = {
                        'order_id':abandoned_order[0].get('id'),
                        "product_uom_qty":order_line.get('product_uom_qty'),
                        "product_id":order_line.get('product_id')[0]
                    }
                    http.request.env['sale.order.line'].sudo().create(vals)

                return {'status':200,'response':"Existing cart is cleared and reorder products added to cart",'message':"success"}
            else:
                vals = {'partner_id':partner_id}
                # creating new order
                order = http.request.env['sale.order'].sudo().create(vals)
                for order_line in order_lines:
                    vals = {
                        'order_id':order.id,
                        "product_uom_qty":order_line.get('product_uom_qty'),
                        "product_id":order_line.get('product_id')[0]
                    }
                    http.request.env['sale.order.line'].sudo().create(vals)
            
                return {'status':200,'response':"Reorder products added to cart",'message':"success"}

    def calculate_percentage_promo_code_discount(self,discount_percentage,total):
        return round(float(total)/float(100) * float(discount_percentage),2)

    def generate_discount_order_line_values(self,product_id,order_id,discount_price):
        vals = {
                "product_id":product_id,
                "order_id":order_id,
                "product_uom_qty":1,
                "is_reward_line":True,
                "price_unit": -discount_price,
                "price_subtotal":-discount_price,
                "price_total":-discount_price,
                "price_reduce":-discount_price,
                "price_reduce_taxinc":-discount_price,
                "price_reduce_taxexcl":-discount_price
                  
            }
        return vals
    
    def check_free_quantity(self,order_lines):
        invalid_order_lines = []
        for order_line in order_lines:
            if order_line.get('product_uom_qty') > order_line.get('free_qty_today'):
                invalid_order_lines.append(order_line)
        return invalid_order_lines
