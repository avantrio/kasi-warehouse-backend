import logging

from odoo.http import route, request, Controller
from odoo import _,tools
from odoo.addons.auth_signup.controllers.main import AuthSignupHome 
from odoo.exceptions import UserError
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.auth_signup.models.res_partner import now
from odoo.exceptions import UserError
from odoo.addons.web.controllers.main import ensure_db, Home
from .services import validate_request, verify_mobile_number,send_sms,sa_number_validation

from base64 import b32encode
from random import randint
from datetime import timedelta, datetime


_logger = logging.getLogger(__name__)


SIGN_UP_REQUEST_PARAMS = {'login', 'password', 'confirm_password', 'new_password','first_name', 'last_name', 'name','email','company_name', 'business_type', 'company_registry', 'vat', 'address', 'location'}

class AuthController(Controller):
    cors = '*'
    @route('/api/session/authenticate/', type='json', auth="none", methods=['POST','OPTIONS'], cors=cors)
    def authenticate(self, login, password, base_location=None):
        try:
            login = sa_number_validation(login)
            db = request.env.cr.dbname
            request.session.authenticate(db, login, password)
            session_info = request.env['ir.http'].session_info()
            response = {'status':200,'response': session_info,'message':"success"}
        except Exception as e:
            _logger.error("%s", e)
            response = {'status':400,'response':{"error": _(e)},'message':"validation error"}
        return response

    @route('/api/session/check/', type='json', auth="user", methods=['POST','OPTIONS'], cors=cors)
    def check(self, *args, **kwargs):
        request.session.check_security()
        response = {'status':200,'response': None,'message':"success"}
        return response

    @route('/api/session/logout/', type='json', auth="user", methods=['POST','OPTIONS'], cors=cors)
    def logout(self, *args, **kwargs):
        request.session.logout()
        response = {'status':200,'response': None,'message':"success"}
        return response


    @route('/api/register/', type='json', auth="public", methods=['POST','OPTIONS'], cors=cors, website=True, sitemap=False)
    def register(self, *args, **kwargs):
        qcontext = self.get_auth_signup_qcontext()
        qcontext['login'] = sa_number_validation(qcontext['login'])
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)

            except UserError as e:
                qcontext['error'] = e.args[0]
                request.env.cr.rollback()
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered using this mobile number.")
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
    def send_token(self, mobile,*args, **kwargs):
        try:
            mobile = sa_number_validation(mobile)
            _logger.info("Mobile number: %s" % mobile)
            if not verify_mobile_number(mobile):
                raise UserError(_("Mobile number is wrong; please retry."))
            token = self._generate_token(4)
            request.env['mobile.verification'].sudo().create({
                'token': token,
                'mobile_number': mobile
            })
            _logger.info("SMS: %s" % token)
            send_sms(mobile,f'Your Kasi Warehouse verification code: {token}')
            response = {'status':200,'response':{},'message':"success"}
        except Exception as e:
            _logger.error("%s", e)
            response = {'status':400,'response':{"error": _(e)},'message':"validation error"}
        return response
    
    @route('/api/otp/', type='json', auth="public", methods=['PUT','OPTIONS'], cors=cors)
    def verify_token(self,mobile,token,*args, **kwargs):
        try:
            mobile = sa_number_validation(mobile)
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

    @route('/api/reset_password/', type='json', auth='public', methods=['POST','OPTIONS'], cors=cors)
    def web_auth_reset_password(self, *args, **kwargs):
        qcontext = self.get_auth_signup_qcontext()
        qcontext['login'] = sa_number_validation(qcontext['login'])

        if not qcontext.get('reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                login = qcontext.get('login')
                assert login, _("No login provided.")
                _logger.info(
                    "Password reset attempt for <%s> by user <%s> from %s",
                    login, request.env.user.login, request.httprequest.remote_addr)
                self.reset_password(login)
                qcontext['message'] = _("A SMS has been sent with credentials to reset your password")
            except UserError as e:
                qcontext['error'] = e.args[0]
            except SignupError:
                qcontext['error'] = _("Could not reset your password")
                _logger.exception('error when resetting password')
            except Exception as e:
                qcontext['error'] = str(e)
        if 'error' not in qcontext:
            response = {'status':200,'response':qcontext,'message':"success"}
        else:
            response = {'status':400,'response':{"error": qcontext['error']},'message':"validation error"}

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

    def reset_password(self, login):
        """ retrieve the user corresponding to login (login or mobile),
            and reset their password
        """
        users = request.env['res.users'].sudo().search([('login', '=', login)])
        if len(users) != 1:
            raise Exception(_('Reset password: invalid username'))
        return self.action_reset_password(users)

    def action_reset_password(self, users):
        """ create signup token for each user, and send their signup url by moblie """
        if request.env.context.get('install_mode', False):
            return
        if users.filtered(lambda u: not u.active):
            raise UserError(_("You cannot perform this action on an archived user."))
        # prepare reset password signup
        create_mode = bool(request.env.context.get('create_user'))

        # no time limit for initial invitation, only for reset password
        expiration = False if create_mode else now(days=+1)

        users.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)

        # send sms to users with their signup url
        for user in users:
            partner = user.partner_id
            url = partner.sudo()._get_signup_url_for_action()

            _logger.info("Reset password sms sent for user <%s>", user.login)
            _logger.info("Reset URL: %s", url[partner.id])
            send_sms(user.login,f'Your Kasi Warehouse password reset URL: {url[partner.id]}')


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
                    values['partner'].update({ key: address.get(key) for key in ('street', 'city', 'province','zip', 'landmark', 'township') })
                else:
                    location = qcontext.get(key)
                    values['partner']['partner_latitude'] = location["lat"]
                    values['partner']['partner_longitude'] = location["long"]
        if qcontext.get('first_name') or qcontext.get('last_name'): 
            values['user']['name'] = self._get_name(qcontext.get('first_name'), qcontext.get('last_name'))

        if not values and (('login', 'password', 'company_name') not in values or ('location' or 'address') not in values):
            raise UserError(_("The form was not properly filled in."))
        if values['user'].get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        if values['user'].get('login') and not verify_mobile_number(values['user'].get('login')):
            raise UserError(_("Mobile number is wrong; please retry."))

        if qcontext.get('login'):
            verification_obj = request.env['mobile.verification'].sudo().search([('mobile_number', '=', qcontext.get('login')),('mobile_verified','=', True)], limit=1)
            if not verification_obj:
                raise UserError(_("Mobile number not verified"))
            
        return values

    def _signup_with_values(self, token, values):
        db = request.env.cr.dbname
        company = request.env['res.company'].sudo().create(values['company'])
        user = request.env['res.users'].sudo().create(values['user'])
        user.write({
            'business_id': company.id
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