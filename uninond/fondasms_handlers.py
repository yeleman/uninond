#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import random
import logging

from django.conf import settings
from django.utils import timezone
from fondasms.utils import datetime_from_timestamp, outgoing_for

from uninond.tools import (normalized_phonenumber,
                           operator_from_malinumber)
from uninond.tools import to_ascii
from uninond.models.SMSMessages import SMSMessage
from uninond.handler import uninond_sms_handler

logger = logging.getLogger(__name__)

# place holder for incoming phone numbers (phone device)
# with operator
INCOMING_NUMBERS_BY_OPERATOR = {}
INCOMING_NUMBERS_WITH_OPERATOR = {}


def snisi_outgoing_for(to, message):
    if settings.SMS_CONVERT_UNICODE_TO_ASCII:
        message = to_ascii(message)
    return outgoing_for(to=to, message=message)


def automatic_reply_handler(payload):
    # called by automatic reply logic
    # if settings.FONDA_SEND_AUTOMATIC_REPLY_VIA_HANDLER
    # Can be used to fetch or forge reply when we need more than
    # the static FONDA_AUTOMATIC_REPLY_TEXT
    return None


def handle_incoming_sms(payload):
    logger.debug("handle_incoming_sms")
    # on SMS received
    return handle_sms_call(payload)


def handle_incoming_call(payload):
    logger.debug("handle_incoming_call")
    # on call received
    return handle_sms_call(payload, event_type='call')


def handle_sms_call(payload, event_type=None):

    logger.debug("handle_sms_call")

    phone_number = normalized_phonenumber(payload.get('from').strip())
    if phone_number is None:
        return

    message = payload.get('message').strip()
    if not len(message):
        message = None

    if message is None and event_type == 'call':
        message = "ring ring"

    timestamp = payload.get('timestamp')
    received_on = datetime_from_timestamp(timestamp)

    try:
        msg, created = SMSMessage.objects.get_or_create(
            direction=SMSMessage.INCOMING,
            identity=phone_number,
            event_on=received_on,
            text=message,
            defaults={'created_on': timezone.now()})
    except Exception as e:
        logger.critical("Unable to save SMS into DB: {}".format(e))
        raise

    # don't re-run handler if message is handled (in case of duplicate)
    if msg.handled:
        logger.debug("Skipping duplicate message: {}".format(msg))
        return []

    # call specific handler
    msg_id = msg.id
    if uninond_sms_handler(msg):
        # we re-get the message from the DB
        # since handlers are allowed to destroy it (spam, etc)
        try:
            msg = SMSMessage.objects.get(id=msg_id)
        except SMSMessage.DoesNotExist:
            pass
        # might already be marked handled
        else:
            if not msg.handled:
                msg.handled = True
                msg.save()

    # send reply/pending messages
    return handle_outgoing_request(payload)


def handle_outgoing_status_change(payload):
    # we don't store outgoing messages for now
    return


def handle_device_status_change(payload):
    # we don't track device changes for now
    return


def check_meta_data(payload):
    # we don't track device changes for now
    return


def reply_with_phone_number(payload):
    end_user_phone = payload.get('from')
    if end_user_phone is not None:
        return get_phone_number_for(operator_from_malinumber(end_user_phone))
    return None


def handle_outgoing_request(payload):
    # logger.debug("handle_outgoing_request")
    outgoings = []
    for message in SMSMessage.objects.filter(
            direction=SMSMessage.OUTGOING, handled=False)[:10]:
        outgoings.append(snisi_outgoing_for(to=message.identity,
                                            message=message.content))
        message.handled = True
        message.save()
    return outgoings


def get_phone_number_for(operator):
    return random.choice(
        INCOMING_NUMBERS_BY_OPERATOR.get(operator, [None])) or None

for number in settings.FONDA_INCOMING_NUMBERS:
    operator = operator_from_malinumber(number)
    if operator not in INCOMING_NUMBERS_BY_OPERATOR.keys():
        INCOMING_NUMBERS_BY_OPERATOR.update({operator: []})
    INCOMING_NUMBERS_BY_OPERATOR[operator].append(number)
    INCOMING_NUMBERS_WITH_OPERATOR.update({number: operator})
