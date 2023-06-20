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
            print(user_id)
            validate_request(kwargs)
            
            user = http.request.env['res.users'].sudo().search_read([('id','=',user_id)],fields=['partner_id'])
            orders = http.request.env['sale.order'].sudo().search_read([('partner_id','=',user[0].get('partner_id')[0])],order="id desc")

            response = {'status':200,'response':orders,'message':"success"}
            return response
        
        if kwargs.get('method') == 'POST':
            user_id = http.request.uid
            print(user_id)
            user = http.request.env['res.users'].sudo().search_read([('id','=',user_id)],fields=['partner_id'])
            partner_id = user[0].get('partner_id')[0]
            print(partner_id)
            values_updated_products_data = []
            products_in_cart = {}
            user_id = http.request.uid

            vals = {
                'partner_id': partner_id,
                'require_signature':True,
                'require_payment':True,
            }
            order = http.request.env['sale.order'].sudo().create(vals)
            
            # user = http.request.env['res.users'].sudo().search_read([('id','=',user_id)],fields=['partner_id'])
            # partner_id = user[0].get('partner_id')[0]

            for product in kwargs.get('products'):
                product_data = http.request.env['product.product'].sudo().search_read([('id', '=', product.get('id'))],fields=['name','list_price'])
                products_in_cart['product'] = product_data[0]
                products_in_cart['quantity'] = product.get('quantity')
                products_in_cart['pricelist_id'] = product.get('pricelist_id')
                values_updated_products_data.append(products_in_cart.copy())

            
            # for product_in_cart in products_in_cart:
            #     pricelist_items =  http.request.env['product.pricelist.item'].sudo().search_read([('product_id','=',product_in_cart.get('id'))])
            #     product_in_cart['pricelist_items'] = pricelist_items

            # TODO create orderline

            # for id in [18]:
            #     vals ={
            #         'order_id':52,
            #         # "price_sub_total":"price after applying pricelist or product amount ",
            #         # "price_tax":"price if tax",
            #         # "price_total":,
            #         "product_uom_qty":2,
            #         "product_id":id
            #     }
            #     order = http.request.env['sale.order.line'].sudo().create(vals)
            #     print(order)
            # order = http.request.env['sale.order.line'].sudo().search([('id','=',94)]).unlink()
            # values = {
            #     "code_promo_program_id":4
            # }
            # http.request.env['sale.order'].sudo().search([('id','=',56)]).update(values)
            return {'status':200,'response':values_updated_products_data,'message':"success"}
    
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
        