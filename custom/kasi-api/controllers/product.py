from odoo import http
from werkzeug.exceptions import NotFound
from math import ceil

from .services import validate_request

class ProductTemplateController(http.Controller):

    cors = '*'
    fields = ['price','price_extra','lst_price','partner_ref','active','product_tmpl_id','product_template_attribute_value_ids','is_product_variant','standard_price','pricelist_item_count',
              'image_128','__last_update','display_name','create_uid','create_date','write_date','qty_available','virtual_available','free_qty','incoming_qty','outgoing_qty','base_unit_price',
              'is_published','name','description','type','detailed_type','categ_id','currency_id','list_price','product_variant_ids','product_variant_id','product_variant_count','alternative_product_ids',
              'product_template_image_ids']

    def filter_products_based_on_color(self,product,html_colors):
        for product_attribute_value in product.get('product_attribute_values'):
            if product_attribute_value.get('html_color') in html_colors:
                return True
        return False
    
    def filter_products_based_on_pricelist(self,product,pricelist_ids):
        for pricelist_item in product.get('pricelist_items'):
            if pricelist_item.get('pricelist_id')[0] in pricelist_ids:
                return True
        return False

    def paginate(self,page,page_size,total):
        result = {}
        if page <= 0  or page_size <= 0:
            offset = 0
            page_size = 25
        else:
            offset  = (page - 1) * page_size
            result['total_count'] = total
            result['current_page'] = page
            result['previous_page'] = page - 1 if page != 1 else None
            result['next_page'] = page + 1 if ceil(total/page_size) != result.get('current_page') else None
            result['offset'] = offset
            return result

    @http.route('/api/products',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_products(self, **kwargs):
        validate_request(kwargs)
        filter_set = []
        response = {}
        if 'order_by' not in kwargs:
            order_by = 'id asc'
        else:
            order_by = kwargs.get('order_by')

        if 'category_id' in kwargs:
            filter_set.append(('categ_id','=',kwargs.get('category_id')))
        if 'list_price_gte' in kwargs:
            filter_set.append(('list_price','>=',kwargs.get('list_price_gte')))
        if 'list_price_lte' in kwargs:
            filter_set.append(('list_price','<=',kwargs.get('list_price_lte')))
        if 'search' in kwargs:
            filter_set.append(('name','ilike',kwargs.get('search')))
        
        # default filter for all products
        filter_set.append(('is_published','=',True))

        products_total = http.request.env['product.product'].sudo().search_count(filter_set)

        if 'page' and 'page_size' in kwargs:
            page_size = kwargs.get('page_size')
            result = self.paginate(kwargs.get('page'),page_size,products_total)
            response['total_count'] = result.get('total_count')
            response['current_page'] = result.get('current_page')
            response['previous_page'] = result.get('previous_page')
            response['next_page'] = result.get('next_page')
            offset= result.get('offset')
        else:
            offset = 0
            page_size = products_total


        products = http.request.env['product.product'].sudo().search_read(filter_set,order=order_by,offset=offset,limit=page_size,fields=self.fields)

        # appending product attribues and pricelist items to product list
        for product in products:
            product_template_attribute_values = http.request.env['product.template.attribute.value'].sudo().search_read([('id', 'in', product.get('product_template_attribute_value_ids'))],
                                                                                                                       fields = ['name','html_color','display_type','display_name'])
            product['product_attribute_values'] = product_template_attribute_values

            pricelist_items =  http.request.env['product.pricelist.item'].sudo().search_read([('product_id','=',product.get('id'))])
            product['pricelist_items'] = pricelist_items

        if 'html_colors' in kwargs:
            products[:] = (product for product in products if self.filter_products_based_on_color(product,kwargs.get('html_colors')))
        
        if 'pricelist_ids' in kwargs:
            products[:] = (product for product in products if self.filter_products_based_on_pricelist(product,kwargs.get('pricelist_ids')))
            

        response['status'] = 200
        response['response'] = products
        response['message'] = 'success'
        return response
    
    @http.route('/api/products/<int:product_id>/',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_product(self,product_id,**kwargs):
        validate_request(kwargs)
        products = http.request.env['product.product'].sudo().search_read([('id', '=', product_id)],fields=self.fields)
        
        for product in products:
            product_template_attribute_values = http.request.env['product.template.attribute.value'].sudo().search_read([('id', 'in', product.get('product_template_attribute_value_ids'))],
                                                                                                                        fields = ['name','html_color','display_type','display_name'])
            product['product_attribute_values'] = product_template_attribute_values

            pricelist_items =  http.request.env['product.pricelist.item'].sudo().search_read([('product_id','=',product.get('id'))])
            product['pricelist_items'] = pricelist_items

            product_template_images  = http.request.env['product.image'].sudo().search_read([('id','in',product.get('product_template_image_ids'))])
            product['extra_product_media'] = product_template_images

        if not products:
            raise NotFound('Not found')
        else:
            response = {'status':200,'response':products,'message':"success"}
            return response
    
    @http.route('/api/products/<int:product_id>/alternative-products',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_alternative_products(self,product_id,**kwargs):
        validate_request(kwargs)
        alternative_products_list = []
        product = http.request.env['product.product'].sudo().search_read([('id', '=', product_id)])
        if product:
            alternative_product_templates = http.request.env['product.template'].sudo().search_read([('is_published','=',True),('id','in',product[0].get('alternative_product_ids'))],order ='id asc',fields=['product_variant_ids'])
            for alternative_product_template in alternative_product_templates:
                alternative_products = http.request.env['product.product'].sudo().search_read([('is_published','=',True),('id','in',alternative_product_template.get('product_variant_ids'))],order ='id asc',fields=self.fields)
                for alternative_product in alternative_products:
                    alternative_products_list.append(alternative_product)
            response = {'status':200,'response':alternative_products_list,'message':"success"}
            return response
        else:
            raise NotFound('Not found')

    @http.route('/api/product-colors',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_product_colors(self,**kwargs):
        validate_request(kwargs)
        product_attributes = http.request.env['product.attribute'].sudo().search_read([('display_type','=','color'),('display_name','=','Color')],fields=['value_ids'])
        if len(product_attributes) == 1:
            if product_attributes[0].get('value_ids') is not None:
                values = http.request.env['product.attribute.value'].sudo().search_read([('id','in',product_attributes[0].get('value_ids'))],fields = ['html_color','display_name','name'],order='id asc')
                response = {'status':200,'response':values,'message':"success"}
        else:
            response = {'status':400,'message':"Error getiing product attributes"}

        return response
