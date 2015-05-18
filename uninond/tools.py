#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import re
import unicodedata
import datetime
import subprocess

from py3compat import string_types, text_type
from django.utils import timezone
from django.conf import settings

from uninond.models.SMSMessages import SMSMessage

# default country prefix
COUNTRY_PREFIX = getattr(settings, 'COUNTRY_PREFIX', 223)
ALL_COUNTRY_CODES = [1242, 1246, 1264, 1268, 1284, 1340, 1345, 1441, 1473,
                     1599, 1649, 1664, 1670, 1671, 1684, 1758, 1767, 1784,
                     1809, 1868, 1869, 1876, 1, 20, 212, 213, 216, 218, 220,
                     221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231,
                     232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242,
                     243, 244, 245, 248, 249, 250, 251, 252, 253, 254, 255,
                     256, 257, 258, 260, 261, 262, 263, 264, 265, 266, 267,
                     268, 269, 27, 290, 291, 297, 298, 299, 30, 31, 32, 33,
                     34, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359,
                     36, 370, 371, 372, 373, 374, 375, 376, 377, 378, 380,
                     381, 382, 385, 386, 387, 389, 39, 40, 41, 420, 421, 423,
                     43, 44, 45, 46, 47, 48, 49, 500, 501, 502, 503, 504,
                     505, 506, 507, 508, 509, 51, 52, 53, 54, 55, 56, 57, 58,
                     590, 591, 592, 593, 595, 597, 598, 599, 60, 61, 62, 63,
                     64, 65, 66, 670, 672, 673, 674, 675, 676, 677, 678, 679,
                     680, 681, 682, 683, 685, 686, 687, 688, 689, 690, 691,
                     692, 7, 81, 82, 84, 850, 852, 853, 855, 856, 86, 870,
                     880, 886, 90, 91, 92, 93, 94, 95, 960, 961, 962, 963,
                     964, 965, 966, 967, 968, 970, 971, 972, 973, 974, 975,
                     976, 977, 98, 992, 993, 994, 995, 996, 998]
MONTHS = ['J', 'F', 'M', 'A', 'Y', 'U', 'L', 'G', 'S', 'O', 'N', 'D']
ALPHA = 'abcdefghijklmnopqrstuvwxyz'


def phonenumber_isint(number):
    ''' whether number is in international format '''
    if re.match(r'^[+|(]', number):
        return True
    if re.match(r'^\d{1,4}\.\d+$', number):
        return True
    return False


def phonenumber_indicator(number):
    ''' extract indicator from number or "" '''
    for indic in ALL_COUNTRY_CODES:
        if number.startswith("%{}".format(indic)) \
                or number.startswith("+{}".format(indic)):
            return str(indic)
    return ""


def phonenumber_cleaned(number):
    ''' return (indicator, number) cleaned of space and other '''
    # clean up
    if not isinstance(number, string_types):
        number = number.__str__()

    # cleanup markup
    clean_number = re.sub(r'[^\d\+]', '', number)

    if phonenumber_isint(clean_number):
        h, indicator, clean_number = \
            clean_number.partition(phonenumber_indicator(clean_number))
        return (indicator, clean_number)

    return (None, clean_number)


def join_phonenumber(prefix, number, force_intl=True):
    if not number:
        return None
    if not prefix and force_intl:
        prefix = COUNTRY_PREFIX
    return "+{prefix}{number}".format(prefix=prefix, number=number)


def phonenumber_repr(number, skip_indicator=str(COUNTRY_PREFIX)):
    ''' properly formated for visualization: (xxx) xx xx xx xx '''

    def format(number):
        if len(number) % 2 == 0:
            span = 2
        else:
            span = 3
        # use NBSP
        return " ".join(["".join(number[i:i + span])
                         for i in range(0, len(number), span)])

    indicator, clean_number = phonenumber_cleaned(number)

    # string-only identity goes into indicator
    if indicator is None and not clean_number:
        return number.strip()

    if indicator and indicator != skip_indicator:
        return "(%(ind)s) %(num)s" \
               % {'ind': indicator,
                  'num': format(clean_number)}
    return format(clean_number)


def normalized_phonenumber(number_text):
    if number_text is None or not number_text.strip():
        return None
    return join_phonenumber(*phonenumber_cleaned(number_text))


def operator_from_malinumber(number, default=settings.FOREIGN):
    ''' ORANGE or MALITEL based on the number prefix '''

    indicator, clean_number = phonenumber_cleaned(
        normalized_phonenumber(number))
    if indicator is not None and indicator != str(COUNTRY_PREFIX):
        return default

    for operator, opt in settings.OPERATORS.items():

        for prefix in opt[1]:
            if clean_number.startswith(str(prefix)):
                return operator

    return default


def send_sms(to, text):

    return SMSMessage.objects.create(
        direction=SMSMessage.OUTGOING,
        identity=to,
        event_on=timezone.now(),
        text=text)


def fake_message(to, text):
    message = send_sms(to, text)
    message.handled = True
    message.save()
    return message


def to_ascii(text):
    return unicodedata.normalize('NFKD', unicode(text)) \
                      .encode('ASCII', 'ignore').strip()


def date_to_ident(adate):
    year, month, day = adate.timetuple()[0:3]
    hyear = text_type(year)[-1]
    if day > 16:
        hmonth = ALPHA[month * 2]
        hday = hex(day // 2)[2:]
    else:
        hmonth = ALPHA[month]
        hday = hex(day)[2:]
    return "{y}{m}{d}".format(m=hmonth, d=hday, y=hyear)


def ident_to_date(ident):
    hyear, hmonth, hday = ident[0], ident[1], ident[2:]
    year = int('201{}'.format(hyear))
    day = int(hday, 16)
    month = ALPHA.index(hmonth)
    if month > 12:
        month //= 2
        day *= 2
    return datetime.date(year, month, day)


def dispatch_sms(text, roles, root):
    sent_messages = []
    for identity in root.ancestors_contacts(roles, identies_only=True):
        sent_messages.append(send_sms(identity, text))
    return sent_messages


def datetime_repr(adatetime):
    return ("{date} à {time}"
            .format(date=adatetime.strftime("%A %-d"),
                    time=adatetime.strftime("%Hh%M")).lower())


def exec_cmd(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    process.wait()
    return process.returncode
