# -*- coding: utf-8 -*-

import logging
import pytz

from odoo import fields, models, api, _
from odoo.addons.sanqua_print.helpers import amount_to_text,\
    format_local_currency,\
    format_local_datetime
_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @staticmethod
    def get_format_currency(value,total=False):
        """ Get format currency with rule: thousand -> (.) and no decimal place.
        :param value: Float. Value that need to be formatting.
        :return: String. Format currency result.
        """
        return format_local_currency(value,total)

    def get_format_datetime(self, datetime_value, only_date=False):
        """ Get format datetime as string.
        :param datetime_value: Datetime. Datetime that need to be formatting.
        :param only_date: Boolean. If 'True' then value will be return as Date.
        :return: String. Format datetime result.
        """
        user_tz = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
        return format_local_datetime(user_tz, datetime_value, only_date=True)

    def terbilang(self, satuan):
        huruf = ["","Satu","Dua","Tiga","Empat","Lima","Enam","Tujuh","Delapan","Sembilan","Sepuluh","Sebelas"]
        # huruf = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Eleven","Twelve"]
        hasil = ""; 
        if satuan < 12: 
            hasil = hasil + huruf[int(satuan)]; 
        elif satuan < 20: 
            hasil = hasil + self.terbilang(satuan-10)+" Belas"; 
        elif satuan < 100:
            hasil = hasil + self.terbilang(satuan/10)+" Puluh "+self.terbilang(satuan%10); 
        elif satuan < 200: 
            hasil=hasil+"Seratus "+self.terbilang(satuan-100); 
        elif satuan < 1000: 
            hasil=hasil+self.terbilang(satuan/100)+" Ratus "+self.terbilang(satuan%100); 
        elif satuan < 2000: 
            hasil=hasil+"Seribu "+self.terbilang(satuan-1000); 
        elif satuan < 1000000: 
            hasil=hasil+self.terbilang(satuan/1000)+" Ribu "+self.terbilang(satuan%1000); 
        elif satuan < 1000000000:
            hasil=hasil+self.terbilang(satuan/1000000)+" Juta "+self.terbilang(satuan%1000000);
        elif satuan < 1000000000000:
            hasil=hasil+self.terbilang(satuan/1000000000)+" Milyar "+self.terbilang(satuan%1000000000)
        elif satuan >= 1000000000000:
            hasil="Angka terlalu besar, harus kurang dari 1 Trilyun!"; 
        return hasil;
