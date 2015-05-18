#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import datetime

from py3compat import implements_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db import models

from uninond.tools import date_to_ident, ALPHA

logger = logging.getLogger(__name__)


@implements_to_string
class FloodEvent(models.Model):

    class Meta:
        app_label = 'uninond'
        verbose_name = _("Inondation")
        verbose_name_plural = _("Inondations")
        ordering = ['-created_on']

    EXPIRATION_DELAY = 5 * 86400  # 5days
    DUPLICATE_DURATION = 36 * 3600  # 36hours
    CREATED = 'created'
    CANCELLED = 'cancelled'
    RESTRAINED = 'restrained'
    CONFIRMED = 'confirmed'
    EXPIRED = 'expired'

    STATUSES = {
        CREATED: "Créé",
        CANCELLED: "Annulée",
        RESTRAINED: "Contenue",
        CONFIRMED: "Confirmée",
        EXPIRED: "Expirée"
    }

    AREAS = {
        1: "1/3",
        2: "2/3",
        3: "3/3"
    }

    ident = models.SlugField(max_length=10, primary_key=True)

    created_on = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey('Contact', related_name='flood_events')
    location = models.ForeignKey('Location', related_name='flood_events')

    messages = models.ManyToManyField('SMSMessage', blank=True,
                                      related_name='flood_events')
    status = models.SlugField(max_length=50, default=CREATED,
                              choices=STATUSES.items())
    expired_on = models.DateTimeField(blank=True, null=True)

    initial_flooded_area = models.PositiveIntegerField(choices=AREAS.items())
    initial_homes_destroyed = models.PositiveIntegerField(default=0)
    initial_dead = models.PositiveIntegerField(default=0)
    initial_wounded = models.PositiveIntegerField(default=0)

    cancelled_on = models.DateTimeField(blank=True, null=True)
    cancelled_by = models.ForeignKey('Contact',
                                     related_name='cancelled_flood_events',
                                     blank=True, null=True)

    restrained_on = models.DateTimeField(blank=True, null=True)
    restrained_by = models.ForeignKey('Contact',
                                      related_name='restrained_flood_events',
                                      blank=True, null=True)
    restrained_flooded_area = models.PositiveIntegerField(
        choices=AREAS.items(), blank=True, null=True)
    restrained_homes_destroyed = models.PositiveIntegerField(
        blank=True, null=True)
    restrained_dead = models.PositiveIntegerField(blank=True, null=True)
    restrained_wounded = models.PositiveIntegerField(blank=True, null=True)
    restrained_comment = models.CharField(max_length=1600,
                                          blank=True, null=True)

    confirmed_on = models.DateTimeField(blank=True, null=True)
    confirmed_by = models.ForeignKey('Contact',
                                     related_name='confirmed_flood_events',
                                     blank=True, null=True)
    confirmed_flooded_area = models.PositiveIntegerField(
        choices=AREAS.items(), blank=True, null=True)
    confirmed_homes_destroyed = models.PositiveIntegerField(
        blank=True, null=True)
    confirmed_dead = models.PositiveIntegerField(blank=True, null=True)
    confirmed_wounded = models.PositiveIntegerField(blank=True, null=True)
    confirmed_comment = models.CharField(max_length=1600,
                                         blank=True, null=True)

    @classmethod
    def get_or_none(cls, ident):
        try:
            return cls.objects.get(ident=ident.lower())
        except cls.DoesNotExist:
            return None

    @classmethod
    def duplicate(cls, location, created_on):
        try:
            sod = created_on - datetime.timedelta(
                seconds=cls.DUPLICATE_DURATION)
            return cls.objects.filter(location=location) \
                              .filter(created_on__range=(sod, created_on)) \
                              .last()
        except cls.DoesNotExist:
            return None

    @property
    def closed(self):
        return self.status in (self.CANCELLED, self.EXPIRED,
                               self.RESTRAINED, self.CONFIRMED)

    @property
    def expired(self):
        return self.status == self.EXPIRED

    @property
    def cancelled(self):
        return self.status == self.CANCELLED

    @property
    def confirmed(self):
        return self.status == self.CONFIRMED

    @property
    def restrained(self):
        return self.status == self.RESTRAINED

    @property
    def verified(self):
        return self.closed and \
            self.status not in (self.EXPIRED, self.CANCELLED)

    @property
    def verbose_status(self):
        return self.STATUSES.get(self.status)

    @property
    def verbose_ident(self):
        return "#{}".format(self.ident)

    @property
    def closed_on(self):
        if not self.closed:
            return None
        if self.status == self.CANCELLED:
            return self.cancelled_on
        if self.status == self.EXPIRED:
            return self.expired_on
        if self.status == self.RESTRAINED:
            return self.restrained_on
        if self.status == self.CONFIRMED:
            return self.confirmed_on

    @property
    def updated_on(self):
        if self.closed:
            return self.closed_on
        return self.created_on

    def current_value_of(self, field):
        if field == 'comment' and not self.confirmed:
            return None
        if self.status in (self.CREATED, self.CANCELLED, self.EXPIRED):
            prefix = 'initial'
        if self.status == self.RESTRAINED:
            prefix = 'restrained'
        if self.status == self.CONFIRMED:
            prefix = 'confirmed'

        return getattr(self, '{pf}_{f}'.format(pf=prefix, f=field), None)

    @property
    def flooded_area(self):
        return self.current_value_of('flooded_area')

    @property
    def homes_destroyed(self):
        return self.current_value_of('homes_destroyed')

    @property
    def dead(self):
        return self.current_value_of('dead')

    @property
    def wounded(self):
        return self.current_value_of('wounded')

    @property
    def comment(self):
        return self.current_value_of('comment')

    def cancel(self, by, at=None):
        self.change_status(self.CANCELLED, by, at)

    def restrain(self, by, flooded_area, homes_destroyed,
                 dead, wounded, comment=None, at=None):
        self.update_parameters(self.RESTRAINED,
                               flooded_area, homes_destroyed,
                               dead, wounded, comment)
        self.change_status(self.RESTRAINED, by, at)

    def confirm(self, by, flooded_area, homes_destroyed,
                dead, wounded, comment=None, at=None):
        self.update_parameters(self.CONFIRMED,
                               flooded_area, homes_destroyed,
                               dead, wounded, comment)
        self.change_status(self.CONFIRMED, by, at)

    def expire(self, at=None):
        self.change_status(self.EXPIRED, at=at)

    def change_status(self, new_status, by=None, at=None):
        if at is None:
            at = timezone.now()
        if new_status == self.CANCELLED:
            self.cancelled_on = at
            self.cancelled_by = by
        elif new_status == self.RESTRAINED:
            self.restrained_on = at
            self.restrained_by = by
        elif new_status == self.CONFIRMED:
            self.confirmed_on = at
            self.confirmed_by = by
        elif new_status == self.EXPIRED:
            self.expired_on = at

        self.status = new_status
        self.save()

    def update_parameters(self, for_status, flooded_area, homes_destroyed,
                          dead, wounded, comment=None):
        upd = lambda f, v: setattr(self, '{status}_{field}'
                                         .format(status=for_status, field=f),
                                   v)
        upd('flooded_area', flooded_area)
        upd('homes_destroyed', homes_destroyed)
        upd('dead', dead)
        upd('wounded', wounded)
        upd('comment', comment)
        self.save()

    def __str__(self):
        return "{ident} at {location}".format(ident=self.verbose_ident,
                                              location=self.location)

    def gen_ident(self):
        ident = date_to_ident(self.created_on)
        if self.get_or_none(ident) is None:
            return ident
        else:
            eoi = FloodEvent.objects.filter(ident__startswith=ident) \
                .order_by('-created_on').first().ident[-1]
            if eoi.isdigit():
                counter = 'a'
            else:
                counter = ALPHA[ALPHA.index(eoi) + 1]
            return "{ident}{counter}".format(ident=ident, counter=counter)

    def save(self, *args, **kwargs):
        if not self.ident:
            self.ident = self.gen_ident()
        super(FloodEvent, self).save()

    def add_message(self, message):
        self.messages.add(message)
