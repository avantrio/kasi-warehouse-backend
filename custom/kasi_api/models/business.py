from odoo import models, fields

class Business(models.Model):
    _inherit="res.company"

    Types = [
        ('BC', 'Beauty & Cosmetic stores'),
        ('SL', 'Salons'),
        ('SP', 'Spazarettes'),
        ('MW', 'Midi Wholesale'),
        ('MP', 'Market Place'),
    ]

    Townships = [
        ('TB-NJ', 'Tembisa - North Joburg'),
        ('KT-SD', 'Kathorus - Sedibeng'),
        ('SS-TS', 'Sosshangave - Tshwane'),
        ('SW-WJ', 'Soweto - West Joburg'),
        ('DS-WJ', 'Diepsloot - West Joburg'),
        ('DC-WJ', 'Dragon City - West Joburg'),
        ('RB-WJ', 'Randburg - West Joburg'),
        ('QT-EC', 'Queenstown - Eastern Cape'),
        ('Jb-WJ', 'Joburg CBD - West Joburg'),
        ('BR-WJ', 'Braamfontein - West Joburg'),
        ('AX-NJ', 'Alexandra - North Joburg'),
        ('BK-SD', 'Boksburg - Sedibeng'),
        ('GR-SD', 'Germiston - Sedibeng'),
        ('PT-TS', 'Pretoria - Tshwane'),
        ('KD-WJ', 'Krugersdorp- West Joburg'),
        ('RF-WJ', 'Randfontein - West Joburg'),
        ('RV-SJ', 'Rosettenville - South Joburg'),
        ('TK-SD', 'Thokoza - Sedibeng'),
        ('KP-NJ', 'Kempton Park - North Joburg'),
        ('RD-WJ', 'Roodepoort - West Joburg'),
        ('SS-SD', 'Springs - Sedibeng'),
    ]

    business_type = fields.Selection(Types, string='Business Type', required=False)
    township = fields.Selection(Townships, string='Township', required=False)



