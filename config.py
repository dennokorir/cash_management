from openerp import models, fields, api

class cash_management_settings(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'cash.management.settings'

    module_cash_management_approvals = fields.Boolean(string = 'Uses Approvals')
    module_approvals_cash_management = fields.Boolean(string = 'Uses Approvals')
