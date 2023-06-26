from odoo import models, fields

class PaymentMethod(models.Model):
    _inherit=["sale.order"]

    Types = [
        ('CASH', 'Cash'),
        ('SHOP_TO_SHOP', 'Shop to Shop'),
        ('BANK_DEPOSIT', 'Cash deposit in Bank'),
        ('EFT', 'EFT')
    ]

    payment_method = fields.Selection(Types, string='Payment Method', required=False)



