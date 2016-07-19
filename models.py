from openerp import models, fields, api
from openerp.exceptions import ValidationError
from datetime import datetime

class payment_header(models.Model):
    _name = 'cash.management.payment.header'

    name = fields.Char(string = "No.")
    date = fields.Date()
    payment_method = fields.Selection([('cash',"Cash"),('cheque',"Cheque")], default = 'cash')
    cheque_no = fields.Char()
    paying_bank = fields.Many2one('res.bank')
    paying_account_no = fields.Char()
    payment_to = fields.Char()
    on_behalf_of = fields.Char()
    payment_narration = fields.Text()
    cashier = fields.Many2one('res.users', default = lambda self:self.env.user)
    state = fields.Selection([('open',"Open"),('pending',"Pending Approval"),('approved',"Approved")], default = 'open')
    posted = fields.Boolean(default = False)
    gross_amount = fields.Float()
    tax_amount = fields.Float()
    total_amount = fields.Float(compute = 'calculate_amounts')
    line_ids = fields.One2many('cash.management.payment.lines','header_id')
    dimension1 = fields.Many2one('dimension.values', domain = [('sequence','=',1)])
    dimension2 = fields.Many2one('dimension.values', domain = [('sequence','=',2)])
    dimension3 = fields.Many2one('dimension.values', domain = [('sequence','=',3)])
    dimension4 = fields.Many2one('dimension.values', domain = [('sequence','=',4)])

    @api.one
    @api.onchange('name')
    def get_sequence(self):
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])
        sequence = self.env['ir.sequence'].search([('id','=',setup.payment_voucher_numbers.id)])
        self.name = sequence.next_by_id(sequence.id, context = None)

    @api.onchange('paying_bank')
    def get_account(self):
        bank = self.env['res.partner.bank'].search([('bank','=',self.paying_bank.id)])
        self.paying_account_no = bank.acc_number

    @api.one
    @api.depends('line_ids')
    def calculate_amounts(self):
        self.gross_amount = sum(line.amount for line in self.line_ids)
        self.total_amount = sum(line.amount for line in self.line_ids)

    @api.one
    def action_post(self):
        #date
        today = datetime.now().strftime("%Y/%m/%d")
        #create journal header
        paying_bank = self.env['res.partner.bank'].search([('bank','=',self.paying_bank.id)])

        journal = self.env['account.journal'].search([('id','=',paying_bank.journal_id.id)]) #get journal id
        #period
        period = self.env['account.period'].search([('state','=','draft'),('date_start','<=',today),('date_stop','>=',today)])
        period_id = period.id

        journal_header = self.env['account.move']#reference to journal entry
        move = journal_header.create({'journal_id':journal.id,'period_id':period_id,'state':'draft','name':self.name,
            'date':today})
        move_id = move.id

        #create journal lines
        journal_lines = self.env['account.move.line']

        #dr = receiving_bank.journal_id.default_debit_account_id.id
        cr = paying_bank.journal_id.default_credit_account_id.id

        for line in self.line_ids:
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Payments::' + self.name,'account_id':line.account_name.id,'move_id':move_id,'debit':line.amount})
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Payments::' + self.name,'account_id':cr,'move_id':move_id,'credit':line.amount})

        self.posted = True



class payment_details(models.Model):
    _name = 'cash.management.payment.lines'

    header_id = fields.Many2one('cash.management.payment.header')
    payment_type = fields.Many2one('cash.management.receipts.and.payment.types', domain = [('transaction_type','=','payment')])
    account_no = fields.Char()
    account_name = fields.Many2one('account.account')
    description = fields.Char()
    tax = fields.Char()#consider using many2many field
    tax_amount = fields.Float()
    amount = fields.Float()

    @api.onchange('payment_type')
    def get_accounts(self):
        payment_type = self.env['cash.management.receipts.and.payment.types'].search([('id','=',self.payment_type.id)])
        self.account_name = payment_type.account_name
        self.description = payment_type.description

class petty_cash_header(models.Model):
    _name = 'cash.management.petty.cash.header'

    name = fields.Char(string = "No.")
    date = fields.Date()
    payment_method = fields.Selection([('cash',"Cash"),('cheque',"Cheque")], default = 'cash')
    cheque_no = fields.Char()
    paying_bank = fields.Many2one('res.bank')
    paying_account_no = fields.Char()
    payment_to = fields.Char()
    on_behalf_of = fields.Char()
    payment_narration = fields.Text()
    cashier = fields.Many2one('res.users', default = lambda self:self.env.user)
    state = fields.Selection([('draft',"draft"),('pending',"Pending Approval"),('approved',"Approved")], default = 'draft')
    posted = fields.Boolean(default = False)
    gross_amount = fields.Float()
    tax_amount = fields.Float()
    total_amount = fields.Float(compute = 'calculate_amounts')
    line_ids = fields.One2many('cash.management.petty.cash.lines','header_id')
    dimension1 = fields.Many2one('dimension.values', domain = [('sequence','=',1)])
    dimension2 = fields.Many2one('dimension.values', domain = [('sequence','=',2)])
    dimension3 = fields.Many2one('dimension.values', domain = [('sequence','=',3)])
    dimension4 = fields.Many2one('dimension.values', domain = [('sequence','=',4)])

    @api.one
    @api.onchange('name')
    def get_sequence(self):
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])
        sequence = self.env['ir.sequence'].search([('id','=',setup.petty_cash_voucher_numbers.id)])
        self.name = sequence.next_by_id(sequence.id, context = None)

    @api.onchange('paying_bank')
    def get_account(self):
        bank = self.env['res.partner.bank'].search([('bank','=',self.paying_bank.id)])
        self.paying_account_no = bank.acc_number

    @api.one
    @api.depends('line_ids')
    def calculate_amounts(self):
        self.gross_amount = sum(line.amount for line in self.line_ids)
        self.total_amount = sum(line.amount for line in self.line_ids)

    @api.one
    def action_post(self):
        #date
        today = datetime.now().strftime("%Y/%m/%d")
        #create journal header
        paying_bank = self.env['res.partner.bank'].search([('bank','=',self.paying_bank.id)])

        journal = self.env['account.journal'].search([('id','=',paying_bank.journal_id.id)]) #get journal id
        #period
        period = self.env['account.period'].search([('state','=','draft'),('date_start','<=',today),('date_stop','>=',today)])
        period_id = period.id

        journal_header = self.env['account.move']#reference to journal entry
        move = journal_header.create({'journal_id':journal.id,'period_id':period_id,'state':'draft','name':self.name,
            'date':today})
        move_id = move.id

        #create journal lines
        journal_lines = self.env['account.move.line']

        #dr = receiving_bank.journal_id.default_debit_account_id.id
        cr = paying_bank.journal_id.default_credit_account_id.id

        for line in self.line_ids:
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Petty Cash::' + self.name,'account_id':line.account_name.id,'move_id':move_id,'debit':line.amount})
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Petty Cash::' + self.name,'account_id':cr,'move_id':move_id,'credit':line.amount})

        self.posted = True
        self.state = 'approved'

    @api.one
    def request(self):
        self.state = 'pending'
        #requests = self.env['cash.management.petty.cash.header'].search([('state','=','draft')])
        return {'type':'ir.actions.act_window',
        'res_model':'cash.management.petty.cash.header',
        'view_type':'form',
        'view_mode':'tree',
        'target':'new',
        }


class petty_cash_details(models.Model):
    _name = 'cash.management.petty.cash.lines'

    header_id = fields.Many2one('cash.management.petty.cash.header')
    payment_type = fields.Many2one('cash.management.receipts.and.payment.types', domain = [('transaction_type','=','petty')])
    account_no = fields.Char()
    account_name = fields.Many2one('account.account')
    description = fields.Char()
    tax = fields.Char()#consider using many2many field
    tax_amount = fields.Float()
    amount = fields.Float()

    @api.onchange('payment_type')
    def get_accounts(self):
        payment_type = self.env['cash.management.receipts.and.payment.types'].search([('id','=',self.payment_type.id)])
        self.account_name = payment_type.account_name
        self.description = payment_type.description


class receipt_header(models.Model):
    _name = 'cash.management.receipt.header'

    name = fields.Char()
    date = fields.Date()
    receiving_bank = fields.Many2one('res.bank')
    receiving_account_no = fields.Char()
    received_from = fields.Char()
    cashier = fields.Many2one('res.users', default = lambda self:self.env.user)
    posted = fields.Boolean(default = False)
    remarks = fields.Text()
    gross_amount = fields.Float()
    tax_amount = fields.Float()
    total_amount = fields.Float(compute = 'sum_totals')
    state = fields.Selection([('draft',"Draft"),('received',"Recieved")], default = 'draft')
    line_ids = fields.One2many('cash.management.receipt.lines','header_id')
    dimension1 = fields.Many2one('dimension.values', domain = [('sequence','=',1)])
    dimension2 = fields.Many2one('dimension.values', domain = [('sequence','=',2)])
    dimension3 = fields.Many2one('dimension.values', domain = [('sequence','=',3)])
    dimension4 = fields.Many2one('dimension.values', domain = [('sequence','=',4)])

    @api.one
    @api.onchange('name')
    def get_sequence(self):
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])
        sequence = self.env['ir.sequence'].search([('id','=',setup.receipt_numbers.id)])
        self.name = sequence.next_by_id(sequence.id, context = None)

    @api.onchange('receiving_bank')
    def get_account(self):
        bank = self.env['res.partner.bank'].search([('bank','=',self.receiving_bank.id)])
        self.receiving_account_no = bank.acc_number

    @api.one
    def action_post(self):
        #date
        today = datetime.now().strftime("%Y/%m/%d")
        #create journal header
        receiving_bank = self.env['res.partner.bank'].search([('bank','=',self.receiving_bank.id)])

        journal = self.env['account.journal'].search([('id','=',receiving_bank.journal_id.id)]) #get journal id
        #period
        period = self.env['account.period'].search([('state','=','draft'),('date_start','<=',today),('date_stop','>=',today)])
        period_id = period.id

        journal_header = self.env['account.move']#reference to journal entry
        move = journal_header.create({'journal_id':journal.id,'period_id':period_id,'state':'draft','name':self.name,
            'date':today})
        move_id = move.id

        #create journal lines
        journal_lines = self.env['account.move.line']

        dr = receiving_bank.journal_id.default_debit_account_id.id
        #cr = paying_bank.journal_id.default_credit_account_id.id

        for line in self.line_ids:
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Cash/Bank Receipts::' + self.name,'account_id':dr,'move_id':move_id,'debit':line.amount})
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Cash/Bank Receipts::' + self.name,'account_id':line.account_name.id,'move_id':move_id,'credit':line.amount})

        self.posted = True

    @api.one
    @api.depends('line_ids')
    def sum_totals(self):
        self.total_amount = sum(line.amount for line in self.line_ids)


class receipt_details(models.Model):
    _name = 'cash.management.receipt.lines'

    header_id = fields.Many2one('cash.management.receipt.header')
    receipt_type = fields.Many2one('cash.management.receipts.and.payment.types', domain = [('transaction_type','=','receipt')])#
    account_no = fields.Many2one('account.account')
    account_name = fields.Many2one('account.account')
    description = fields.Char()
    amount = fields.Float()

    @api.onchange('receipt_type')
    def get_accounts(self):
        receipt_type = self.env['cash.management.receipts.and.payment.types'].search([('id','=',self.receipt_type.id)])
        self.account_name = receipt_type.account_name
        self.description = receipt_type.description

class bank_transfer_header(models.Model):
    _name = 'cash.management.bank.transfer.header'

    name = fields.Char(string = "No.")
    date = fields.Date()
    paying_bank = fields.Many2one('res.bank')
    paying_account_no = fields.Char()
    paying_account_balance = fields.Float()
    receiving_bank = fields.Many2one('res.bank')
    receiving_account_no = fields.Char()
    receiving_account_balance = fields.Float()
    state = fields.Selection([('draft',"Draft"),('ready',"Ready")], default = 'draft')
    posted = fields.Boolean()
    amount = fields.Float()
    remarks = fields.Text()
    dimension1 = fields.Many2one('dimension.values', domain = [('sequence','=',1)])
    dimension2 = fields.Many2one('dimension.values', domain = [('sequence','=',2)])
    dimension3 = fields.Many2one('dimension.values', domain = [('sequence','=',3)])
    dimension4 = fields.Many2one('dimension.values', domain = [('sequence','=',4)])

    @api.one
    @api.onchange('name')
    def get_sequence(self):
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])
        sequence = self.env['ir.sequence'].search([('id','=',setup.bank_transfer_numbers.id)])
        self.name = sequence.next_by_id(sequence.id, context = None)

    @api.onchange('paying_bank','receiving_bank')
    def get_account(self):
        paying_bank = self.env['res.partner.bank'].search([('bank','=',self.paying_bank.id)])
        self.paying_account_no = paying_bank.acc_number
        #get balance
        self.paying_account_balance = paying_bank.journal_id.default_debit_account_id.balance

        receiving_bank = self.env['res.partner.bank'].search([('bank','=',self.receiving_bank.id)])
        self.receiving_account_no = receiving_bank.acc_number
        self.receiving_account_balance = receiving_bank.journal_id.default_debit_account_id.balance

    @api.one
    def action_post(self):
        if self.paying_account_balance > self.amount:
            #date
            today = datetime.now().strftime("%Y/%m/%d")
            #setup = self.env['sacco.setup'].search([('id','=',1)])
            #create journal header
            receiving_bank = self.env['res.partner.bank'].search([('bank','=',self.receiving_bank.id)])
            paying_bank = self.env['res.partner.bank'].search([('bank','=',self.paying_bank.id)])

            journal = self.env['account.journal'].search([('id','=',paying_bank.journal_id.id)]) #get journal id
            #period
            #month = datetime.strptime(str(today),'%Y-%m-%d').date().month
            #year = datetime.strptime(str(today),'%Y-%m-%d').date().year
            period = self.env['account.period'].search([('state','=','draft'),('date_start','<=',today),('date_stop','>=',today)])
            period_id = period.id

            journal_header = self.env['account.move']#reference to journal entry


            move = journal_header.create({'journal_id':journal.id,'period_id':period_id,'state':'draft','name':self.name,
                'date':today})

            move_id = move.id

            #create journal lines

            journal_lines = self.env['account.move.line']

            dr = receiving_bank.journal_id.default_debit_account_id.id
            cr = paying_bank.journal_id.default_credit_account_id.id

            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Bank Transfer','account_id':dr,'move_id':move_id,'debit':self.amount})
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Bank Transfer','account_id':cr,'move_id':move_id,'credit':self.amount})

            self.posted = True
        else:
            raise ValidationError("Your transfer exceeds the Bank Balance")

    @api.one
    def confirm(self):
        self.state = 'ready'

    @api.one
    def reset(self):
        self.state = 'draft'

class staff_advance_header(models.Model):
    _name = 'cash.management.staff.advance.header'

    name = fields.Char()
    date = fields.Date()
    advance_to = fields.Many2one('res.partner')
    purpose = fields.Text()
    paying_bank = fields.Many2one('res.bank')


    paying_account_name = fields.Char()
    payment_method = fields.Selection([('cash',"Cash"),('cheque',"Cheque")])
    cheque_no = fields.Char()
    total_amount = fields.Float(compute = 'compute_totals')
    state = fields.Selection([('draft',"Draft"),('ready',"Ready")], default = 'draft')
    cashier = fields.Many2one('res.users', default = lambda self:self.env.user)
    posted = fields.Boolean()
    surrendered = fields.Boolean()
    line_ids = fields.One2many('cash.management.staff.advance.lines', 'header_id')
    dimension1 = fields.Many2one('dimension.values', domain = [('sequence','=',1)])
    dimension2 = fields.Many2one('dimension.values', domain = [('sequence','=',2)])
    dimension3 = fields.Many2one('dimension.values', domain = [('sequence','=',3)])
    dimension4 = fields.Many2one('dimension.values', domain = [('sequence','=',4)])

    @api.one
    @api.onchange('name')
    def get_sequence(self):
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])
        sequence = self.env['ir.sequence'].search([('id','=',setup.staff_advance_numbers.id)])
        self.name = sequence.next_by_id(sequence.id, context = None)

    @api.one
    def confirm(self):
        self.state = 'ready'

    @api.one
    def reset(self):
        self.state = 'draft'

    @api.one
    @api.depends('line_ids')
    def compute_totals(self):
        self.total_amount = sum(line.amount for line in self.line_ids)

    @api.one
    def action_post(self):
        #date
        today = datetime.now().strftime("%Y/%m/%d")
        #create journal header
        paying_bank = self.env['res.partner.bank'].search([('bank','=',self.paying_bank.id)])

        journal = self.env['account.journal'].search([('id','=',paying_bank.journal_id.id)]) #get journal id
        #period
        period = self.env['account.period'].search([('state','=','draft'),('date_start','<=',today),('date_stop','>=',today)])
        period_id = period.id

        journal_header = self.env['account.move']#reference to journal entry
        move = journal_header.create({'journal_id':journal.id,'period_id':period_id,'state':'draft','name':self.name,
            'date':today})
        move_id = move.id

        #create journal lines
        journal_lines = self.env['account.move.line']

        #setup
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])

        dr = setup.staff_advance_receivable_account.id
        cr = paying_bank.journal_id.default_credit_account_id.id

        for line in self.line_ids:
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Staff Advance::' + self.name,'account_id':dr,'move_id':move_id,'debit':line.amount,'partner_id':self.advance_to.id})
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Staff Advance::' + self.name,'account_id':cr,'move_id':move_id,'credit':line.amount,'partner_id':self.advance_to.id})

        self.posted = True

class staff_advance_lines(models.Model):
    _name = 'cash.management.staff.advance.lines'

    header_id = fields.Many2one('cash.management.staff.advance.header')
    advance_type = fields.Many2one('cash.management.receipts.and.payment.types', domain = [('transaction_type','=','staff')])
    account_no = fields.Many2one('account.account')
    account_name = fields.Many2one('account.account')
    description = fields.Char()
    amount = fields.Float()

    @api.onchange('advance_type')
    def get_accounts(self):
        advance_type = self.env['cash.management.receipts.and.payment.types'].search([('id','=',self.advance_type.id)])
        self.account_name = advance_type.account_name
        self.description = advance_type.description

class staff_advance_surrender_header(models.Model):
    _name = 'cash.management.staff.advance.surrender.header'

    name = fields.Char(string = 'No.')
    date = fields.Date()
    source_document = fields.Many2one('cash.management.staff.advance.header', domain = [('surrendered','=',False)])
    surrendered_by = fields.Many2one('res.partner')
    advanced_amount = fields.Float()
    actual_spent = fields.Float()
    balance = fields.Float()
    cashier = fields.Many2one('res.users', default = lambda self:self.env.user)
    state = fields.Selection([('draft',"Draft"),('ready',"Ready"),('open',"Open"),('surrendered',"Surrendered")], default = 'draft')
    remarks = fields.Text()
    posted = fields.Boolean()
    line_ids = fields.One2many('cash.management.staff.advance.surrender.lines', 'header_id')
    dimension1 = fields.Many2one('dimension.values', domain = [('sequence','=',1)])
    dimension2 = fields.Many2one('dimension.values', domain = [('sequence','=',2)])
    dimension3 = fields.Many2one('dimension.values', domain = [('sequence','=',3)])
    dimension4 = fields.Many2one('dimension.values', domain = [('sequence','=',4)])

    @api.one
    @api.onchange('name')
    def get_sequence(self):
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])
        sequence = self.env['ir.sequence'].search([('id','=',setup.staff_advance_surrender_numbers.id)])
        self.name = sequence.next_by_id(sequence.id, context = None)

    @api.onchange('source_document')
    def get_advance_details(self):
        self.surrendered_by = self.source_document.advance_to.id
        self.advanced_amount = self.source_document.total_amount
        #self.remarks = self.name
        #self.remarks = self.env['cash.management.staff.advance.surrender.header'].search([('name','=',self.name)]).id

    @api.one
    def get_advance_lines(self):
        if not self.source_document:
            raise ValidationError('Source document must have a value before getting lines')
        #populate lines
        self.line_ids.unlink()
        for line in self.source_document.line_ids:
            self.env['cash.management.staff.advance.surrender.lines'].create({'header_id':self.id,'advance_type':line.advance_type.id,
                'account_name':line.account_name.id,'description':line.description,'amount_advanced':line.amount})

    @api.onchange('actual_spent')
    def compute_balance(self):
        if self.advanced_amount > 0:
            self.balance = self.advanced_amount - self.actual_spent

    @api.one
    def confirm(self):
        self.state = 'ready'

    @api.one
    def reset(self):
        self.state = 'draft'

    @api.one
    def action_post(self):
        #date
        today = datetime.now().strftime("%Y/%m/%d")
        #create journal header
        paying_bank = self.env['res.partner.bank'].search([('bank','=',self.source_document.paying_bank.id)])

        journal = self.env['account.journal'].search([('id','=',paying_bank.journal_id.id)]) #get journal id
        #period
        period = self.env['account.period'].search([('state','=','draft'),('date_start','<=',today),('date_stop','>=',today)])
        period_id = period.id

        journal_header = self.env['account.move']#reference to journal entry
        move = journal_header.create({'journal_id':journal.id,'period_id':period_id,'state':'draft','name':self.name,
            'date':today})
        move_id = move.id

        #create journal lines
        journal_lines = self.env['account.move.line']

        #setup
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])

        #dr = self.source_document.line_ids.account_name.id
        cr = setup.staff_advance_receivable_account.id #paying_bank.journal_id.default_credit_account_id.id

        for line in self.line_ids:
            dr = line.account_name.id
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Staff Advance Surrender::' + self.name,'account_id':dr,'move_id':move_id,'debit':line.actual_spent,'partner_id':self.surrendered_by.id})
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Staff Advance Surrender::' + self.name,'account_id':cr,'move_id':move_id,'credit':line.actual_spent,'partner_id':self.surrendered_by.id})

        self.posted = True
        self.source_document.surrendered = True


    @api.one
    def action_create_draft_receipt(self):
        pass

    @api.one
    def action_create_draft_payment(self):
        pass


class staff_advance_surrender_lines(models.Model):
    _name = 'cash.management.staff.advance.surrender.lines'

    header_id = fields.Many2one('cash.management.staff.advance.surrender.header')
    advance_type = fields.Many2one('cash.management.receipts.and.payment.types', domain = [('transaction_type','=','staff')])
    account_name = fields.Many2one('account.account')
    description = fields.Char()
    amount_advanced = fields.Float()
    actual_spent = fields.Float()
    balance = fields.Float()

    @api.onchange('actual_spent')
    def get_balance(self):
        self.balance = self.amount_advanced - self.actual_spent

class travel_advance_header(models.Model):
    _name = 'cash.management.travel.advance.header'

    name = fields.Char(string = 'No.')
    date = fields.Date()
    advance_to = fields.Many2one('res.partner')
    purpose = fields.Text()
    paying_bank = fields.Many2one('res.bank')
    paying_account_name = fields.Char()
    payment_method = fields.Selection([('cash',"Cash"),('cheque',"Cheque")])
    cheque_no = fields.Char()
    total_amount = fields.Float(compute = 'compute_totals')
    state = fields.Selection([('draft',"Draft"),('ready',"Ready")], default = 'draft')
    cashier = fields.Many2one('res.users', default = lambda self:self.env.user)
    posted = fields.Boolean()
    surrendered = fields.Boolean()
    line_ids = fields.One2many('cash.management.travel.advance.lines', 'header_id')
    dimension1 = fields.Many2one('dimension.values', domain = [('sequence','=',1)])
    dimension2 = fields.Many2one('dimension.values', domain = [('sequence','=',2)])
    dimension3 = fields.Many2one('dimension.values', domain = [('sequence','=',3)])
    dimension4 = fields.Many2one('dimension.values', domain = [('sequence','=',4)])

    @api.one
    @api.onchange('name')
    def get_sequence(self):
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])
        sequence = self.env['ir.sequence'].search([('id','=',setup.travel_advance_numbers.id)])
        self.name = sequence.next_by_id(sequence.id, context = None)

    @api.one
    def confirm(self):
        self.state = 'ready'

    @api.one
    def reset(self):
        self.state = 'draft'

    @api.one
    @api.depends('line_ids')
    def compute_totals(self):
        self.total_amount = sum(line.amount for line in self.line_ids)

    @api.one
    def action_post(self):
        #date
        today = datetime.now().strftime("%Y/%m/%d")
        #create journal header
        paying_bank = self.env['res.partner.bank'].search([('bank','=',self.paying_bank.id)])

        journal = self.env['account.journal'].search([('id','=',paying_bank.journal_id.id)]) #get journal id
        #period
        period = self.env['account.period'].search([('state','=','draft'),('date_start','<=',today),('date_stop','>=',today)])
        period_id = period.id

        journal_header = self.env['account.move']#reference to journal entry
        move = journal_header.create({'journal_id':journal.id,'period_id':period_id,'state':'draft','name':self.name,
            'date':today})
        move_id = move.id

        #create journal lines
        journal_lines = self.env['account.move.line']

        #setup
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])

        dr = setup.staff_travel_receivable_account.id
        cr = paying_bank.journal_id.default_credit_account_id.id

        for line in self.line_ids:
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Staff Advance::' + self.name,'account_id':dr,'move_id':move_id,'debit':line.amount,'partner_id':self.advance_to.id})
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Staff Advance::' + self.name,'account_id':cr,'move_id':move_id,'credit':line.amount,'partner_id':self.advance_to.id})

        self.posted = True

class travel_advance_lines(models.Model):
    _name = 'cash.management.travel.advance.lines'

    header_id = fields.Many2one('cash.management.travel.advance.header')
    advance_type = fields.Many2one('cash.management.receipts.and.payment.types', domain = [('transaction_type','=','travel')])
    account_no = fields.Many2one('account.account')
    account_name = fields.Many2one('account.account')
    travel_from = fields.Many2one('cash.management.travel.destinations')
    travel_to = fields.Many2one('cash.management.travel.destinations')
    description = fields.Char()
    amount = fields.Float()

    @api.onchange('advance_type')
    def get_accounts(self):
        advance_type = self.env['cash.management.receipts.and.payment.types'].search([('id','=',self.advance_type.id)])
        self.account_name = advance_type.account_name
        self.description = advance_type.description

class travel_advance_surrender_header(models.Model):
    _name = 'cash.management.travel.advance.surrender.header'

    name = fields.Char(string = 'No.')
    date = fields.Date()
    source_document = fields.Many2one('cash.management.travel.advance.header', domain = [('surrendered','=',False)])
    surrendered_by = fields.Many2one('res.partner')
    advanced_amount = fields.Float()

    cashier = fields.Many2one('res.users', default = lambda self:self.env.user)
    state = fields.Selection([('draft',"Draft"),('ready',"Ready"),('open',"Open"),('surrendered',"Surrendered")], default = 'draft')
    remarks = fields.Text()
    posted = fields.Boolean()
    line_ids = fields.One2many('cash.management.travel.advance.surrender.lines', 'header_id')
    dimension1 = fields.Many2one('dimension.values', domain = [('sequence','=',1)])
    dimension2 = fields.Many2one('dimension.values', domain = [('sequence','=',2)])
    dimension3 = fields.Many2one('dimension.values', domain = [('sequence','=',3)])
    dimension4 = fields.Many2one('dimension.values', domain = [('sequence','=',4)])

    @api.one
    @api.onchange('name')
    def get_sequence(self):
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])
        sequence = self.env['ir.sequence'].search([('id','=',setup.travel_advance_surrender_numbers.id)])
        self.name = sequence.next_by_id(sequence.id, context = None)

    @api.onchange('source_document')
    def get_advance_details(self):
        self.surrendered_by = self.source_document.advance_to.id
        self.advanced_amount = self.source_document.total_amount


    @api.one
    def confirm(self):
        self.state = 'ready'

    @api.one
    def reset(self):
        self.state = 'draft'

    @api.one
    def get_travel_lines(self):
        if not self.source_document:
            raise ValidationError('Source document must have a value before getting lines')
        #populate lines
        self.line_ids.unlink()
        for line in self.source_document.line_ids:
            self.env['cash.management.travel.advance.surrender.lines'].create({'header_id':self.id,'advance_type':line.advance_type.id,
                'account_name':line.account_name.id,'travel_from':line.travel_from.id,'travel_to':line.travel_to.id,'amount_advanced':line.amount})


    @api.one
    def action_post(self):
        #date
        today = datetime.now().strftime("%Y/%m/%d")
        #create journal header
        paying_bank = self.env['res.partner.bank'].search([('bank','=',self.source_document.paying_bank.id)])

        journal = self.env['account.journal'].search([('id','=',paying_bank.journal_id.id)]) #get journal id
        #period
        period = self.env['account.period'].search([('state','=','draft'),('date_start','<=',today),('date_stop','>=',today)])
        period_id = period.id

        journal_header = self.env['account.move']#reference to journal entry
        move = journal_header.create({'journal_id':journal.id,'period_id':period_id,'state':'draft','name':self.name,
            'date':today})
        move_id = move.id

        #create journal lines
        journal_lines = self.env['account.move.line']

        #setup
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])

        #dr = self.source_document.line_ids.account_name.id
        cr = setup.staff_travel_receivable_account.id #paying_bank.journal_id.default_credit_account_id.id

        for line in self.line_ids:
            dr = line.account_name.id
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Staff Advance Surrender::' + self.name,'account_id':dr,'move_id':move_id,'debit':line.actual_spent,'partner_id':self.surrendered_by.id})
            journal_lines.create({'journal_id':journal.id,'period_id':period_id,'date':today,'name':'Staff Advance Surrender::' + self.name,'account_id':cr,'move_id':move_id,'credit':line.actual_spent,'partner_id':self.surrendered_by.id})

        self.posted = True
        self.source_document.surrendered = True

    @api.one
    def action_create_draft_receipt(self):
        pass

    @api.one
    def action_create_draft_payment(self):
        pass

class travel_advance_surrender_lines(models.Model):
    _name = 'cash.management.travel.advance.surrender.lines'

    header_id = fields.Many2one('cash.management.travel.advance.surrender.header')
    advance_type = fields.Many2one('cash.management.receipts.and.payment.types', domain = [('transaction_type','=','staff')])
    account_name = fields.Many2one('account.account')
    travel_from = fields.Many2one('cash.management.travel.destinations')
    travel_to = fields.Many2one('cash.management.travel.destinations')
    amount_advanced = fields.Float()
    actual_spent = fields.Float()
    balance = fields.Float()

    @api.onchange('actual_spent')
    def get_balance(self):
        self.balance = self.amount_advanced - self.actual_spent

class receipt_payment_types(models.Model):
    _name = 'cash.management.receipts.and.payment.types'

    name = fields.Char()
    transaction_type = fields.Selection([('receipt',"Receipt"),('payment',"Payment"),('staff',"Staff Advance"),('travel',"Travel Advance"),('petty',"Petty Cash")])
    description = fields.Char()
    account_no = fields.Char()
    account_name = fields.Many2one('account.account')



class travel_destinations(models.Model):
    _name = 'cash.management.travel.destinations'

    name = fields.Char()
    country = fields.Many2one('res.country')

class store_requisition(models.Model):
    _name = 'cash.management.store.requisition.header'

    name = fields.Char()
    request_date = fields.Date(string = 'Request Date', default = fields.Date.today)
    required_date = fields.Date(string = 'Required Date')
    request_description = fields.Text()
    issuing_store = fields.Char()
    requested_by = fields.Many2one('res.users', default = lambda self:self.env.user)
    state = fields.Selection([('draft','Draft'),('pending',"Pending Approval"),('issued',"Issued")], default = 'draft')
    line_ids = fields.One2many('cash.management.store.requisition.lines','header_id')

    @api.one
    @api.onchange('name')
    def get_sequence(self):
        setup = self.env['cash.management.general.setup'].search([('id','=',1)])
        sequence = self.env['ir.sequence'].search([('id','=',setup.store_requisition_numbers.id)])
        self.name = sequence.next_by_id(sequence.id, context = None)

class store_requisition_lines(models.Model):
    _name = 'cash.management.store.requisition.lines'

    header_id = fields.Many2one('cash.management.store.requisition.header')
    item = fields.Many2one('product.product')
    quantity_available = fields.Float()
    quantity_requested = fields.Float()
    unit_of_measure = fields.Char()
    unit_cost = fields.Float()
    total_cost = fields.Float()

class setup(models.Model):
    _name = 'cash.management.general.setup'

    name = fields.Char()
    petty_cash_voucher_numbers = fields.Many2one('ir.sequence')
    payment_voucher_numbers = fields.Many2one('ir.sequence')
    receipt_numbers = fields.Many2one('ir.sequence')
    bank_transfer_numbers = fields.Many2one('ir.sequence')
    staff_advance_numbers = fields.Many2one('ir.sequence')
    staff_advance_surrender_numbers = fields.Many2one('ir.sequence')
    travel_advance_numbers = fields.Many2one('ir.sequence')
    travel_advance_surrender_numbers = fields.Many2one('ir.sequence')
    store_requisition_numbers = fields.Many2one('ir.sequence')
    staff_advance_receivable_account = fields.Many2one('account.account')
    staff_travel_receivable_account = fields.Many2one('account.account')
