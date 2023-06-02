from odoo import http

class ProductTemplateController(http.Controller):
    @http.route('/api/product-templates',auth='public',type='json')
    def get_product_templates(self, **kwargs):
        filter_set = []
        if 'order_by' not in kwargs:
            order_by = 'id desc'
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

        filter_set.append(('is_published','=',True))

        product_tempaltes = http.request.env['product.template'].sudo().search_read(filter_set,order=order_by)

        response = {'status':200,'response':product_tempaltes,'message':"success"}
        return response
    
    @http.route('/api/product-templates/<int:product_template_id>/',auth='public',type='json')
    def get_product_template(self,product_template_id,**kwargs):
        product_tempalte = http.request.env['product.template'].sudo().search_read([('id', '=', product_template_id)])
        response = {'status':200,'response':product_tempalte,'message':"success"}
        return response
    

    @http.route('/api/product-templates/<int:product_template_id>/products/',auth='public',type='json')
    def get_product_template_variants(self,product_template_id,**kwargs):
             
        product_tempalte = http.request.env['product.template'].sudo().search_read([('id', '=', product_template_id)],fields=['product_variant_ids'])                          
        products = http.request.env['product.product'].sudo().search_read([('id', 'in', product_tempalte[0].get('product_variant_ids')),('is_published','=',True)])

        for product in products:
            product_template_attribute_value = http.request.env['product.template.attribute.value'].sudo().search_read([('id', 'in', product.get('product_template_attribute_value_ids'))])
            product['product_template_attribute_value'] = product_template_attribute_value

        response = {'status':200,'response':products,'message':"success"}
        return response
    

    @http.route('/api/product-templates/<int:product_template_id>/products/<int:product_id>',auth='public',type='json')
    def get_product_template_variant(self,product_template_id,product_id,**kwargs):
        product = http.request.env['product.product'].sudo().search_read([('id', '=', product_id)])

        product_template_attribute_value = http.request.env['product.template.attribute.value'].sudo().search_read([('id', 'in', product[0].get('product_template_attribute_value_ids'))])
        product[0]['product_template_attribute_value'] = product_template_attribute_value

        response = {'status':200,'response':product,'message':"success"}
        return response
    
    @http.route('/api/product-templates/<int:product_template_id>/products/<int:product_id>/alternative-products',auth='public',type='json')
    def get_alternative_products(self,product_template_id, product_id,**kwargs):

        product = http.request.env['product.product'].sudo().search_read([('id', '=', product_id)])
        alternative_product_ids = product[0].get('alternative_product_ids')
        products = http.request.env['product.product'].sudo().search_read([('is_published','=',True),('id','in',alternative_product_ids)],order ='id asc')

        response = {'status':200,'response':products,'message':"success"}
        return response
    
    @http.route('/api/pricelists',auth='public',type='json')
    def get_pricelists(self,**kwargs):

        pricelists = http.request.env['product.pricelist'].sudo().search_read([],order ='id desc')
        
        response = {'status':200,'response':pricelists,'message':"success"}
        return response
    
    @http.route('/api/pricelists/<int:pricelist_id>/products/<int:product_id>',auth='public',type='json')
    def get_pricelist_products(self,pricelist_id,product_id,**kwargs):
        pricelists = http.request.env['product.pricelist'].sudo().search_read([('id','=',pricelist_id)],fields=['item_ids'])
        pricelist_items =  http.request.env['product.pricelist.item'].sudo().search_read([('id','in',pricelists[0].get('item_ids'))])
        for pricelist_item in pricelist_items:
            if pricelist_item.get('product_id')[0] == product_id:
                response = {'status':200,'response':pricelist_item,'message':"success"}
                return response
        
        response = {'status':200,'response':[],'message':"success"}
        return response
    