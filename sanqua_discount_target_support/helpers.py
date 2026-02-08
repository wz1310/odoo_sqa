""" This is collections of helper functions """
import pytz


def amount_to_text(amount):
    """ Convert from amount float to text.
    :param amount: Float. amount value.
    :return: String. Text of amount.
    """
    angka = ["", "Satu", "Dua", "Tiga", "Empat", "Lima", "Enam", "Tujuh", "Delapan", "Sembilan",
             "Sepuluh", "Sebelas"]
    result = " "
    n = int(amount)
    if n >= 0 and n <= 11:
        result = result + angka[n]
    elif n < 20:
        result = amount_to_text(n % 10) + " Belas"
    elif n < 100:
        result = amount_to_text(n / 10) + " Puluh" + amount_to_text(n % 10)
    elif n < 200:
        result = " Seratus" + amount_to_text(n - 100)
    elif n < 1000:
        result = amount_to_text(n / 100) + " Ratus" + amount_to_text(n % 100)
    elif n < 2000:
        result = " Seribu" + amount_to_text(n - 1000)
    elif n < 1000000:
        result = amount_to_text(n / 1000) + " Ribu" + amount_to_text(n % 1000)
    elif n < 1000000000:
        result = amount_to_text(n / 1000000) + " Juta" + amount_to_text(n % 1000000)
    elif n < 1000000000000:
        result = amount_to_text(n / 1000000000) + " Milyar" + amount_to_text(n % 1000000000)
    else:
        result = amount_to_text(n / 1000000000000) + " Triliyun" + amount_to_text(n % 1000000000000)
    return result


def format_local_currency(value,total=False):
    """ Convert from float currency to local (indonesian) string of currency.
    :param value: Float. value that want to formatting.
    :return: String. Currency format result.
    """
    new_format = '{0:,.2f}'.format(value)
    if total:
        new_format.replace(',', ';').replace('.', ',').replace(';', '.')
        return 'Rp. ' + new_format
    return new_format.replace(',', ';').replace('.', ',').replace(';', '.')


def format_local_datetime(timezone, datetime_value, only_date=False):
    """ Format datetime to local timezone as string.
    :param datetime_value: Datetime. Datetime that need to be formatting.
    :param only_date: Boolean. If 'True' then value will be return as Date.
    :return: String. Format datetime result.
    """
    result = pytz.utc.localize(datetime_value).astimezone(timezone)
    if only_date:
        result = result.date()
        return result.strftime('%d/%m/%Y')

    return result.strftime('%d-%m-%Y %H:%M:%S')
