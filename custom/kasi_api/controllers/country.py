from odoo.http import route, request, Controller
from .services import validate_request


class CountryController(Controller):

    cors = "*"

    @route('/api/countries/',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_countries(self, **kwargs):
        validate_request(kwargs)
        townships = request.env['res.country'].sudo().search_read([])
        return townships
        
    @route('/api/countries/<int:id>/states',auth='public',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_states(self, id,**kwargs):
        validate_request(kwargs)
        states = request.env['res.country.state'].sudo().search_read([("country_id","=?",id)])
        return states