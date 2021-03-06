#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2016 University of Oslo, Norway
#
# This file is part of Cerebrum.
#
# Cerebrum is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Cerebrum is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cerebrum; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import decimal
import xmlrpclib
from mx import DateTime


class AttributeDict(dict):
    """Adds attribute access to keys, ie. a['knott'] == a.knott"""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


def native_to_xmlrpc(obj, no_unicodify=0):
    """Translate Python objects to XML-RPC-usable structures."""
    if obj is None:
        return ':None'
    elif isinstance(obj, (str, unicode)):
        if isinstance(obj, str) and not no_unicodify:
            obj = unicode(obj, 'iso8859-1')
        if obj.startswith(":"):
            return ":" + obj
        return obj
    elif isinstance(obj, (tuple, list)):
        obj_type = type(obj)
        return obj_type([native_to_xmlrpc(x) for x in obj])
    elif isinstance(obj, dict):
        obj_type = type(obj)
        return obj_type(
            [(native_to_xmlrpc(x, no_unicodify=1), native_to_xmlrpc(obj[x]))
             for x in obj])
    elif isinstance(obj, (int, long, float)):
        return obj
    elif decimal and isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, (xmlrpclib.DateTime, DateTime.DateTimeType)):
        # TODO: This only works for Postgres.  Needs support
        # in Database.py as the Python database API doesn't
        # define any return type for Date

        # python2.3 don't want floats here
        return xmlrpclib.DateTime(tuple([int(i) for i in obj.tuple()]))
    else:
        raise ValueError("Unrecognized parameter type: '{!r}' {!r}".format(
            obj, getattr(obj, '__class__', type(obj))))


def xmlrpc_to_native(obj):
    """Translate XML-RPC-usable structures back to Python objects"""
    #  We could have used marshal.{loads,dumps} here,
    # but then the Java client would have trouble
    # encoding/decoding requests/responses.
    if isinstance(obj, unicode):
        obj = obj.encode('ISO-8859-1', 'ignore')
    if isinstance(obj, str):
        if obj == ':None':
            return None
        elif obj.startswith(":"):
            return obj[1:]
        return obj
    elif isinstance(obj, (tuple, list)):
        obj_type = type(obj)
        return obj_type([xmlrpc_to_native(x) for x in obj])
    elif isinstance(obj, dict):
        return AttributeDict([(xmlrpc_to_native(x), xmlrpc_to_native(obj[x]))
                              for x in obj])
    elif isinstance(obj, (int, long, float)):
        return obj
    elif isinstance(obj, xmlrpclib.DateTime):
        return DateTime.ISO.ParseDateTime(obj.value)
    elif isinstance(obj, xmlrpclib.Binary):
        return xmlrpc_to_native(obj.data)
    else:
        # unknown type, no need to recurse
        return obj
