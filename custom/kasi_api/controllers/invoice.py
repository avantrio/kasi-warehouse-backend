from odoo import http
from .services import validate_request
from werkzeug.exceptions import NotFound

class InvoiceController(http.Controller):

    cors = "*"

    @http.route('/api/invoices',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def order(self, **kwargs):
        print("came")
        if kwargs.get('method') == 'GET':
            validate_request(kwargs)
            user_id = http.request.uid
            invoices = http.request.env['account.move'].sudo().search_read([('user_id','=',user_id),('state','!=','draft')],order="id desc")
            response = {'status':200,'response':invoices,'message':"success"}
            return response
        
    @http.route('/api/invoices/<int:invoice_id>',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_order(self, invoice_id,**kwargs):
        validate_request(kwargs)
        user_id = http.request.uid
        invoice = http.request.env['account.move'].sudo().search_read([('id','=',invoice_id),('user_id','=',user_id),('state','!=','draft')],order="id desc")
        if not invoice:
            raise NotFound('Not found')
        else:
            response = {'status':200,'response':invoice,'message':"success"}
            return response
        
        