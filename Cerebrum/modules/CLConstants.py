# -*- coding: iso-8859-1 -*-
# Copyright 2003 University of Oslo, Norway
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

import cereconf
from Cerebrum.DatabaseAccessor import DatabaseAccessor
from Cerebrum import Constants
from Cerebrum.Constants import _CerebrumCode

class _ChangeTypeCode(_CerebrumCode):
    _lookup_code_column = 'change_type_id'
    # _lookup_str_column = 'status_str'
    _lookup_table = '[:table schema=cerebrum name=change_type]'
    # _insert_dependency = _PersonAffiliationCode
    _lookup_desc_column = 'msg_string'
    _key_size = 2

    # TODO: accept numeric code value
    def __init__(self, category, type, msg_string):
        super(_ChangeTypeCode, self).__init__(category)
        self.category = category
        self.type = type
        self.int = None
        self.msg_string = msg_string
        
    def __str__(self):
        return "%s:%s" % (self.category, self.type)

    def __int__(self):
        if self.int is None:
            self.int = int(self.sql.query_1("""
            SELECT change_type_id FROM [:table schema=cerebrum name=change_type]
            WHERE category=:category AND type=:type""", {
                'category': self.category,
                'type': self.type}))
        return self.int

    def insert(self):
        self._pre_insert_check()
        self.sql.execute("""
        INSERT INTO %(code_table)s
          (%(code_col)s, category, type ,%(desc_col)s)
        VALUES
          ( %(code_seq)s, :category, :type, :desc)""" % {
            'code_table': self._lookup_table,
            'code_col': self._lookup_code_column,
            'desc_col': self._lookup_desc_column,
            'code_seq': self._code_sequence},
                         {'category': self.category,
                          'type': self.type,
                          'desc': self.msg_string})
        

class CLConstants(Constants.Constants):

    """Singleton whose members make up all needed coding values.

    Defines a number of variables that are used to get access to the
    string/int value of the corresponding database key."""

    ChangeType = _ChangeTypeCode

    group_add = _ChangeTypeCode('e_group', 'add',
                                'added %(subject)s to %(dest)s')
    group_rem = _ChangeTypeCode('e_group', 'rem',
                                'removed %(subject)s from %(dest)s')
    group_create = _ChangeTypeCode('e_group', 'create',
                                   'created %(subject)s')
    group_mod = _ChangeTypeCode('e_group', 'mod',
                                'modified %(subject)s')
    group_destroy = _ChangeTypeCode('e_group', 'destroy',
                                    'destroyed %(subject)s')

    account_create =  _ChangeTypeCode('e_account', 'create',
                                      'created %(subject)s')
    account_mod =  _ChangeTypeCode('e_account', 'mod',
                                   'modified %(subject)s')
    account_password =  _ChangeTypeCode('e_account', 'password',
                                        'new password for %(subject)s')
    # TODO: account_move is obsolete, remove it
    account_move =  _ChangeTypeCode('e_account', 'move',
                                    '%(subject)s moved to %(param_name)s')
    account_home_updated = _ChangeTypeCode('e_account', 'home_update',
                                           'home updated for %(subject)s')
    account_home_added = _ChangeTypeCode('e_account', 'home_added',
                                           'home added for %(subject)s')
    account_home_removed = _ChangeTypeCode('e_account', 'home_removed',
                                           'home removed for %(subject)s')
    spread_add =  _ChangeTypeCode('spread', 'add',
                                  'add spread for %(subject)s')
    spread_del =  _ChangeTypeCode('spread', 'delete',
                                  'delete spread for %(subject)s')
    account_type_add = _ChangeTypeCode('ac_type', 'add',
                                       'ac_type add for account %(subject)s')
    account_type_mod = _ChangeTypeCode('ac_type', 'mod',
                                       'ac_type mod for account %(subject)s')
    account_type_del = _ChangeTypeCode('ac_type', 'del',
                                       'ac_type del for account %(subject)s')
    disk_add = _ChangeTypeCode('disk', 'add', 'new disk %(subject)s')
    disk_mod = _ChangeTypeCode('disk', 'mod', 'update disk %(subject)s')
    disk_del = _ChangeTypeCode('disk', 'del', "delete disk %(subject)s")
    host_add = _ChangeTypeCode('host', 'add', 'new host %(subject)s')
    host_mod = _ChangeTypeCode('host', 'mod', 'update host %(subject)s')
    host_del = _ChangeTypeCode('host', 'del', 'del host %(subject)s')
    ou_create = _ChangeTypeCode('ou', 'create', 'created OU %(subject)s')
    ou_mod = _ChangeTypeCode('ou', 'mod', 'modified OU %(subject)s')
    ou_unset_parent = _ChangeTypeCode('ou', 'unset_parent',
                                      'parent for %(subject)s unset')
    ou_set_parent = _ChangeTypeCode('ou', 'set_parent',
                                    'parent for %(subject)s set to %(dest)s')
    person_create = _ChangeTypeCode('person', 'create', 'created %(subject)s')
    person_update = _ChangeTypeCode('person', 'update', 'update %(subject)s')
    person_name_del = _ChangeTypeCode('person', 'name_del', 'del name for %(subject)s')
    person_name_add = _ChangeTypeCode('person', 'name_add', 'add name for %(subject)s')
    person_name_mod = _ChangeTypeCode('person', 'name_mod', 'mod name for %(subject)s')
    person_ext_id_del = _ChangeTypeCode('person', 'ext_id_del', 'del ext_id for %(subject)s')
    person_ext_id_mod = _ChangeTypeCode('person', 'ext_id_mod', 'mod ext_id for %(subject)s')
    person_ext_id_add = _ChangeTypeCode('person', 'ext_id_add', 'add ext_id for %(subject)s')
    person_aff_add = _ChangeTypeCode('person', 'aff_add', 'add aff for %(subject)s')
    person_aff_mod = _ChangeTypeCode('person', 'aff_mod', 'mod aff for %(subject)s')
    person_aff_del = _ChangeTypeCode('person', 'aff_del', 'del aff for %(subject)s')
    person_aff_src_add = _ChangeTypeCode('person', 'aff_src_add',
                                         'add aff_src for %(subject)s')
    person_aff_src_mod = _ChangeTypeCode('person', 'aff_src_mod',
                                         'mod aff_src for %(subject)s')
    person_aff_src_del = _ChangeTypeCode('person', 'aff_src_del',
                                         'del aff_src for %(subject)s')
    quarantine_add = _ChangeTypeCode('quarantine', 'add',
                                     'add quarantine for %(subject)s')
    quarantine_mod = _ChangeTypeCode('quarantine', 'mod',
                                     'mod quarantine for %(subject)s')
    quarantine_del = _ChangeTypeCode('quarantine', 'del',
                                     'del quarantine for %(subject)s')
    entity_add = _ChangeTypeCode('entity', 'add', 'add entity %(subject)s')
    entity_del = _ChangeTypeCode('entity', 'del', 'del entity %(subject)s')
    entity_name_add = _ChangeTypeCode('entity_name', 'add',
                                      'add entity_name for %(subject)s')
    entity_name_mod = _ChangeTypeCode('entity_name', 'mod',
                                      'mod entity_name for %(subject)s')
    entity_name_del = _ChangeTypeCode('entity_name', 'del',
                                      'del entity_name for %(subject)s')
    entity_cinfo_add = _ChangeTypeCode('entity_cinfo', 'add',
                                       'add entity_cinfo for %(subject)s')
    entity_cinfo_del = _ChangeTypeCode('entity_cinfo', 'del',
                                       'del entity_cinfo for %(subject)s')
    entity_addr_add = _ChangeTypeCode('entity_addr', 'add',
                                      'add entity_addr for %(subject)s')
    entity_addr_del = _ChangeTypeCode('entity_addr', 'del',
                                      'del entity_addr for %(subject)s')
    # TBD: Is it correct to have posix_demote in this module?
    posix_demote =  _ChangeTypeCode('posix', 'demote',
                                    'demote posix %(subject)s')

    def __init__(self, database):
        super(CLConstants, self).__init__(database)

        # TBD: Works, but is icky -- _CerebrumCode or one of its
        # superclasses might use the .sql attribute themselves for
        # other purposes; should be cleaned up.
        _ChangeTypeCode.sql = database

def main():
    from Cerebrum.Utils import Factory
    from Cerebrum import Errors

    Cerebrum = Factory.get('Database')()
    co = CLConstants(Cerebrum)

    skip = dir(Cerebrum)
    skip.append('map_const')
    for x in filter(lambda x: x[0] != '_' and not x in skip, dir(co)):
        try:
            print "co.%s: %s = %d" % (x, getattr(co, x), getattr(co, x))
        except Errors.NotFoundError:
            print "NOT FOUND: co.%s" % x

if __name__ == '__main__':
    main()
