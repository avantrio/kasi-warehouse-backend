from odoo import http
from .services import validate_request
from werkzeug.exceptions import NotFound
from math import ceil

class InvoiceController(http.Controller):

    cors = "*"

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
        
    @http.route('/api/invoices',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def invoice(self, **kwargs):
        if kwargs.get('method') == 'GET':
            filter_set = []
            response = {}
            validate_request(kwargs)
            user_id = http.request.uid

            filter_set.append(('user_id','=',user_id))
            filter_set.append(('state','!=','draft'))
            if 'payment_state' in kwargs:
                filter_set.append(('payment_state','=',kwargs.get('payment_state')))

            invoices_total = http.request.env['account.move'].sudo().search_count(filter_set)

            if 'page' and 'page_size' in kwargs:
                page_size = kwargs.get('page_size')
                result = self.paginate(kwargs.get('page'),page_size,invoices_total)
                response['total_count'] = result.get('total_count')
                response['current_page'] = result.get('current_page')
                response['previous_page'] = result.get('previous_page')
                response['next_page'] = result.get('next_page')
                offset= result.get('offset')
            else:
                offset = 0
                page_size = invoices_total

            invoices = http.request.env['account.move'].sudo().search_read(filter_set,order="id desc",offset=offset,limit=page_size)

            for invoice in invoices:
                order_payment_method = http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('name','=',invoice.get('invoice_origin'))],fields=['payment_method'])
                invoice['payment_method'] = order_payment_method[0].get('payment_method')


            response['status'] = 200
            response['response'] = invoices
            response['message'] = 'success'
            return response

    @http.route('/api/invoices/<int:invoice_id>',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_invoice(self, invoice_id,**kwargs):
        validate_request(kwargs)
        user_id = http.request.uid
        invoice = http.request.env['account.move'].sudo().search_read([('id','=',invoice_id),('user_id','=',user_id),('state','!=','draft')],order="id desc")
        order_payment_method = http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('name','=',invoice[0].get('invoice_origin'))],fields=['payment_method'])
        invoice[0]['payment_method'] = order_payment_method[0].get('payment_method')
        if not invoice:
            raise NotFound('Not found')
        else:
            response = {'status':200,'response':invoice,'message':"success"}
            return response
        
        