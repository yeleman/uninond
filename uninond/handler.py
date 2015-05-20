#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import os

from django.utils import timezone
from django.conf import settings

from uninond.tools import exec_cmd
from uninond.models.Locations import Location
from uninond.models.FloodEvents import FloodEvent
from uninond.models.Contacts import Contact
from uninond.reply import SMSReply
from uninond.tools import (normalized_phonenumber, dispatch_sms,
                           datetime_repr, fake_message)

PROJECT_BRAND = "DRPC"
logger = logging.getLogger(__name__)


def test(message):
    msg = "Received on {date}"
    try:
        _, content = message.content.split()
        msg += ": {content}"
    except:
        content = None

    message.respond(msg.format(date=timezone.now(), content=content))
    return True


def echo(message):
    try:
        kw, args = message.content.split(" ", 1)
    except:
        args = "-"
    message.respond(args)
    return True


def uninond_sms_handler(message):

    # migration to non-snisi prefixed SMS
    if message.content.startswith('uninond '):
        message.text = message.content[6:]
        message.save()

    logger.debug("Incoming SMS from {}: {}".format(
        message.identity, message.content))

    keywords = {'test': test,
                'echo': echo,
                'alerte': create_event,
                'alert': create_event,

                # avertir gouvernorat
                'ag': event_confirmed,
                'fw': event_confirmed,
                'refer': event_confirmed,
                'confirm': event_confirmed,
                'confirme': event_confirmed,
                'confirmer': event_confirmed,

                # maitre de la situation
                # secours suffisants, aggravation improbable
                'ms': event_restrained,
                'ssc': event_restrained,  # situation sous controle
                'es': event_restrained,  # effectifs suffisants
                'contenue': event_restrained,

                # mission annulee
                'ma': event_cancelled,
                'ras': event_cancelled,  # rien a signaler
                'annule': event_cancelled,
                'annuler': event_cancelled,
                }

    for keyword, handler in keywords.items():
        if message.content.lower().startswith(keyword):
            try:
                return handler(message)
            except Exception as e:
                logger.exception(e)
                message.respond("Une erreur s'est produite.")
                return True

    if len(normalized_phonenumber(message.identity)) == 12:
        message.respond("Message non pris en charge.")
    return False


def check_metadata(flooded_area, homes_destroyed, dead, wounded):
    # ensure flooded area is within proper range (1-3)
    if flooded_area not in range(1, 4):
        return ("La surface submergée ({}) doit être comprise "
                "entre 1 et 3."
                .format(flooded_area))

    # ensure data is within proper boundaries
    if homes_destroyed not in range(500):
        return ("Le nombre de maisons détruites ({}) "
                "semble erronné."
                .format(homes_destroyed))

    if dead not in range(100):
        return ("Le nombre de morts ({}) semble erronné."
                .format(dead))

    if wounded not in range(500):
        return ("Le nombre de blessés ({}) semble erronné."
                .format(wounded))


def create_event(message):

    reply = SMSReply(message, PROJECT_BRAND)

    # create variables from text messages.
    try:
        args_names = ['kw', 'location_slug',
                      'flooded_area', 'homes_destroyed',
                      'dead', 'wounded']
        args_values = message.content.strip().lower().split()
        arguments = dict(zip(args_names, args_values))
        assert len(arguments) == len(args_names)
    except (ValueError, AssertionError):
        # failure to split means we proabably lack a data or more
        # we can't process it.
        return reply.error("Le format du SMS est incorrect.")

    # convert form-data to int or bool respectively
    try:
        for key, value in arguments.items():
            if key not in ('kw', 'location_slug'):
                arguments[key] = int(value)
            if key == 'location_slug':
                arguments[key] = value.upper()
    except:
        logger.warning("Unable to convert SMS data to int: {}"
                       .format(message.content))
        # failure to convert means non-numeric value which we can't process.
        return reply.error("Les données sont malformées.")

    # retrieve location
    location = Location.get_or_none(arguments['location_slug'])
    if location is None or location.location_type != Location.VFQ:
        return reply.error("Votre code de village `{}` est incorrect."
                           .format(arguments['location_slug']))

    error_msg = check_metadata(arguments['flooded_area'],
                               arguments['homes_destroyed'],
                               arguments['dead'], arguments['wounded'])
    if error_msg:
        return reply.error(error_msg)

    # check for duplicate event
    now = timezone.now()
    duplicate = FloodEvent.duplicate(location=location, created_on=now)
    if duplicate is not None:
        # mark message as part of that duplicate
        duplicate.add_message(message)
        repl = reply.warning("L'inondation de {location} a déjà été signalée "
                             "le {at} par {by}. Merci de patienter ou de "
                             "rappeller la DRPC au {hotline}."
                             .format(location=location,
                                     at=datetime_repr(duplicate.created_on),
                                     by=duplicate.created_by,
                                     hotline=settings.HOTLINE_NUMBER))
        duplicate.add_message(repl)
        return repl

    # find or create contact
    contact = Contact.get_or_create(
        identity=normalized_phonenumber(message.identity),
        location=location)

    # ready to create event
    event = FloodEvent.objects.create(
        created_on=now,
        created_by=contact,
        location=location,
        status=FloodEvent.CREATED,
        initial_flooded_area=arguments['flooded_area'],
        initial_homes_destroyed=arguments['homes_destroyed'],
        initial_dead=arguments['dead'],
        initial_wounded=arguments['wounded'])
    event.add_message(message)

    # dispatch alert to DRPC (with identifier)
    text_base = ("{location} (cercle de {cercle}) a déclaré une "
                 "inondation avec surface submergée de {fa}, {hd} maisons "
                 "détruites, {nd} morts et {nw} blessés. Alerte par {contact}."
                 " Maire de {commune}: {maire}.").format(
        location=event.location,
        cercle=event.location.get_cercle(),
        fa=FloodEvent.get_verbose_flooded_area(event.initial_flooded_area),
        hd=event.initial_homes_destroyed,
        nd=event.initial_dead,
        nw=event.initial_wounded,
        contact=event.created_by,
        commune=event.location.get_commune(),
        maire=getattr(event.location.get_maire(), 'sms_name', "-")
        )
    text_drpc = "[ALERTE INONDATION:{ident}] {base}".format(
        ident=event.verbose_ident, base=text_base)
    dispatch_sms(text_drpc, [Contact.DRPC], location)
    # record forward in log
    event.add_message(
        fake_message(Contact.get_verbose_role(Contact.DRPC), text_drpc))

    # dispatch alert to all but DRPC (without identifier)
    text_all = "[ALERTE INONDATION (NON CONFIRMÉE)] {base}".format(
        ident=event.ident, base=text_base)
    dispatch_sms(text_all, Contact.dispatch_list(), location)

    # add broadcast to event
    event.add_message(fake_message(
        ", ".join(Contact.dispatch_list(verbose=True)), text_all))

    # trigger server events
    exec_cmd(os.path.join(settings.BASE_DIR, 'uninond',
                          'scripts', 'incoming_alert.sh'))

    repl = reply.success("Votre alerte inondation pour {location} a bien "
                         "été prise en compte. La DRPC est informée "
                         "ainsi que les autorités. Vous allez être rappellé. "
                         "En cas de besoin, appellez la DRPC au {hotline}."
                         .format(location=location.full_name,
                                 hotline=settings.HOTLINE_NUMBER))
    event.add_message(repl)
    return repl


def event_confirmed(message):
    reply = SMSReply(message, PROJECT_BRAND)

    # create variables from text messages.
    try:
        args_names = ['kw', 'event_ident',
                      'flooded_area', 'homes_destroyed',
                      'dead', 'wounded', 'comment']
        args_values = message.content.strip().lower().split()
        arguments = dict(zip(args_names, args_values))
        assert len(arguments) >= len(args_names) - 1
    except (ValueError, AssertionError):
        # failure to split means we proabably lack a data or more
        # we can't process it.
        return reply.error("Le format du SMS est incorrect.")

    # convert form-data to int or bool respectively
    try:
        for key, value in arguments.items():
            if key not in ('kw', 'event_ident', 'comment'):
                arguments[key] = int(value)
            if key == 'event_ident':
                arguments[key] = value
    except:
        logger.warning("Unable to convert SMS data to int: {}"
                       .format(message.content))
        # failure to convert means non-numeric value which we can't process.
        return reply.error("Les données sont malformées.")

    # retrieve location
    event = FloodEvent.get_or_none(arguments['event_ident'])
    if event is None:
        return reply.error("Votre code d'inondation ({}) est incorrect."
                           .format(arguments['event_ident']))

    if event.closed:
        repl = reply.error("Cette inondation ({event}) est déjà cloturée "
                           "({status} le {at})."
                           .format(event=event.verbose_ident,
                                   status=event.verbose_status,
                                   at=datetime_repr(event.closed_on)))
        event.add_message(repl)
        return repl

    # update data
    error_msg = check_metadata(arguments['flooded_area'],
                               arguments['homes_destroyed'],
                               arguments['dead'], arguments['wounded'])
    if error_msg:
        repl = reply.error(error_msg)
        event.add_message(repl)
        return repl

    comment = arguments.get('comment', '').strip() or None

    now = timezone.now()
    # find or create contact
    contact = Contact.get_or_create(
        identity=normalized_phonenumber(message.identity),
        location=event.location)

    # update event
    event.confirm(flooded_area=arguments['flooded_area'],
                  homes_destroyed=arguments['homes_destroyed'],
                  dead=arguments['dead'],
                  wounded=arguments['wounded'],
                  comment=comment,
                  by=contact, at=now)
    event.add_message(message)

    # broadcast update to all
    text_base = ("{location} (cercle de {cercle}) a déclaré une "
                 "inondation avec surface submergée de {fa}, {hd} maisons "
                 "détruites, {nd} morts et {nw} blessés. Alerte par {contact}."
                 " Maire de {commune}: {maire}.").format(
        location=event.location,
        cercle=event.location.get_cercle(),
        fa=FloodEvent.get_verbose_flooded_area(event.flooded_area),
        hd=event.homes_destroyed,
        nd=event.dead,
        nw=event.wounded,
        contact=event.created_by,
        commune=event.location.get_commune(),
        maire=getattr(event.location.get_maire(), 'sms_name', "-")
        )

    if event.confirmed_comment:
        comment_txt = " Détails: {}".format(event.confirmed_comment)
    else:
        comment_txt = ""

    # dispatch alert to all
    text_all = "[ALERTE INONDATION (CONFIRMÉE)] {base}{comment}".format(
        ident=event.ident, base=text_base, comment=comment_txt)
    dispatch_sms(text_all,
                 Contact.dispatch_list(gouverneur=True, drpc=True),
                 event.location)

    # add broadcast to event
    event.add_message(fake_message(
        ", ".join(Contact.dispatch_list(gouverneur=True,
                                        drpc=True, verbose=True)),
        text_all))

    repl = reply.success("Merci. L'inondation {ident} a été confirmée. "
                         "Le gouvernorat et les autres acteurs ont "
                         "été prévenus."
                         .format(ident=event.verbose_ident))
    event.add_message(repl)
    return repl


def event_restrained(message):
    reply = SMSReply(message, PROJECT_BRAND)

    # create variables from text messages.
    try:
        args_names = ['kw', 'event_ident',
                      'flooded_area', 'homes_destroyed',
                      'dead', 'wounded']
        args_values = message.content.strip().lower().split()
        arguments = dict(zip(args_names, args_values))
        assert len(arguments) == len(args_names)
    except (ValueError, AssertionError):
        # failure to split means we proabably lack a data or more
        # we can't process it.
        return reply.error("Le format du SMS est incorrect.")

    # convert form-data to int or bool respectively
    try:
        for key, value in arguments.items():
            if key not in ('kw', 'event_ident'):
                arguments[key] = int(value)
            if key == 'event_ident':
                arguments[key] = value
    except:
        logger.warning("Unable to convert SMS data to int: {}"
                       .format(message.content))
        # failure to convert means non-numeric value which we can't process.
        return reply.error("Les données sont malformées.")

    # retrieve location
    event = FloodEvent.get_or_none(arguments['event_ident'])
    if event is None:
        return reply.error("Votre code d'inondation ({}) est incorrect."
                           .format(arguments['event_ident']))

    if event.closed:
        repl = reply.error("Cette inondation ({event}) est déjà cloturée "
                           "({status} le {at})."
                           .format(event=event.verbose_ident,
                                   status=event.verbose_status,
                                   at=datetime_repr(event.closed_on)))
        event.add_message(repl)
        return repl

    # update data
    error_msg = check_metadata(arguments['flooded_area'],
                               arguments['homes_destroyed'],
                               arguments['dead'], arguments['wounded'])
    if error_msg:
        repl = reply.error(error_msg)
        event.add_message(repl)
        return repl

    now = timezone.now()
    # find or create contact
    contact = Contact.get_or_create(
        identity=normalized_phonenumber(message.identity),
        location=event.location)

    # update event
    event.restrain(flooded_area=arguments['flooded_area'],
                   homes_destroyed=arguments['homes_destroyed'],
                   dead=arguments['dead'],
                   wounded=arguments['wounded'],
                   by=contact, at=now)
    event.add_message(message)

    # broadcast update to all
    text_base = ("{location} (cercle de {cercle}) a déclaré une "
                 "inondation avec surface submergée de {fa}, {hd} maisons "
                 "détruites, {nd} morts et {nw} blessés. Alerte par {contact}."
                 " Maire de {commune}: {maire}.").format(
        location=event.location,
        cercle=event.location.get_cercle(),
        fa=FloodEvent.get_verbose_flooded_area(event.flooded_area),
        hd=event.homes_destroyed,
        nd=event.dead,
        nw=event.wounded,
        contact=event.created_by,
        commune=event.location.get_commune(),
        maire=getattr(event.location.get_maire(), 'sms_name', "-")
        )

    # dispatch alert to all
    text_all = "[ALERTE INONDATION (CONTENUE)] {base}".format(
        ident=event.ident, base=text_base)
    dispatch_sms(text_all, Contact.dispatch_list(drpc=True), event.location)

    # add broadcast to event
    event.add_message(fake_message(
        ", ".join(Contact.dispatch_list(drpc=True, verbose=True)), text_all))

    repl = reply.success("Merci. L'inondation {ident} a été marquée comme "
                         "contenue. Tous les acteurs (sauf le gouvernorat) "
                         "ont été prévenus."
                         .format(ident=event.verbose_ident))
    event.add_message(repl)
    return repl


def event_cancelled(message):
    reply = SMSReply(message, PROJECT_BRAND)

    # create variables from text messages.
    try:
        args_names = ['kw', 'event_ident']
        args_values = message.content.strip().lower().split()
        arguments = dict(zip(args_names, args_values))
        assert len(arguments) == len(args_names)
    except (ValueError, AssertionError):
        # failure to split means we proabably lack a data or more
        # we can't process it.
        return reply.error("Le format du SMS est incorrect.")

    # convert form-data to int or bool respectively
    try:
        for key, value in arguments.items():
            if key == 'event_ident':
                arguments[key] = value
    except:
        logger.warning("Unable to convert SMS data to int: {}"
                       .format(message.content))
        # failure to convert means non-numeric value which we can't process.
        return reply.error("Les données sont malformées.")

    # retrieve location
    event = FloodEvent.get_or_none(arguments['event_ident'])
    if event is None:
        return reply.error("Votre code d'inondation ({}) est incorrect."
                           .format(arguments['event_ident']))

    if event.closed:
        repl = reply.error("Cette inondation ({event}) est déjà cloturée "
                           "({status} le {at})."
                           .format(event=event.verbose_ident,
                                   status=event.verbose_status.lower(),
                                   at=datetime_repr(event.closed_on)))
        event.add_message(repl)
        return repl

    now = timezone.now()

    # find or create contact
    contact = Contact.get_or_create(
        identity=normalized_phonenumber(message.identity),
        location=event.location)

    # update event
    event.cancel(by=contact, at=now)
    event.add_message(message)

    # broadcast update to all
    text_base = ("{location} (cercle de {cercle}) avait déclaré une "
                 "inondation sans suite. Alerte par {contact}. "
                 "Maire de {commune}: {maire}. Contactez DRPC pour plus "
                 "de détails.").format(
        location=event.location,
        cercle=event.location.get_cercle(),
        contact=event.created_by,
        commune=event.location.get_commune(),
        maire=getattr(event.location.get_maire(), 'sms_name', "-")
        )

    # dispatch alert to all
    text_all = "[ALERTE INONDATION (ANNULÉE)] {base}".format(
        ident=event.ident, base=text_base)
    dispatch_sms(text_all, Contact.dispatch_list(drpc=True), event.location)

    # add broadcast to event
    event.add_message(fake_message(
        ", ".join(Contact.dispatch_list(drpc=True, verbose=True)), text_all))

    repl = reply.success("Merci. L'inondation {ident} a été annulée. "
                         "Tous les acteurs (sauf le gouvernorat) "
                         "ont été prévenus."
                         .format(ident=event.verbose_ident))
    event.add_message(repl)
    return repl
