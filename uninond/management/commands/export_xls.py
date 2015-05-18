#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import os
import sys

from django.core.management.base import BaseCommand
from optparse import make_option

from uninond.exports import export_to

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-p',
                    help='Destination Path',
                    action='store',
                    dest='dest_path'),
    )

    def handle(self, *args, **options):

        if not os.path.exists(options.get('dest_path') or ""):
            logger.error("Destination path does not exist."
                         .format(options.get('dest_path')))
            sys.exit(1)

        try:
            fp = export_to(options.get('dest_path'))
        except Exception as e:
            logger.exception(e)
            sys.exit(1)
        else:
            logger.info("Exported file to `{}`".format(fp))
