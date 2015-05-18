#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from py3compat import implements_to_string


@implements_to_string
class SMSMessage(models.Model):

    class Meta:
        app_label = 'uninond'
        verbose_name = _("SMS Message")
        verbose_name_plural = _("SMS Messages")

    INCOMING = 'incoming'
    OUTGOING = 'outgoing'
    DIRECTIONS = {
        INCOMING: "Reçu",
        OUTGOING: "Envoyé"
    }

    SUCCESS = 'success'
    FAILURE = 'failure'
    BUFFERED = 'buffered'
    SMSC_SUBMIT = 'smsc_submit'
    SMSC_REJECT = 'smsc_reject'
    SMSC_NOTIFS = 'smsc_notifications'
    UNKNOWN = 'unknown'

    DELIVERY_STATUSES = {
        UNKNOWN: "Unknown",
        SUCCESS: "Delivery Success",
        FAILURE: "Delivery Failure",
        BUFFERED: "Message Buffered",
        SMSC_SUBMIT: "SMSC Submit",
        SMSC_REJECT: "SMSC Reject",
        SMSC_NOTIFS: "SMSC Intermediate Notifications",
    }

    direction = models.CharField(max_length=75,
                                 choices=DIRECTIONS.items())
    identity = models.CharField(max_length=250)
    created_on = models.DateTimeField(default=timezone.now)
    event_on = models.DateTimeField(default=timezone.now)
    text = models.TextField()
    handled = models.BooleanField(default=False)
    # minutes of validity
    validity = models.PositiveIntegerField(blank=True, null=True)
    # minutes after creation time to send the SMS at
    deferred = models.PositiveIntegerField(blank=True, null=True)
    # DLR statuses
    delivery_status = models.CharField(max_length=75, default=UNKNOWN,
                                       choices=DELIVERY_STATUSES.items())

    def __str__(self):
        return self.text

    @property
    def message(self):
        return self.text

    @property
    def content(self):
        return self.message

    def respond(self, text):
        SMSMessage.objects.create(
            direction=self.OUTGOING,
            identity=self.identity,
            event_on=timezone.now(),
            text=text)

    @property
    def verbose_direction(self):
        return self.DIRECTIONS.get(self.direction)
