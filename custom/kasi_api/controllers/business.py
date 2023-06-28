from odoo.http import route, request, Controller
from .services import validate_request
from odoo.addons.kasi_api.models.business import Business
from odoo.addons.kasi_api.models.address import Address

class BusinessController(Controller):

    cors = "*"
     
    @route('/api/business/types/',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_types(self,**kwargs):
        validate_request(kwargs)
        response = {'status':200,'response':Business.Types,'message':"success"}
        return response

    @route('/api/business/<int:id>/',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_buisness(self,id,**kwargs):
        validate_request(kwargs)
        business = request.env['res.company'].sudo().search([('id','=',id)])
        partner = business.partner_id
        business_dict = business.read()[0]
        business_dict["address"] = self._get_partner_address(partner)
        business_dict["location"] = self._get_partner_location(partner)
        response = {'status':200,'response':business_dict,'message':"success"}
        return response

    def _get_partner_address(self, partner):
        address = {
            "street": partner.street,
            "city": partner.city, 
            "province": partner.province,
            "zip": partner.zip,
            "landmark": partner.landmark,
            "township": partner.township 
        }
        return address

    def _get_partner_location(self, partner):
        location = {
            "lat": partner.partner_latitude,
            "long": partner.partner_longitude
        }
        return location

    @route('/api/address/townships/',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_townships(self,**kwargs):
        validate_request(kwargs)
        response = {'status':200,'response':Address.Townships,'message':"success"}
        return response

    