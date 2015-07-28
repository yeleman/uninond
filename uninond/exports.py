#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import os
import StringIO
import datetime

import xlwt

from uninond.models.FloodEvents import FloodEvent
from uninond.models.SMSMessages import SMSMessage
from uninond.models.Contacts import Contact
from uninond.tools import phonenumber_repr

logger = logging.getLogger(__name__)

BLANK = ""

# styles
border_bottom_large = xlwt.Borders()
border_bottom_large.left = 1
border_bottom_large.right = 1
border_bottom_large.top = 1
border_bottom_large.bottom = 2

border_all_regular = xlwt.Borders()
border_all_regular.left = 1
border_all_regular.right = 1
border_all_regular.top = 1
border_all_regular.bottom = 1

align_center = xlwt.Alignment()
align_center.horz = xlwt.Alignment.HORZ_CENTER
align_center.vert = xlwt.Alignment.VERT_CENTER
align_center.wrap = 1

align_left = xlwt.Alignment()
align_left.horz = xlwt.Alignment.HORZ_LEFT
align_left.vert = xlwt.Alignment.VERT_CENTER

font_regular = xlwt.Font()
font_regular.name = "Trebuchet MS"
font_regular.bold = False
font_regular.height = 12 * 0x14

font_bold = xlwt.Font()
font_bold.name = "Trebuchet MS"
font_bold.bold = True
font_bold.height = 12 * 0x14

font_title = xlwt.Font()
font_title.name = "Trebuchet MS"
font_title.bold = True
font_title.height = 12 * 0x14

color_lightgrey = xlwt.Pattern()
color_lightgrey.pattern = xlwt.Pattern.SOLID_PATTERN
color_lightgrey.pattern_fore_colour = 7

header_style = xlwt.XFStyle()
header_style.alignment = align_center
header_style.borders = border_bottom_large
header_style.font = font_title
header_style.pattern = color_lightgrey

regular_style = xlwt.XFStyle()
regular_style.alignment = align_left
regular_style.borders = border_all_regular
regular_style.font = font_regular


def dtformat(dt):
    if dt is None:
        return None
    return dt.strftime("%c")


def xl_col_width(cm):
    """ xlwt width for a given width in centimeters """
    return int(2770 / 2.29 * cm)


def xl_set_col_width(sheet, col, cm):
    """ change column width """
    sheet.col(col).width = xl_col_width(cm)


def generate_xls_export():

    def write_col(col, content):
        fl_sheet.write(row, col, content, regular_style)
        col += 1
        return col

    now = datetime.datetime.now()
    book = xlwt.Workbook(encoding='utf-8')

    # INONDATIONS SHEET
    fl_sheet = book.add_sheet("INONDATIONS")

    # write header
    row = 0

    columns = ["Code Inondation", "Créée le", "Créée par", "Village",
               "Statut", "", "Expirée le", "", "Surface sub. délcarée",
               "Maisons détruites délcarée", "Morts délcarés",
               "Blessés délcarés", "", "Annulée le", "Annulée par", "",
               "DRPC contenue le", "DRPC contenue par", "",
               "DRPC confirmée le", "DRPC confirmée par", "",
               "Surface sub. DRPC", "Maisons détruites DRPC",
               "Morts DRPC", "Blessés DRPC", "Commentaire DRPC"]

    for idx, column_label in enumerate(columns):
        fl_sheet.write(row, idx, column_label, header_style)

    # loop through FloodEvents
    for event in FloodEvent.objects.all().order_by('-created_on'):
        row += 1
        col = 0

        col = write_col(col, event.verbose_ident)

        xl_set_col_width(fl_sheet, col, 5.2)
        col = write_col(col, dtformat(event.created_on))

        xl_set_col_width(fl_sheet, col, 6)
        col = write_col(col, event.created_by.full_name)

        xl_set_col_width(fl_sheet, col, 10)
        col = write_col(col, getattr(event.location, 'display_name', BLANK))
        col = write_col(col, event.verbose_status)
        col = write_col(col, "")

        xl_set_col_width(fl_sheet, col, 5.2)
        col = write_col(col, dtformat(event.expired_on) or BLANK)
        col = write_col(col, "")
        col = write_col(col, event.initial_flooded_area)
        col = write_col(col, event.initial_homes_destroyed)
        col = write_col(col, event.initial_dead)
        col = write_col(col, event.initial_wounded)
        col = write_col(col, "")

        xl_set_col_width(fl_sheet, col, 5.2)
        col = write_col(col, dtformat(event.cancelled_on))
        xl_set_col_width(fl_sheet, col, 6)
        col = write_col(col, getattr(event.cancelled_by, 'full_name', BLANK))
        col = write_col(col, "")

        xl_set_col_width(fl_sheet, col, 5.2)
        col = write_col(col, dtformat(event.restrained_on))
        xl_set_col_width(fl_sheet, col, 6)
        col = write_col(col, getattr(event.restrained_by, 'full_name', BLANK))
        col = write_col(col, "")

        xl_set_col_width(fl_sheet, col, 5.2)
        col = write_col(col, dtformat(event.confirmed_on))
        xl_set_col_width(fl_sheet, col, 6)
        col = write_col(col, getattr(event.confirmed_by, 'full_name', BLANK))
        col = write_col(col, "")
        if event.verified:
            fa = event.flooded_area
            hd = event.homes_destroyed
            db = event.dead
            wd = event.wounded
            cm = event.comment
        else:
            fa = hd = db = wd = cm = BLANK
        col = write_col(col, fa)
        col = write_col(col, hd)
        col = write_col(col, db)
        col = write_col(col, wd)

        xl_set_col_width(fl_sheet, col, 10)
        col = write_col(col, cm)

    # SMS SHEET
    fl_sheet = book.add_sheet("SMS")

    # write header
    row = 0

    columns = ["Direction", "Numéro tél.", "Créé le", "message"]

    for idx, column_label in enumerate(columns):
        fl_sheet.write(row, idx, column_label, header_style)

    # loop through SMSMessage
    for message in SMSMessage.objects.all().order_by('-created_on'):
        row += 1
        col = 0

        col = write_col(col, message.verbose_direction)

        xl_set_col_width(fl_sheet, col, 8)
        col = write_col(col, phonenumber_repr(message.identity))

        xl_set_col_width(fl_sheet, col, 5.2)
        col = write_col(col, dtformat(message.created_on))

        xl_set_col_width(fl_sheet, col, 50)
        col = write_col(col, message.text)

    # CONTACTS SHEET
    fl_sheet = book.add_sheet("ANNUAIRE")

    # write header
    row = 0

    columns = ["Nom", "Numéro tél.", "Rôle", "Localité", "Fonction", "Actif"]

    for idx, column_label in enumerate(columns):
        fl_sheet.write(row, idx, column_label, header_style)

    # loop through Contacts
    for contact in Contact.objects.all().order_by('name'):
        row += 1
        col = 0

        xl_set_col_width(fl_sheet, col, 8)
        col = write_col(col, contact.name or BLANK)

        xl_set_col_width(fl_sheet, col, 8)
        col = write_col(col, phonenumber_repr(contact.identity))

        xl_set_col_width(fl_sheet, col, 4)
        col = write_col(col, contact.verbose_role or BLANK)

        xl_set_col_width(fl_sheet, col, 10)
        col = write_col(col, getattr(contact.location, 'display_name', BLANK))

        xl_set_col_width(fl_sheet, col, 6)
        col = write_col(col, contact.position or BLANK)

        xl_set_col_width(fl_sheet, col, 5)
        col = write_col(col, "Oui" if contact.active else "Non")

    # finish excel document
    stream = StringIO.StringIO()
    book.save(stream)

    filename = "UNINOND-DRPC-MOPTI_{}.xls".format(now.strftime('%d-%m-%Y'))

    return filename, stream


def export_to(apath):
    if not os.path.exists(apath) or not os.path.isdir(apath):
        raise IOError("Specified path is not a folder")

    filename, datastream = generate_xls_export()
    full_path = os.path.join(apath, filename)
    with open(full_path, 'w') as f:
        f.write(datastream.getvalue())

    return full_path
