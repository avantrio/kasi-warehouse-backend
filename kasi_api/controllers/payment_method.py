from odoo import http
from .services import validate_request

class PaymentMethodController(http.Controller):

    cors = "*"

    @http.route('/api/payment-methods/',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def payment_methods(self, **kwargs):
        if kwargs.get('method') == 'GET':
            validate_request(kwargs)
            payment_methods = {
                'CASH':'Cash',
                'SHOP_TO_SHOP':'Shop to Shop',
                'BANK_DEPOSIT':'Cash deposit in Bank',
                'EFT':'EFT'
            }
            response = {'status':200,'response':payment_methods,'message':"success"}
            return response
        
    