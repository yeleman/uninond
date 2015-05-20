#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.utils.translation import ugettext_lazy as _


class SMSReply(object):

    INFO = 'info'
    ERROR = 'error'
    WARNING = 'warning'
    SUCCESS = 'success'

    LEVEL_PREFIXES = {
        INFO: "",
        ERROR: _("ECHEC"),
        WARNING: _("ATTENTION"),
        SUCCESS: _("OK")
    }

    STANDARD_REPLIES = {
        'error_saving_report': {
            'level': ERROR,
            'text': _("Impossible d'enregistrer la demande. "
                      "Reessayez plus tard ou contactez DRPC.")},
    }

    def __init__(self, message, namespace=None):
        self._message = message
        self._namespace = namespace or None

    @property
    def message(self):
        return self._message

    @property
    def namespace(self):
        return self._namespace

    def prefix(self, level=None):
        ns = self.namespace
        level_str = self.LEVEL_PREFIXES.get(level).format()

        if ns is None and level is None:
            return None

        parts = [ns, level_str]
        try:
            parts.remove(None)
        except:
            pass

        return "[{}]".format(":".join(parts))

    def body(self, text, level=INFO):
        if self.prefix(level) is not None:
            return "{prefix} {text}".format(
                prefix=self.prefix(level), text=text)
        return text

    def send(self, text, level=INFO):
        return self.message.respond(self.body(text, level))

    def info(self, text):
        return self.send(text, self.INFO)

    def error(self, text):
        return self.send(text, self.ERROR)

    def warning(self, text):
        return self.send(text, self.WARNING)

    def success(self, text):
        return self.send(text, self.SUCCESS)

    def std(self, slug):
        rpl = self.STANDARD_REPLIES.get(slug)
        if rpl is None:
            return True
        return self.send(rpl.get('text'), rpl.get('level'))

    def __str__(self):
        return self.message
