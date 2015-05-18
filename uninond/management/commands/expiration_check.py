#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from uninond.models.FloodEvents import FloodEvent

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        now = timezone.now()
        nbd = FloodEvent.EXPIRATION_DELAY // 86400
        nbs = FloodEvent.EXPIRATION_DELAY % 86400
        expiration = now - datetime.timedelta(days=nbd, seconds=nbs)
        for event in FloodEvent.objects.filter(created_on__lte=expiration,
                                               status=FloodEvent.CREATED):
            logger.info("FloodEvent {} created on {} has expired."
                        .format(event.verbose_ident,
                                event.created_on))
            event.expire()
