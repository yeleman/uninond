#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from py3compat import implements_to_string
from django.db import models
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger(__name__)


@implements_to_string
class Location(models.Model):

    class Meta:
        app_label = 'uninond'
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")

    REGION = 'region'
    CERCLE = 'cercle'
    ARRONDISSEMENT = 'arrondissement'
    COMMUNE = 'commune'
    VFQ = 'vfq'

    TYPES = {
        REGION: "Région",
        CERCLE: "Cercle",
        ARRONDISSEMENT: "Arrondissement",
        COMMUNE: "Commune",
        VFQ: "Village"
    }

    slug = models.SlugField(max_length=50, unique=True, null=True)
    name = models.CharField(max_length=150)
    parent = models.ForeignKey('self', null=True, blank=True)
    location_type = models.SlugField(max_length=50, choices=TYPES.items())
    main_contact = models.ForeignKey('Contact',
                                     related_name='locations',
                                     blank=True, null=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_or_none(cls, slug):
        try:
            return cls.objects.get(slug=slug)
        except cls.DoesNotExist:
            return None

    @property
    def parent_name(self):
        return "{name} / {parent}".format(name=self.name,
                                          parent=self.parent.name)

    @property
    def full_name(self):
        return "{type} de {name}".format(
            name=self.name,
            type=self.TYPES.get(self.location_type))

    @property
    def display_name(self):
        if self.location_type in (self.REGION, self.CERCLE):
            return self.name
        if self.location_type in (self.ARRONDISSEMENT, self.COMMUNE):
            return "{name}/{cercle}".format(
                name=self.name,
                cercle=self.get_cercle())
        return "{name}/{commune}/{cercle}".format(
            name=self.name,
            commune=self.get_commune(),
            cercle=self.get_cercle())

    def get_commune(self):
        return self.get_of_type(self.COMMUNE)

    def get_maire(self):
        return getattr(self.get_commune(), 'main_contact', None)

    def get_arrondissement(self):
        return self.get_of_type(self.ARRONDISSEMENT)

    def get_sous_prefet(self):
        return getattr(self.get_arrondissement(), 'main_contact', None)

    def get_cercle(self):
        return self.get_of_type(self.CERCLE)

    def get_prefet(self):
        return getattr(self.get_cercle(), 'main_contact', None)

    def get_region(self):
        return self.get_of_type(self.REGION)

    def get_gouverneur(self):
        return getattr(self.get_region(), 'main_contact', None)

    def get_of_type(self, location_type):
        for ancestor in self.get_ancestors(True):
            if ancestor.location_type == location_type:
                return ancestor

    def get_ancestors(self, include_self=False):
        ancestors = []
        if not self.parent and not include_self:
            return ancestors

        location = self if include_self else self.parent
        ancestors.append(location)

        while location.parent:
            location = location.parent
            ancestors.append(location)

        return ancestors

    def ancestors_contacts(self, roles, identies_only=False):
        from uninond.models.Contacts import Contact
        qs = Contact.objects.filter(active=True) \
                            .filter(role__in=roles) \
                            .filter(
            location__in=self.get_ancestors(True))
        if identies_only:
            return [c['identity'] for c in qs.values('identity')]
        else:
            return qs

    def get_children(self):
        return self.objects.filter(parent=self)

    @property
    def level(self):
        return len(self.get_ancestors())
