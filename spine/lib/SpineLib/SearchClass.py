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


from __future__ import generators

from Cerebrum.extlib import sets

from DatabaseClass import DatabaseTransactionClass
from Builder import Attribute, Method
from SpineExceptions import ClientProgrammingError

import Registry
registry = Registry.get_registry()

def create_id_iterator(start=0):
    while 1:
        yield start
        start += 1

class SearchClass(DatabaseTransactionClass):
    """Base class for all searchclasses.

    Implements the search-method which finds the attributes which have
    been set, and send them into the generated create_search_method.
    """
    
    primary = []
    slots = []
    search_slots = []
    method_slots = [Method('clear', None, write=True)]

    search_id_iterator = create_id_iterator()

    def __init__(self, search_id=None):
        super(SearchClass, self).__init__(search_id)
        self._unions = sets.Set()
        self.mark = None

    def save(self):
        self.updated.clear()

    def reset(self):
        self.updated.clear()

    def create_primary_key(cls, search_id=None):
        #if search_id is None:
        search_id = cls.search_id_iterator.next()

        return (search_id, )

    create_primary_key = classmethod(create_primary_key)

    def get_alive_slots(self): # FIXME: d�rlig navn?
        alive = {}
        mine = object() # make a unique object
        for attr in self.slots:
            val = getattr(self, attr.get_name_private(), mine)
            if val is not mine:
                alive[attr.name] = val
        return alive

    def clear(self):
        for attr in self.slots:
            if hasattr(self, attr.get_name_private()):
                delattr(self, attr.get_name_private())

    def search(self, **vargs):
        alive = self.get_alive_slots()
        alive.update(vargs)
        return self._search(**alive)

def set_unions(self, unions):
    self._unions = unions
def set_intersections(self, intersections):
    self._intersections = intersections
def set_differences(self, differences):
    self._differences = differences

args = [('search_classes', [SearchClass])]
SearchClass.register_method(Method('set_unions', None, args, write=True), set_unions)
SearchClass.register_method(Method('set_intersections', None, args, write=True), set_intersections)
SearchClass.register_method(Method('set_differences', None, args, write=True), set_differences)

registry.register_class(SearchClass)


# arch-tag: c3bdb45f-2d86-4863-8df7-6a3f33776bde
