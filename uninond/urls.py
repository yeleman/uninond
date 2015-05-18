#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import TemplateView

urlpatterns = [
    # Examples:
    # url(r'^$', 'uninond.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^api/acpi_status?$', 'uninond.views.api.acpi_status',
        name='acpi_status'),
    url(r'^api/new_alert?$', 'uninond.views.api.new_alert',
        name='acpi_status'),

    # Android API
    url(r'^fondasms/?$', 'fondasms.views.fondasms_handler',
        {'handler_module': 'uninond.fondasms_handlers',
         'send_automatic_reply': False,
         'automatic_reply_via_handler': False,
         'automatic_reply_text': None},
        name='fondasms'),
    url(r'^fondasms/test/?$',
        TemplateView.as_view(template_name="fondasms_tester.html"),
        name='fondasms_tester'),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^addressbook/(?P<contact_identity>[\+0-9]+)/enable/?$',
        'uninond.views.dashboard.contact_enable', name='contact_enable'),
    url(r'^addressbook/(?P<contact_identity>[\+0-9]+)/disable/?$',
        'uninond.views.dashboard.contact_disable', name='contact_disable'),
    url(r'^addressbook/(?P<contact_identity>[\+0-9]+)/?$',
        'uninond.views.dashboard.contact_details', name='contact_details'),
    url(r'^addressbook/?$',

        'uninond.views.dashboard.addressbook', name='addressbook'),
    url(r'^smses/?$', 'uninond.views.dashboard.sms_list', name='smses'),
    url(r'^events/(?P<ident>[a-z0-9]+)?$',
        'uninond.views.dashboard.event_details', name='event'),
    url(r'^/?$', 'uninond.views.dashboard.home', name='dashboard'),
]
