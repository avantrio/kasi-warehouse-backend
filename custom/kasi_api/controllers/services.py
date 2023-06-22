
from odoo import http
from werkzeug.exceptions import MethodNotAllowed

import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type

def validate_request(kwargs):
    if 'method' not in kwargs or kwargs.get('method') != 'GET':
        raise MethodNotAllowed()
    
def verify_mobile_number(number):
    return carrier._is_mobile(number_type(phonenumbers.parse(number)))
        