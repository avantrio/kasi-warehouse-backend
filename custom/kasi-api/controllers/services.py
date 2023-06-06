
from odoo import http
from werkzeug.exceptions import MethodNotAllowed

def validate_request():
        header = http.request.httprequest.headers.environ
        if header.get('HTTP_CUSTOM_REQUEST_METHOD') != 'GET':
            raise MethodNotAllowed()
        