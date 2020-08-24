from openerp import fields, models, api

class staff_claim_payments(models.TransientModel):
    _name = 'cash.management.staff.claim.payments'

    name = fields.Many2one('res.partner', required = True)
    amount = fields.Float(required = True)
    paying_bank = fields.Many2one('res.bank', required = True)
    date = fields.Date(default = fields.Date.today, required = True)
    payment_reference = fields.Char()
    claim_id = fields.Many2one('cash.management.staff.claim')

    @api.one
    def action_post(self):
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])
        if setup.staff_claims_payable_account.id == False:
            raise Validationerror('\'Staff Claims Payable Account\' field must have a value in General Setup!')
        else:
            dr = setup.staff_claims_payable_account.id

        if self.payment_reference == '': #or self.payment_reference == None:
            self.payment_reference == 'Claim by' + self.name.name
        payment = self.env['cash.management.payment.header'].create({
            'date':self.date, 
            'paying_bank':self.paying_bank.id,
            'payment_to':self.name.name, 
            'on_behalf_of':self.name.name, 
            'payment_narration':self.payment_reference, 
            'claim_id':self.claim_id.id,
            'partner':self.name.id,
            'name':False
            })
        # payment.get_sequence()#number series
        #Create lines to represent debit entry to pay creditor
        self.env['cash.management.payment.lines'].create({
            'header_id':payment.id, 
            'account_id':dr,
            'description':'%s Payment for %s' %(self.payment_reference, self.claim_id.purpose), 
            'amount':self.amount
            })
        payment.signal_workflow('send_for_posting')
        self.claim_id.compute_totals()