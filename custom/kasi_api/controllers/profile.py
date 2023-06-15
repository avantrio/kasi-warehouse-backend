import logging

from odoo.http import route, request, Controller
from .services import validate_request
from .auth import SIGN_UP_REQUEST_PARAMS, AuthController
from odoo import _

_logger = logging.getLogger(__name__)


class ProfileController(Controller):

    cors = "*"

    @route('/api/profile/me/', type='json', auth="public", methods=['POST','OPTIONS'], cors=cors)
    def me(self,*args, **kwargs):
        validate_request(kwargs)
        session_info = request.env['ir.http'].session_info()
        user = request.env['res.users'].sudo().search([('id', '=', session_info['uid'])])
        response = {'status':200,'response': user.read(),'message':"success"}
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
            response = {'status':200,'response':profile.read(),'message':"success"}
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
                values['company'][key] = qcontext.get(key)
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

    def _update_profile(self, values):
        session_info = request.env['ir.http'].session_info()
        user = request.env['res.users'].sudo().search([('id', '=', session_info['uid'])])
        company = user.company_id
        partner = company.partner_id
        self._update_obj(values['user'], user)
        self._update_obj(values['company'], company)
        self._update_obj(values['partner'], partner)
        return user

    
    def _update_obj(self, values, obj):
        obj.write(values)

    
        