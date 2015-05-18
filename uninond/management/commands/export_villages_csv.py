#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import unicodecsv as csv

from django.core.management.base import BaseCommand
from optparse import make_option

from uninond.models.Locations import Location

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-f',
                    help='Path to export villages to',
                    action='store',
                    dest='filepath'),
    )

    def handle(self, *args, **options):

        headers = ['cercle', 'commune', 'code', 'vfq']
        output_csv_file = open(options.get('filepath'), 'w')
        csv_writer = csv.DictWriter(output_csv_file, fieldnames=headers)

        csv_writer.writeheader()

        for vfq in Location.objects.filter(
                location_type=Location.VFQ).order_by('name') \
                                           .order_by('parent__name') \
                                           .order_by('parent__parent__name'):
            entry = {
                'cercle': vfq.parent.parent.name,
                'commune': vfq.parent.name,
                'code': vfq.slug.upper(),
                'vfq': vfq.name
            }

            csv_writer.writerow(entry)

        output_csv_file.close()

        logger.info("Export successful to `{}`"
                    .format(options.get('filepath')))
