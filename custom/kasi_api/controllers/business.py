from odoo.http import route, request, Controller
from .services import validate_request
from odoo.addons.kasi_api.models.business import Business

class BusinessController(Controller):

    cors = "*"
     
    @route('/api/business/types/',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_types(self,**kwargs):
        validate_request(kwargs)
        response = {'status':200,'response':Business.Types,'message':"success"}
        return response

    @route('/api/business/townships/',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_townships(self,**kwargs):
        validate_request(kwargs)
        response = {'status':200,'response':Business.Townships,'message':"success"}
        return response

    @route('/api/business/<int:id>/',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_buisness(self,id,**kwargs):
        validate_request(kwargs)
        business = request.env['res.company'].sudo().search_read([('id','=',id)])
        return business

    