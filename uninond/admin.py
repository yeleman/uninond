#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.contrib import admin

from uninond.models.Locations import Location
from uninond.models.SMSMessages import SMSMessage
from uninond.models.Contacts import Contact
from uninond.models.FloodEvents import FloodEvent

admin.site.register(Location)
admin.site.register(SMSMessage)
admin.site.register(Contact)
admin.site.register(FloodEvent)
