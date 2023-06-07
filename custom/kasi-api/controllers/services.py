
from odoo import http
from werkzeug.exceptions import MethodNotAllowed

def validate_request(kwargs):
    if 'method' not in kwargs or kwargs.get('method') != 'GET':
        raise MethodNotAllowed()
    
        