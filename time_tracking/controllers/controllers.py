# -*- coding: utf-8 -*-
# from odoo import http


# class TimeTracking(http.Controller):
#     @http.route('/time_tracking/time_tracking', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/time_tracking/time_tracking/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('time_tracking.listing', {
#             'root': '/time_tracking/time_tracking',
#             'objects': http.request.env['time_tracking.time_tracking'].search([]),
#         })

#     @http.route('/time_tracking/time_tracking/objects/<model("time_tracking.time_tracking"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('time_tracking.object', {
#             'object': obj
#         })

