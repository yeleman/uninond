#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from django.shortcuts import render, redirect
from django.http import Http404
from django import forms
from django.contrib import messages

from uninond.models.FloodEvents import FloodEvent
from uninond.models.SMSMessages import SMSMessage
from uninond.models.Locations import Location
from uninond.models.Contacts import Contact
from uninond.tools import normalized_phonenumber


logger = logging.getLogger(__name__)


class ContactUpdateForm(forms.ModelForm):

    class Meta:
        model = Contact
        exclude = ('identity', 'location', 'active')

    is_main_contact = forms.BooleanField(
        required=False,
        label="Contact principal ?",
        help_text="Attention, remplacera le contact de la localité"
                  "par cette personne (utilisé dans les notifications).")

    def __init__(self, *args, **kwargs):
        super(ContactUpdateForm, self).__init__(*args, **kwargs)

        instance = kwargs.get('instance', None)
        if instance is not None:
            self.fields['is_main_contact'].initial = instance.is_main


class AddContactForm(forms.ModelForm):

    class Meta:
        model = Contact
        exclude = ('active',)

    is_main_contact = forms.BooleanField(
        required=False,
        label="Contact principal ?",
        help_text="Attention, remplacera le contact de la localité"
                  "par cette personne (utilisé dans les notifications).")

    def __init__(self, *args, **kwargs):
        super(AddContactForm, self).__init__(*args, **kwargs)

        def display_name(location):
            return "{} {}".format(
                "-".join(["" for _ in range(location.level)]),
                location.display_name)

        locations = [(location.id, display_name(location))
                     for location in Location.objects.all()]

        self.fields['location'].choices = locations

    def clean_identity(self):
        identity = normalized_phonenumber(self.cleaned_data.get('identity'))
        if not identity:
            raise forms.ValidationError(
                "Numéro incorrect : %(value)s",
                code='invalid',
                params={'value': self.cleaned_data.get('identity')})

        return identity


class SearchForm(forms.Form):
    query = forms.CharField(max_length=100, required=False)


def home(request, **kwargs):
    context = {'page': 'dashboard'}

    context.update({
        'events': FloodEvent.objects.all().order_by('-created_on')
        })

    return render(request,
                  kwargs.get('template_name', 'dashboard.html'),
                  context)


def event_details(request, ident, **kwargs):
    context = {'page': 'dashboard'}

    event = FloodEvent.get_or_none(ident)
    if event is None:
        raise Http404("Évennement introuvable: `{}`".format(ident))

    context.update({'event':  event})

    return render(request,
                  kwargs.get('template_name', 'event.html'),
                  context)


def sms_list(request, **kwargs):
    context = {'page': 'sms'}

    context.update({
        'smses': SMSMessage.objects.all().order_by('-created_on')
        })

    return render(request,
                  kwargs.get('template_name', 'smses.html'),
                  context)


def addressbook(request, **kwargs):
    context = {'page': 'addressbook'}

    qs = Contact.objects.all()

    if request.method == 'POST':

        action = request.POST.get('action') or "search"

        if action == "search":
            form = SearchForm(request.POST)
            if form.is_valid():
                query = form.cleaned_data.get('query')
                if query:
                    qs = qs.filter(name__icontains=query)
        else:
            form = SearchForm()

        if action == "add":
            add_form = AddContactForm(request.POST)
            if add_form.is_valid():
                identity = add_form.cleaned_data.get('identity')
                if Contact.get_or_none(identity) is not None:
                    return redirect('contact_details',
                                    identity=identity)

                contact = Contact.objects.create(
                    identity=identity,
                    name=add_form.cleaned_data.get('name') or None,
                    role=add_form.cleaned_data.get('role') or None,
                    position=add_form.cleaned_data.get('position') or None,
                    location=add_form.cleaned_data.get('location') or None)

                if add_form.cleaned_data.get('is_main_contact'):
                    contact.location.main_contact = contact
                    contact.location.save()

                messages.success(request, "Le contact «{}» a été créé."
                                          .format(contact))
                return redirect('addressbook')
            else:
                context.update({'open_add_form': True})
        else:
            add_form = AddContactForm()
    else:
        form = SearchForm()
        add_form = AddContactForm()

    context.update({
        'contacts': qs.order_by('name'),
        'form': form,
        'add_form': add_form
        })

    return render(request,
                  kwargs.get('template_name', 'contacts.html'),
                  context)


def contact_details(request, identity, **kwargs):
    context = {'page': 'addressbook'}

    contact = Contact.get_or_none(identity)
    if contact is None:
        raise Http404("Contact introuvable: `{}`".format(identity))

    if request.method == 'POST':
        form = ContactUpdateForm(request.POST)
        if form.is_valid():
            contact.name = form.cleaned_data.get('name') or None
            contact.role = form.cleaned_data.get('role') or None
            contact.position = form.cleaned_data.get('position') or None
            contact.save()

            if form.cleaned_data.get('is_main_contact'):
                contact.location.main_contact = contact
                contact.location.save()
            else:
                if contact.location.main_contact == contact:
                    contact.location.main_contact = None
                    contact.location.save()

            return redirect('contact_details',
                            identity=identity)
    else:
        form = ContactUpdateForm(instance=contact)

    context.update({'contact':  contact,
                    'form': form})

    return render(request,
                  kwargs.get('template_name', 'contact.html'),
                  context)


def contact_disable(request, identity, **kwargs):

    contact = Contact.get_or_none(identity)
    if contact is None:
        raise Http404("Contact introuvable: `{}`".format(identity))

    contact.disable()

    return redirect('contact_details', identity=identity)


def contact_enable(request, identity, **kwargs):

    contact = Contact.get_or_none(identity)
    if contact is None:
        raise Http404("Contact introuvable: `{}`".format(identity))

    contact.enable()

    return redirect('contact_details', identity=identity)
