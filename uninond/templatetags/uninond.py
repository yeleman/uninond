#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.template.defaultfilters import stringfilter
from django import template

from uninond.tools import phonenumber_repr

register = template.Library()


@register.filter(name='phone')
@stringfilter
def phone_number_formatter(number):
    ''' format phone number properly for display '''
    return phonenumber_repr(number)
