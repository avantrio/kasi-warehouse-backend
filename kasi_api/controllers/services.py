
from odoo import http
from werkzeug.exceptions import MethodNotAllowed
import requests
import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type
from math import ceil
import re
import logging
_logger = logging.getLogger(__name__)



ADMIN_USERNAME = ''
ADMIN_PASSWORD = ''

def validate_request(kwargs):
    if 'method' not in kwargs or kwargs.get('method') != 'GET':
        raise MethodNotAllowed()
    
def verify_mobile_number(number):
    pattern = r"^\+?\d+$"
    if bool(re.match(pattern, number)):
        return carrier._is_mobile(number_type(phonenumbers.parse(number)))
    else:
        return False
        
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

def send_sms(to,body):
    try:
        r = requests.get(f'https://{ADMIN_USERNAME}:{ADMIN_PASSWORD}@smsgw3.gsm.co.za/xml/send/?number={to}&message={body}')
        r.raise_for_status()
        _logger.error("SMS sent status" + str(r))
        _logger.error("SMS sent " + str(r.content))
    except Exception as err:
        _logger.error("SMS sent failed" + str(err))