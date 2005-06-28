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

from Cerebrum.extlib import sets

from SpineLib.Builder import Method
from SpineLib.DatabaseClass import DatabaseClass, DatabaseAttr

from Entity import Entity
from Group import Group
from Types import EntityType, GroupMemberOperationType

from SpineLib import Registry
registry = Registry.get_registry()

table = 'group_member'
class GroupMember(DatabaseClass):
    primary = [
        DatabaseAttr('group', table, Group),
        DatabaseAttr('operation', table, GroupMemberOperationType),
        DatabaseAttr('member', table, Entity),
        DatabaseAttr('member_type', table, EntityType)
    ]
    slots = []
    method_slots = []
    db_attr_aliases = {
        table:{
            'group':'group_id',
            'member':'member_id'
        }
    }

registry.register_class(GroupMember)

def get_group_members(self):
    s = registry.GroupMemberSearcher((self, 'get_group_members'))
    s.set_group(self)
    return s.search()

Group.register_method(Method('get_group_members', [GroupMember]), get_group_members)

UnionType = GroupMemberOperationType(name='union')
IntersectionType = GroupMemberOperationType(name='intersection')
DifferenceType = GroupMemberOperationType(name='difference')

GroupType = EntityType(name='group')

def _get_members(group, group_members):
    unions = sets.Set()
    intersects = sets.Set()
    differences = sets.Set()

    for entity, operation in group_members[group]:
        if entity.get_type() is GroupType:
            members = get_members(entity)
        else:
            members = sets.Set([entity])

        if operation is UnionType:
            unions.update(members)
        elif operation is IntersectionType:
            intersects.update(members)
        elif operation is DifferenceType:
            differences.update(members)

    if intersects:
        unions.intersection_update(intersects)
    if differences:
        unions.difference_update(differences)

    return unions

# FIXME: burde kanskje sjekke for sykler?

def get_groups(self):
    group_members = {}
    # BUG: Returnerer ogs� grupper hvor vedkommende skal v�re
    # difference-tatt-bort. :(
    def get(entity):
        s = registry.GroupMemberSearcher(('get_groups', entity))
        s.set_member(entity)
        for i in s.search():
            group = i.get_group()
            if group not in group_members:
                group_members[group] = []
            group_members[group].append((entity, i.get_operation()))
            get(group)
    get(self)

    return [i for i in group_members if _get_members(i, group_members)]

Entity.register_method(Method('get_groups', [Group]), get_groups)

def get_members(self):
    """
    Return a flattened list of all entities in this group and its subgroups.
    """

    group_members = {}

    def get(group):
        if group not in group_members:
            group_members[group] = []
        for i in get_group_members(group):
            member = i.get_member()
            group_members[group].append((member, i.get_operation()))

            if member.get_type() is GroupType:
                get(member)
    get(self)

    return list(_get_members(self, group_members))

Group.register_method(Method('get_members', [Entity]), get_members)

def add_member(self, entity, operation):
    obj = self._get_cerebrum_obj()
    obj.add_member(entity.get_id(), entity.get_type().get_id(), operation.get_id())
    obj.write_db()

Group.register_method(Method('add_member', None, args=[('entity', Entity), ('operation', GroupMemberOperationType)], write=True), add_member)

def remove_group_member(self, group_member):
    obj = self._get_cerebrum_obj()
    obj.remove_member(group_member.get_member().get_id(), group_member.get_operation().get_id())
    obj.write_db()

Group.register_method(Method('remove_group_member', None, args=[('group_member', GroupMember)], write=True), remove_group_member)

# arch-tag: 62cc34ca-6553-4fcc-bed2-70c0d7dcf6e9
