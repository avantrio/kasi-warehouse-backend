import logging

from odoo.http import route, request, Controller
from .services import validate_request, verify_mobile_number
from .auth import SIGN_UP_REQUEST_PARAMS, AuthController
from odoo import _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
from odoo.addons.web.controllers.main import ensure_db

_logger = logging.getLogger(__name__)


class ProfileController(Controller):

    cors = "*"

    @route('/api/profile/me/', type='json', auth="user", methods=['POST','OPTIONS'], cors=cors)
    def me(self,*args, **kwargs):
        validate_request(kwargs)
        session_info = request.env['ir.http'].session_info()
        user = request.env['res.users'].sudo().search_read([('id', '=', session_info['uid'])])
        partner = request.env['res.partner'].sudo().search_read([('id', '=', user[0].get('partner_id')[0])])
        profile_dict = user[0]
        profile_dict['address'] = self._get_partner_address(partner[0])
        profile_dict['location'] = self._get_partner_location(partner[0])
        response = {'status':200,'response': profile_dict,'message':"success"}
        return response

    @route('/api/profile/me/',auth='user',type='json',methods=['PUT','OPTIONS'],cors=cors)
    def update_profile(self,**kwargs):
        qcontext = AuthController().get_auth_signup_qcontext()

        if 'error' not in qcontext and request.httprequest.method == 'PUT':
            try: 
                values = self._prepare_profile_update_values(qcontext)
                profile = self._update_profile(values)
            except Exception as e:
                _logger.error("%s", e)
                qcontext['error'] = _(e)
                request.env.cr.rollback()
        
        if 'error' not in qcontext:
            user = request.env['res.users'].sudo().search_read([('id', '=', profile.id)])
            response = {'status':200,'response':user,'message':"success"}
        else:
            response = {'status':400,'response':{"error": qcontext['error']},'message':"validation error"}
        return response

    @route('/api/profile/me/login/',auth='user',type='json',methods=['PUT','OPTIONS'],cors=cors)
    def update_login(self,**kwargs):
        qcontext = AuthController().get_auth_signup_qcontext()

        if 'error' not in qcontext and request.httprequest.method == 'PUT':
            try: 
                session_info = request.env['ir.http'].session_info()
                user = request.env['res.users'].sudo().search([('id', '=', session_info['uid'])])
                values = self._prepare_login_update_values(qcontext)
                db = request.env.cr.dbname   
                self._auth_user(db, user.login, values['password'])
                self._update_obj(values, user)
                request.env.cr.commit() 
                self._auth_user(db, values['login'], values['password'])
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
            user = request.env['res.users'].sudo().search_read([('id', '=', user.id)])
            response = {'status':200,'response':user,'message':"success"}
        else:
            response = {'status':400,'response':{"error": qcontext['error']},'message':"validation error"}
        return response

    @route('/api/profile/me/password/',auth='user',type='json',methods=['PUT','OPTIONS'],cors=cors)
    def update_password(self,**kwargs):
        qcontext = AuthController().get_auth_signup_qcontext()

        if 'error' not in qcontext and request.httprequest.method == 'PUT':
            try: 
                session_info = request.env['ir.http'].session_info()
                user = request.env['res.users'].sudo().search([('id', '=', session_info['uid'])])
                db = request.env.cr.dbname
                self._auth_user(db, user.login, qcontext['password'])
                values = self._prepare_password_update_values(qcontext)
                self._update_obj(values, user)
                request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
                self._auth_user(db, user.login, qcontext['new_password'])
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
            user = request.env['res.users'].sudo().search_read([('id', '=', user.id)])
            response = {'status':200,'response':user,'message':"success"}
        else:
            response = {'status':400,'response':{"error": qcontext['error']},'message':"validation error"}
        return response

    def _prepare_profile_update_values(self, qcontext):
        values = {
            "user": {},
            "company": {},
            "partner": {}
        }

        for key in qcontext.keys():
            if key in ('business_type', 'company_registry', 'vat'):
                if key=='company_registry':
                    values['company']['business_registration_number'] = qcontext.get(key)
                else:
                    values['partner'][key] = qcontext.get(key)
            elif key in ('email'):
                values['user'][key] = qcontext.get(key)
            elif key in ('address', 'location'):
                if key=='address':
                    address = qcontext.get(key)
                    values['partner'].update({ key: address.get(key) for key in ('street', 'city', 'province', 'zip', 'landmark', 'township') if address.get(key) })
                else:
                    location = qcontext.get(key)
                    values['partner']['partner_latitude'] = location["lat"]
                    values['partner']['partner_longitude'] = location["long"]
        if qcontext.get('name'):
            values['user']['name'] = qcontext.get('name')

        return values

    def _prepare_login_update_values(self, qcontext):
        values={}
        values['login'] = qcontext.get('login')
        values['password'] = qcontext.get('password')
        values['mobile'] = qcontext.get('login')
        if not values and ('login', 'password') not in values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('login') and not verify_mobile_number(values.get('login')):
            raise UserError(_("Mobile number is wrong; please retry."))

        if qcontext.get('login'):
            verification_obj = request.env['mobile.verification'].sudo().search([('mobile_number', '=', qcontext.get('login')),('mobile_verified','=', True)], limit=1)
            if not verification_obj:
                raise UserError(_("Mobile number not verified"))
        return values

    def _prepare_password_update_values(self, qcontext):
        values={}
        values['password'] = qcontext.get('new_password')
        if not values and ('password') not in values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        return values

    def _update_profile(self, values):
        session_info = request.env['ir.http'].session_info()
        user = request.env['res.users'].sudo().search([('id', '=', session_info['uid'])])
        partner = request.env['res.partner'].sudo().search([('user_id', '=', session_info['uid'])])
        self._update_obj(values['user'], user)
        self._update_obj(values['partner'], partner)
        return user

    
    def _update_obj(self, values, obj):
        obj.write(values)

    def _auth_user(self, db, login, password):
        uid = request.session.authenticate(db, login, password)
        if not uid:
            raise SignupError(_('Authentication Failed.'))
        return uid

    def _get_partner_address(self, partner):
        address = {
            "street": partner.get('street',None),
            "city": partner.get('city',None), 
            "province": partner.get('province',None),
            "zip": partner.get('zip',None),
            "landmark": partner.get('landmark',None),
            "township": partner.get('township',None)
        }
        print(partner.get('street',None))
        return address
    
    def _get_partner_location(self, partner):
        location = {
            "lat": partner.get('partner_latitude',None),
            "long": partner.get('partner_longitude',None)
        }
        return location
    