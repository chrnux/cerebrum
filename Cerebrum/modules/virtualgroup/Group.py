# -*- coding: utf-8 -*-
# Copyright 2016 University of Oslo, Norway
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


"""Implementation of the Virtual group core"""

from types import MethodType
from Cerebrum import Utils
from Cerebrum.Group import Group
from Cerebrum.Errors import NotFoundError


def populator(*types):
    """Create a method get_populator matching types.
    :param types: Matched against to return this method.
    """
    def fn(meth):
        def make_populator(cls):
            def populate(self, creator_id=None, visibility=None, name=None,
                         description=None, expire_date=None, parent=None,
                         group_type='normal_group', **kw):
                """Populate group instance's attributes without database access
                """
                super(cls, self).populate(creator_id=creator_id,
                                          visibility=visibility,
                                          name=name,
                                          description=description,
                                          expire_date=expire_date,
                                          group_type=group_type,
                                          parent=parent)
                if group_type in types:
                    return getattr(self, meth.__name__)(
                        group_type=types[0],
                        **kw)

            return MethodType(populate, None, cls)
        meth.make_populator = make_populator
        return meth
    return fn


class GroupPopulatorInjector(Utils.mark_update):
    """Metaclass for installing a proper get_populator into class"""
    def __new__(cls, name, parents, dct):
        """Find populators and populate dct['get_populator']"""
        ret = super(GroupPopulatorInjector, cls).__new__(cls, name, parents,
                                                         dct)
        found = False
        for member in dct.values():
            if hasattr(member, 'make_populator'):
                assert not found
                ret.populate = member.make_populator(ret)
                found = True
        return ret


class VirtualGroup(Group):
    __read_attr__ = ('__in_db', 'virtual_group_type')
    __metaclass__ = GroupPopulatorInjector

    def clear(self):
        super(VirtualGroup, self).clear()
        self.clear_class(VirtualGroup)
        self.__updated = []

    def populate(self, creator_id=None, visibility=None, name=None,
                 description=None, expire_date=None, parent=None,
                 group_type='normal_group', **kw):
        """Populate group instance's attributes without database access
        """
        super(VirtualGroup, self).populate(creator_id=creator_id,
                                           visibility=visibility,
                                           name=name,
                                           description=description,
                                           expire_date=expire_date,
                                           parent=parent, **kw)
        if isinstance(group_type, self.const.VirtualGroup):
            self.virtual_group_type = group_type
        elif group_type is None or group_type == 'normal_group':
            self.virtual_group_type = self.const.vg_normal_group
        else:
            self.virtual_group_type = self.const.VirtualGroup(group_type)

    def write_db(self):
        """Write group instance to database.

        If this instance has a ``entity_id`` attribute (inherited from
        class Entity), this Group entity is already present in the
        Cerebrum database, and we'll use UPDATE to bring the instance
        in sync with the database.

        Otherwise, a new entity_id is generated and used to insert
        this object.

        """
        is_new = super(VirtualGroup, self).write_db()
        try:
            gt = self.query_1(
                """
                SELECT virtual_group_type
                FROM [:table schema=cerebrum name=virtual_group_info]
                WHERE group_id = :gid
                """, {'gid': self.entity_id})
            if gt != self.virtual_group_type:
                self.execute(
                    """
                    UPDATE [:table schema=cerebrum name=virtual_group_info]
                    SET group_type = :group_type
                    WHERE group_id = :g_id
                    """, {'g_id': self.entity_id,
                          'group_type': self.virtual_group_type})
        except NotFoundError:
            self.execute(
                """
                INSERT INTO [:table schema=cerebrum name=virtual_group_info]
                (group_id, virtual_group_type)
                VALUES (:g_id, :group_type)""",
                {'g_id': self.entity_id,
                 'group_type': self.virtual_group_type})
        try:
            del self.__in_db
        except AttributeError:
            pass
        self.__in_db = True
        self.__updated = []
        return is_new

    def delete(self):
        """ Delete group and entity from database."""
        if self.__in_db:
            self.execute("""
            DELETE FROM [:table schema=cerebrum name=virtual_group_info]
            WHERE group_id=:g_id""", {'g_id': self.entity_id})
        # Class Group is a core class; when its delete() method is
        # called, the underlying Entity object is also removed.
        super(VirtualGroup, self).delete()

    def find(self, group_id):
        """Connect object to group with ``group_id`` in database."""
        self.__super.find(group_id)
        try:
            self.virtual_group_type = self.query_1(
                """
                SELECT virtual_group_type
                FROM [:table schema=cerebrum name=virtual_group_info]
                WHERE group_id = :g_id""", {'g_id': group_id})
        except NotFoundError:
            self.virtual_group_type = self.const.vg_normal_group
        try:
            del self.__in_db
        except AttributeError:
            pass
        self.__in_db = True
        self.__updated = []

    def add_member(self, member_id):
        """Add L{member_id} to this group.

        :type member_id: int
        :param member_id:
          Member (id) to add to this group. This must be an entity
          (i.e. registered in entity_info).
        """
        if self.virtual_group_type == self.const.vg_normal_group:
            return super(VirtualGroup, self).add_member(member_id)
        raise RuntimeError("Group {} is a virtual group; can't add members"
                           .format(self.group_name))

    def remove_member(self, member_id):
        """Remove L{member_id}'s membership from this group.

        :type member_id: int
        :param member_id: Member (id) to remove from this group.
        """
        if self.virtual_group_type == self.const.vg_normal_group:
            return super(VirtualGroup, self).remove_member(member_id)
        raise RuntimeError("Group {} is a virtual group; can't remove members"
                           .format(self.group_name))
