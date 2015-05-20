#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from py3compat import implements_to_string
from django.db import models

from uninond.models.SMSMessages import SMSMessage
from uninond.tools import normalized_phonenumber, phonenumber_repr

logger = logging.getLogger(__name__)


@implements_to_string
class Contact(models.Model):

    GOUVERNEUR = 'gouverneur'
    PREFET = 'prefet'
    SOUS_PREFET = 'sous-prefet'
    MAIRE = 'maire'
    DUGUTIGI = 'dugutigi'
    DRPC = 'DRPC'
    DRDSES = 'DRDSES'
    DRS = 'DRS'

    ROLES = {
        GOUVERNEUR: "Gouverneur",
        PREFET: "Préfet",
        SOUS_PREFET: "Sous-préfet",
        MAIRE: "Maire",
        DUGUTIGI: "Chef de village",
        DRPC: "DRPC",
        DRDSES: "DRDSES",
        DRS: "DRS"
    }

    identity = models.CharField(max_length=50, primary_key=True,
                                verbose_name="Numéro téléphone")
    name = models.CharField(max_length=200, blank=True, null=True,
                            verbose_name="Nom")
    role = models.SlugField(max_length=200, choices=ROLES.items(),
                            null=True, blank=True,
                            verbose_name="Rôle")
    position = models.CharField(max_length=500, blank=True, null=True,
                                verbose_name="Fonction")
    location = models.ForeignKey('Location', verbose_name="Localité")
    active = models.BooleanField(default=True, verbose_name="Actif ?")

    def __str__(self):
        return self.short_name

    @property
    def verbose_identity(self):
        return phonenumber_repr(self.identity)

    @property
    def short_name(self):
        if self.name:
            return self.name
        return self.verbose_identity

    @property
    def is_main(self):
        return self.location.main_contact == self

    @property
    def full_name(self):
        if not self.role and not self.location:
            return self.short_name
        elif not self.location:
            return "{name}, {role}".format(name=self.short_name,
                                           role=self.verbose_role)
        elif not self.role:
            return "{name} de {location}".format(
                name=self.short_name, location=self.location.name)
        else:
            return "{name}, {role_location}".format(
                name=self.short_name, role_location=self.display_role)

    @property
    def display_role(self):
        return "{role} de {location}".format(
            role=self.ROLES.get(self.role) or "Inconnu",
            location=self.location.name)

    @property
    def sms_name(self):
        if self.name:
            return "{name}/{num}".format(name=self.name,
                                         num=self.verbose_identity)
        return self.verbose_identity

    @classmethod
    def get_verbose_role(cls, role):
        return cls.ROLES.get(role) or "Inconnu"

    @property
    def verbose_role(self):
        return self.get_verbose_role(self.role)

    @classmethod
    def get_or_none(cls, identity):
        try:
            return cls.objects.get(identity=normalized_phonenumber(identity))
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_or_create(cls, identity, location):
        qs = Contact.objects.filter(identity=identity)
        if qs.count():
            contact = qs.get()
            if location != contact.location:
                contact.location = location
                contact.save()
            return contact
        else:
            return Contact.objects.create(
                identity=identity,
                name=phonenumber_repr(identity),
                location=location)

    @classmethod
    def all_from(cls, location_types, identies_only=False):
        qs = cls.objects.filter(active=True) \
                        .filter(location__location_type__in=location_types)
        if identies_only:
            return [c['identity'] for c in qs.values('identity')]
        else:
            return qs

    @classmethod
    def dispatch_list(cls, gouverneur=False, drpc=False, verbose=False):
        dlist = []
        if gouverneur:
            dlist.append(cls.GOUVERNEUR)
        if drpc:
            dlist.append(cls.DRPC)

        dlist += [cls.DRS, cls.DRDSES, cls.MAIRE, cls.SOUS_PREFET, cls.PREFET]

        if verbose:
            return [cls.get_verbose_role(r) for r in dlist]

        return dlist

    def disable(self):
        self.active = False
        self.save()

    def enable(self):
        self.active = True
        self.save()

    @property
    def messages(self):
        return SMSMessage.objects.filter(identity=self.identity) \
                                 .order_by('-created_on')
