
from odoo import http
from werkzeug.exceptions import MethodNotAllowed

import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type
from math import ceil
import re
from twilio.rest import Client
import os
import logging
_logger = logging.getLogger(__name__)


ACCOUNT_SID = 'ACCOUNT_SID'
AUTH_TOKEN =  'AUTH_TOKEN'
FROM_NUMBER = 'FROM_NUMBER'

client = Client(ACCOUNT_SID, AUTH_TOKEN)

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
        message = client.messages \
        .create(
            body=body,
            from_=FROM_NUMBER,
            to=to
        )
        _logger.info("SMS sent successfully: %s" % message.sid)
    except Exception as e:
        _logger.error("SMS sent failed" + str(e))
        _logger.error("SMS sent failed")

    