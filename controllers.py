# -*- coding: utf-8 -*-
from openerp import http

# class CashManagement(http.Controller):
#     @http.route('/cash_management/cash_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cash_management/cash_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cash_management.listing', {
#             'root': '/cash_management/cash_management',
#             'objects': http.request.env['cash_management.cash_management'].search([]),
#         })

#     @http.route('/cash_management/cash_management/objects/<model("cash_management.cash_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cash_management.object', {
#             'object': obj
#         })