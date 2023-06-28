from odoo import http
from .services import validate_request
from werkzeug.exceptions import NotFound

class InvoiceController(http.Controller):

    cors = "*"

    @http.route('/api/invoices',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def invoice(self, **kwargs):
        if kwargs.get('method') == 'GET':
            validate_request(kwargs)
            user_id = http.request.uid
            invoices = http.request.env['account.move'].sudo().search_read([('user_id','=',user_id),('state','!=','draft')],order="id desc")
            for invoice in invoices:
                order_payment_method = http.request.env['sale.order'].sudo().search_read([('user_id','=',user_id),('name','=',invoice.get('invoice_origin'))],fields=['payment_method'])
                invoice['payment_method'] = order_payment_method[0].get('payment_method')
            response = {'status':200,'response':invoices,'message':"success"}
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
        
        