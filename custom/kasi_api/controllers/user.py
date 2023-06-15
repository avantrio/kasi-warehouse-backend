from odoo.http import route, request, Controller
from .services import validate_request

class UserController(Controller):

    cors = "*"
        
    @route('/api/users/<int:id>/',auth='user',type='json',methods=['POST','OPTIONS'],cors=cors)
    def get_states(self, id,**kwargs):
        validate_request()
        townships = request.env['res.country.state'].sudo().search_read([("country_id","=?",id)])
        return townships