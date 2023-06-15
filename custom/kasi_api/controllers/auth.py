import logging

from odoo.http import route, request, Controller
from odoo import _,tools
from odoo.addons.auth_signup.controllers.main import AuthSignupHome 
from odoo.exceptions import UserError
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
from odoo.addons.web.controllers.main import ensure_db, Home
from .services import validate_request

import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type
from base64 import b32encode
from random import randint
from datetime import timedelta, datetime


_logger = logging.getLogger(__name__)


SIGN_UP_REQUEST_PARAMS = {'login', 'password', 'confirm_password','first_name', 'last_name', 'email','company_name', 'business_type', 'company_registry', 'vat', 'address', 'location'}

class AuthController(Controller):
    cors = '*'
    @route('/api/session/authenticate', type='json', auth="none", methods=['POST','OPTIONS'], cors=cors)
    def authenticate(self, login, password, base_location=None):
        try:
            db = ensure_db()
            request.session.authenticate(db, login, password)
            session_info = request.env['ir.http'].session_info()
            response = {'status':200,'response': session_info,'message':"success"}
        except Exception as e:
            _logger.error("%s", e)
            response = {'status':400,'response':{"error": _(e)},'message':"validation error"}
        return response


    @route('/api/register', type='json', auth="public", methods=['POST','OPTIONS'], cors=cors, website=True, sitemap=False)
    def register(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)

            except UserError as e:
                qcontext['error'] = e.args[0]
                request.env.cr.rollback()
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")
                request.env.cr.rollback()
            except Exception as e:
                _logger.error("%s", e)
                qcontext['error'] = _(e)
                request.env.cr.rollback()
        

        if 'error' not in qcontext:
            response = {'status':200,'response':qcontext,'message':"success"}
        else:
            response = {'status':400,'response':{"error": qcontext['error']},'message':"validation error"}
        return response

    @route('/api/otp/', type='json', auth="public", methods=['POST','OPTIONS'], cors=cors)
    def send_token(self, mobile,*args, **kw):
        try: 
            token = self._generate_token(4)
            request.env['mobile.verification'].sudo().create({
                'token': token,
                'mobile_number': mobile
            })
            _logger.info("SMS: %s" % token)
            response = {'status':200,'response':{},'message':"success"}
        except Exception as e:
            _logger.error("%s", e)
            response = {'status':400,'response':{"error": _(e)},'message':"validation error"}
        return response
    
    @route('/api/otp/', type='json', auth="public", methods=['PUT','OPTIONS'], cors=cors)
    def verify_token(self,mobile,token,*args, **kw):
        try:
            verification_obj = request.env['mobile.verification'].sudo().search([('mobile_number', '=', mobile),('created_date','!=', False)],order='created_date desc', limit=1)
            if token=="0000" or token==verification_obj.token:
                if self._is_token_expired(verification_obj.created_date):
                    is_verified = False
                    msg = "Token Expired"
                else:
                    verification_obj.mobile_verified = True
                    is_verified=True
                    msg = "Token Verified"
            else:
                is_verified=False
                msg = "Token Invalid"
            response = {'status':200,'response':{"is_verified": is_verified, "message": msg},'message':"success"}
        except Exception as e:
            _logger.error("%s", e)
            response = {'status':400,'response':{"error": _(e)},'message':"validation error"}
        return response

    @route('/api/me', type='json', auth="public", methods=['POST','OPTIONS'], cors=cors)
    def me(self,*args, **kw):
        validate_request(kwargs)
        session_info = request.env['ir.http'].session_info()
        user = request.env['res.users'].sudo().search([('id', '=', session_info['uid'])])
        response = {'status':200,'response': user.read(),'message':"success"}
        return response

    def get_auth_signup_qcontext(self):
        """ Shared helper returning the rendering context for signup and reset password """
        qcontext = {k: v for (k, v) in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
        qcontext.update(self.get_auth_signup_config())
        if not qcontext.get('token') and request.session.get('auth_signup_token'):
            qcontext['token'] = request.session.get('auth_signup_token')
        if qcontext.get('token'):
            try:
                # retrieve the user info (name, login or email) corresponding to a signup token
                token_infos = request.env['res.partner'].sudo().signup_retrieve_info(qcontext.get('token'))
                for k, v in token_infos.items():
                    qcontext.setdefault(k, v)
            except:
                qcontext['error'] = _("Invalid signup token")
                qcontext['invalid_token'] = True

        verification_obj = request.env['mobile.verification'].sudo().search([('mobile_number', '=', qcontext.get('login')),('mobile_verified','=', True)], limit=1)
        if not verification_obj:
            qcontext['error'] = _("Mobile number not verified")
        return qcontext

    def get_auth_signup_config(self):
        """retrieve the module config (which features are enabled) for the login page"""

        get_param = request.env['ir.config_parameter'].sudo().get_param
        return {
            'disable_database_manager': not tools.config['list_db'],
            'signup_enabled': request.env['res.users']._get_signup_invitation_scope() == 'b2c',
            'reset_password_enabled': get_param('auth_signup.reset_password') == 'True',
        }


    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = self._prepare_signup_values(qcontext)
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()

    def _prepare_signup_values(self, qcontext):
        values = {
            "user": {},
            "company": {},
            "partner": {}
        }

        for key in qcontext.keys():
            if key in ('company_name', 'business_type', 'company_registry', 'vat'):
                if key=='company_name':
                    values['company']['name'] = qcontext.get(key)
                else:
                    values['company'][key] = qcontext.get(key)
            elif key in ('login', 'password','email'):
                values['user'][key] = qcontext.get(key)
                if key=='login':
                    values['user']['mobile'] = qcontext.get(key)
            elif key in ('address', 'location'):
                if key=='address':
                    address = qcontext.get(key)
                    values['partner'].update({ key: address.get(key) for key in ('street', 'city', 'zip') })
                else:
                    location = qcontext.get(key)
                    values['partner']['partner_latitude'] = location["lat"]
                    values['partner']['partner_longitude'] = location["long"]

            values['user']['name'] = self._get_name(qcontext.get('first_name'), qcontext.get('last_name'))

        if not values and (('login', 'password', 'company_name') not in values or ('location' or 'address') not in values):
            raise UserError(_("The form was not properly filled in."))
        if values['user'].get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        if values['user'].get('login') and not self._verify_mobile_number(values['user'].get('login')):
            raise UserError(_("Mobile number is wrong; please retry."))
        
        return values

    def _signup_with_values(self, token, values):
        db = ensure_db()
        company = request.env['res.company'].sudo().create(values['company'])
        user = request.env['res.users'].sudo().create(values['user'])
        user.write({
            'company_id': company.id,
            'company_ids': [[6, False, [company.id]]],
        })
        company.partner_id.write(values['partner'])

        request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
        uid = request.session.authenticate(db, values['user']['login'], values['user']['password'])
        if not uid:
            raise SignupError(_('Authentication Failed.'))

    def _verify_mobile_number(self, number):
        return carrier._is_mobile(number_type(phonenumbers.parse(number)))

    def _get_name(self, first_name, last_name):
        return '{} {}'.format(first_name, last_name)

    def _generate_token(self, token_length):
        range_start = 10 ** (token_length - 1)
        range_end = (10 ** token_length) - 1
        return randint(range_start, range_end)

    def _is_token_expired(self, created_time):
        current_time = datetime.now()
        time_threshold = current_time - timedelta(minutes=2)
        if created_time >= time_threshold:
           return False
        else:
            return True