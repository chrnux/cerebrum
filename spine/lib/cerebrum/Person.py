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

from Cerebrum.Utils import Factory

from SpineLib.DatabaseClass import DatabaseAttr
from SpineLib.Builder import Method
from CerebrumClass import CerebrumAttr, CerebrumDbAttr


from Entity import Entity
from Account import Account
from Date import Date
from Types import EntityType, GenderType, NameType, SourceSystem
from Commands import Commands

from SpineLib import Registry
registry = Registry.get_registry()

__all__ = ['Person']

table = 'person_info'
class Person(Entity):
    slots = Entity.slots + [
        CerebrumDbAttr('export_id', table, str, write=True),
        CerebrumDbAttr('birth_date', table, Date, write=True),
        CerebrumDbAttr('gender', table, GenderType, write=True),
        CerebrumDbAttr('deceased_date', table, Date, write=True),
        CerebrumDbAttr('description', table, str, write=True)
    ]
    method_slots = Entity.method_slots + [
        Method('get_primary_account', Account)
    ]

    Entity.db_attr_aliases[table] = {
        'id':'person_id'
    }
    cerebrum_attr_aliases = {}
    cerebrum_class = Factory.get('Person')
    entity_type = 'person'

    def get_primary_account(self):
        account_id = self._get_cerebrum_obj().get_primary_account()
        if account_id is None:
            return None
        return Account(account_id)

registry.register_class(Person)

def create(self, birthdate, gender, full_name, source_system):
    db = self.get_database()
    new_id = Person._create(db, birthdate.strftime('%Y-%m-%d'), gender.get_id())

    person = Person(db, new_id)

    full = NameType(db, name='FULL')
    person.set_name(full_name, full, source_system)

    return person

Commands.register_method(Method('create_person', Person, write=True,
                         args=[('birthdate', Date), ('gender', GenderType), ('full_name', str), ('source_system', SourceSystem)]), create)

# arch-tag: 7b2aca28-7bca-4872-98e1-c45e08faadfc
