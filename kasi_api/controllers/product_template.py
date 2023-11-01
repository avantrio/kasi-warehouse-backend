from odoo import http
from math import ceil
from werkzeug.exceptions import NotFound, MethodNotAllowed

from .services import validate_request,paginate

class ProductTemplateController(http.Controller):
    cors = "*"
    template_fields = ['price','active','is_product_variant','standard_price','pricelist_item_count',
              'image_128','__last_update','display_name','create_uid','create_date','write_date','qty_available','virtual_available','incoming_qty','outgoing_qty','base_unit_price',
              'is_published','name','description','type','detailed_type','categ_id','currency_id','list_price','product_variant_ids','product_variant_id','product_variant_count','alternative_product_ids',
              'product_template_image_ids','public_categ_ids']
    
    product_fields = ['price','price_extra','lst_price','partner_ref','active','product_tmpl_id','product_template_attribute_value_ids','is_product_variant','standard_price','pricelist_item_count',
              'image_128','__last_update','display_name','create_uid','create_date','write_date','qty_available','virtual_available','free_qty','incoming_qty','outgoing_qty','base_unit_price',
              'is_published','name','description','type','detailed_type','categ_id','currency_id','list_price','product_variant_ids','product_variant_id','product_variant_count','alternative_product_ids',
              'product_template_image_ids','public_categ_ids']

        
    @http.route('/api/product-templates',auth='public',type='json',methods=['POST','OPTIONS'],cors="*")
    def get_product_templates(self, **kwargs):
        validate_request(kwargs)
        response = {}
        filter_set = []
        if 'order_by' not in kwargs:
            order_by = 'id desc'
        else:
            order_by = kwargs.get('order_by')

        if 'category_ids' in kwargs:
            filter_set.append(('public_categ_ids','in',kwargs.get('category_ids')))
        if 'list_price_gte' in kwargs:
            filter_set.append(('list_price','>=',kwargs.get('list_price_gte')))
        if 'list_price_lte' in kwargs:
            filter_set.append(('list_price','<=',kwargs.get('list_price_lte')))
        if 'search' in kwargs:
            filter_set.append(('name','ilike',kwargs.get('search')))

        filter_set.append(('is_published','=',True))

        product_templates_total = http.request.env['product.template'].sudo().search_count(filter_set)

        if 'page' and 'page_size' in kwargs:
            page_size = kwargs.get('page_size')
            result = paginate(kwargs.get('page'),page_size,product_templates_total)
            response['total_count'] = result.get('total_count')
            response['current_page'] = result.get('current_page')
            response['previous_page'] = result.get('previous_page')
            response['next_page'] = result.get('next_page')
            offset= result.get('offset')
        else:
            offset = 0
            page_size = product_templates_total

        product_tempaltes = http.request.env['product.template'].sudo().search_read(filter_set,order=order_by,limit=page_size,offset=offset,fields=self.template_fields)

        for product_tempalte in product_tempaltes:
            product_public_categories = http.request.env['product.public.category'].sudo().search_read([('id', 'in', product_tempalte.get('public_categ_ids'))],
                                                                                                                       fields = ['name','id'])
            product_tempalte['product_public_categories'] = product_public_categories

        response['status'] = 200
        response['response'] = product_tempaltes
        response['message'] = 'success'
        return response
    
    @http.route('/api/product-templates/<int:product_template_id>/',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_product_template(self,product_template_id,**kwargs):
        validate_request(kwargs)
        product_tempalte = http.request.env['product.template'].sudo().search_read([('id', '=', product_template_id)])
        response = {'status':200,'response':product_tempalte,'message':"success"}
        return response
    

    @http.route('/api/product-templates/<int:product_template_id>/products/',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_product_template_variants(self,product_template_id,**kwargs):
        validate_request(kwargs)
        product_tempalte = http.request.env['product.template'].sudo().search_read([('id', '=', product_template_id)],fields=['product_variant_ids'])                          
        products = http.request.env['product.product'].sudo().search_read([('id', 'in', product_tempalte[0].get('product_variant_ids')),('is_published','=',True)],fields=self.product_fields)


        for product in products:
            product_template_attribute_values = http.request.env['product.template.attribute.value'].sudo().search_read([('id', 'in', product.get('product_template_attribute_value_ids'))],
                                                                                                                        fields = ['name','html_color','display_type','display_name'])
            product['product_attribute_values'] = product_template_attribute_values

            pricelist_items =  http.request.env['product.pricelist.item'].sudo().search_read([('product_id','=',product.get('id'))])
            product['pricelist_items'] = pricelist_items

            product_template_images  = http.request.env['product.image'].sudo().search_read([('id','in',product.get('product_template_image_ids'))])
            product['extra_product_media'] = product_template_images

            product_public_categories = http.request.env['product.public.category'].sudo().search_read([('id', 'in', product.get('public_categ_ids'))],
                                                                                                                       fields = ['name','id'])
            product['product_public_categories'] = product_public_categories

        response = {'status':200,'response':products,'message':"success"}
        return response
    

    @http.route('/api/product-templates/<int:product_template_id>/products/<int:product_id>',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_product_template_variant(self,product_template_id,product_id,**kwargs):
        validate_request(kwargs)
        products = http.request.env['product.product'].sudo().search_read([('id', '=', product_id)],fields=self.product_fields)

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
        
    #TODO logic changes for alternative products
    @http.route('/api/product-templates/<int:product_template_id>/products/<int:product_id>/alternative-products',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_alternative_products(self,product_template_id, product_id,**kwargs):
        validate_request(kwargs)
        product = http.request.env['product.product'].sudo().search_read([('id', '=', product_id)])
        alternative_product_ids = product[0].get('alternative_product_ids')
        products = http.request.env['product.product'].sudo().search_read([('is_published','=',True),('id','in',alternative_product_ids)],order ='id asc',fields=self.product_fields)

        for product in products:
            product_template_attribute_values = http.request.env['product.template.attribute.value'].sudo().search_read([('id', 'in', product.get('product_template_attribute_value_ids'))],
                                                                                                                        fields = ['name','html_color','display_type','display_name'])
            product['product_attribute_values'] = product_template_attribute_values

            pricelist_items =  http.request.env['product.pricelist.item'].sudo().search_read([('product_id','=',product.get('id'))])
            product['pricelist_items'] = pricelist_items

            product_template_images  = http.request.env['product.image'].sudo().search_read([('id','in',product.get('product_template_image_ids'))])
            product['extra_product_media'] = product_template_images

        response = {'status':200,'response':products,'message':"success"}
        return response
    
    @http.route('/api/pricelists',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_pricelists(self,**kwargs):
        validate_request(kwargs)
        pricelists = http.request.env['product.pricelist'].sudo().search_read([],order ='id desc')
        
        response = {'status':200,'response':pricelists,'message':"success"}
        return response
    
    @http.route('/api/pricelists/<int:pricelist_id>/products/<int:product_id>',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_pricelist_products(self,pricelist_id,product_id,**kwargs):
        validate_request(kwargs)
        pricelists = http.request.env['product.pricelist'].sudo().search_read([('id','=',pricelist_id)],fields=['item_ids'])
        pricelist_items =  http.request.env['product.pricelist.item'].sudo().search_read([('id','in',pricelists[0].get('item_ids'))])
        for pricelist_item in pricelist_items:
            if pricelist_item.get('product_id')[0] == product_id:
                response = {'status':200,'response':pricelist_item,'message':"success"}
                return response
        
        response = {'status':200,'response':[],'message':"success"}
        return response
    