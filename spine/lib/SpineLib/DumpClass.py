# -*- coding: iso-8859-1 -*-

# Copyright 2004, 2005 University of Oslo, Norway
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

from SpineClass import SpineClass

import Registry
registry = Registry.get_registry()

class Struct:
    def __init__(self, data_type):
        self.data_type = data_type

class DumpClass(SpineClass):
    primary = []
    slots = []
    method_slots = []

    def __new__(cls, objects):
        return SpineClass.__new__(cls, objects, cache=None)

    def __init__(self, objects):
        self.structs = []
        self._objects = objects

        for i in objects:
            s = {'reference':i}
            for key, value in zip(i.primary, i.get_primary_key()):
                s[key.name] = value
            self.structs.append(s)

        SpineClass.__init__(self)

registry.register_class(DumpClass)


# arch-tag: 13564347-7aef-4465-8b83-c3d694bf6951
