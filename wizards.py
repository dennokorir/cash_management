from openerp import fields, models, api

class staff_claim_payments(models.TransientModel):
    _name = 'cash.management.staff.claim.payments'

    name = fields.Many2one('res.partner', required = True)
    amount = fields.Float(required = True)
    paying_bank = fields.Many2one('res.bank', required = True)
    date = fields.Date(default = fields.Date.today, required = True)
    payment_reference = fields.Char()
    claim = fields.Many2one('cash.management.staff.claim')

    @api.one
    def action_post(self):
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])
        dr = setup.staff_claims_payable_account.id

        if self.payment_reference == '': #or self.payment_reference == None:
            self.payment_reference == 'Claim by' + self.name.name
        payment = self.env['cash.management.payment.header'].create({'date':self.date, 'paying_bank':self.paying_bank.id,
            'payment_to':self.name.name, 'on_behalf_of':self.name.name, 'payment_narration':self.payment_reference, 'posted':True, 'claim_id':self.claim.id,
            'partner':self.name.id})
        payment.get_sequence()#number series
        #Create lines to represent debit entry to pay creditor
        self.env['cash.management.payment.lines'].create({'header_id':payment.id, 'account_name':dr,
                'description':'Claim Payment', 'amount':self.amount})
        payment.action_post()
        if self.claim.balance <= 0 and self.claim.posted == True:
            self.claim.state = 'claimed'

