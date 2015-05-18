#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import datetime

import acpi
from django.http import JsonResponse

from uninond.models.FloodEvents import FloodEvent

logger = logging.getLogger(__name__)


def acpi_status(request):
    try:
        name, status, percent, value, remaining = acpi.acpi()[-1]
        name, status, percent, value, remaining = (
            'Battery 0', 'Full', 100, None, None)
        name, status, percent, value, remaining = (
            'Battery 0', 'Discharging', 80, 21550, '05:59:10')
        remaining_tuple = [int(x) for x in remaining.split(":")]
        data = {
            'name': name,
            'status': status,
            'percent': percent,
            'value': value,
            'remaining_text': remaining,
            'remaining': remaining_tuple
        }
    except IndexError:
        data = None
    return JsonResponse(data, safe=False)


def new_alert(request):

    try:
        timestamp = int(float(request.GET.get('timestamp')))
        since = datetime.datetime.utcfromtimestamp(timestamp)
    except:
        raise
        since = timestamp = None

    if since is not None:
        nb_alerts = FloodEvent.objects.filter(created_on__gte=since).count()
    else:
        nb_alerts = 0

    data = {
        'nb_new_alerts': nb_alerts,
        'since': timestamp
    }

    return JsonResponse(data, safe=False)
