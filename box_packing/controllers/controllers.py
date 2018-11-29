# -*- coding: utf-8 -*-
from odoo import http

# class BoxPacking(http.Controller):
#     @http.route('/box_packing/box_packing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/box_packing/box_packing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('box_packing.listing', {
#             'root': '/box_packing/box_packing',
#             'objects': http.request.env['box_packing.box_packing'].search([]),
#         })

#     @http.route('/box_packing/box_packing/objects/<model("box_packing.box_packing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('box_packing.object', {
#             'object': obj
#         })