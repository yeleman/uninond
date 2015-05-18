#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import os
import sys
import itertools
import random
import unicodecsv as csv

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from optparse import make_option

from uninond.models.Locations import Location

logger = logging.getLogger(__name__)
alphabet = 'abcdefghijklmnopqrstuvwxyz'
available_codes = ["{}{}".format(*x)
                   for x in list(itertools.combinations(alphabet, 2))]
random.shuffle(available_codes)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-f',
                    help='Villages CSV file',
                    action='store',
                    dest='filepath'),
    )

    def handle(self, *args, **options):
        if not os.path.exists(options.get('filepath') or "") \
                or not os.path.isfile(options.get('filepath') or ""):
            logger.error("Provided CSV file `{}` is incorrect."
                         .format(options.get('filepath')))
            sys.exit(1)

        headers = ['milieu', 'cercle', 'commune', 'vfq', 'nbmen', 'hommes',
                   'femmes', 'total', 'concessions', 'estim2015']
        input_csv_file = open(options.get('filepath'), 'r')
        csv_reader = csv.DictReader(input_csv_file, fieldnames=headers)

        # first, clear all locations
        Location.objects.all().delete()

        # Create the root Location (Mopti)
        mopti = Location.objects.create(
            slug='mopti', name="Mopti", location_type=Location.REGION)

        for entry in csv_reader:
            if csv_reader.line_num == 1:
                continue

            logger.debug(entry)

            # get cercle
            cercle_slug = "cercle_{}".format(slugify(entry.get('cercle')))
            cercle = Location.get_or_none(cercle_slug)
            if cercle is None:
                cercle = Location.objects.create(
                    slug=cercle_slug,
                    name=entry.get('cercle').strip(),
                    parent=mopti,
                    location_type=Location.CERCLE)
                logger.info("Created {}".format(cercle.display_name))

            # get commune
            commune_slug = "commune_{}".format(slugify(entry.get('commune')))
            commune = Location.get_or_none(commune_slug)
            if commune is None:
                commune = Location.objects.create(
                    slug=commune_slug,
                    name=entry.get('commune').strip(),
                    parent=cercle,
                    location_type=Location.COMMUNE)
                logger.info("Created {}".format(commune.display_name))

            # get vfq
            vfq_slug = available_codes.pop()
            vfq = Location.objects.create(
                slug=vfq_slug,
                name=entry.get('vfq').strip(),
                parent=commune,
                location_type=Location.VFQ)

            logger.info("Created {}: {}".format(vfq.slug, vfq.display_name))
