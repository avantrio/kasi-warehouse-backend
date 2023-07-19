
from odoo import http
from werkzeug.exceptions import MethodNotAllowed

import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type
from math import ceil

def validate_request(kwargs):
    if 'method' not in kwargs or kwargs.get('method') != 'GET':
        raise MethodNotAllowed()
    
def verify_mobile_number(number):
    return carrier._is_mobile(number_type(phonenumbers.parse(number)))
        
def paginate(page,page_size,total):
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
    