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

from DatabaseClass import DatabaseTransactionClass, DatabaseAttr
from Builder import Builder, Attribute, Method
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
    method_slots = [
        Method('clear', None),
        Method('get_signature', [str]), # FIXME: bedre navn?
        Method('set_search_limit', None, args=[('limit', int), ('offset', int)]),
        Method('dump_rows', [[str]], exceptions=[ClientProgrammingError])
    ]
    search_id_iterator = create_id_iterator()

    def __init__(self, *args, **vargs):
        super(SearchClass, self).__init__(*args, **vargs)

        self._joins = []
        self._operations = []
        self._search_limit = None
        self._order = []

    def save(self):
        self.updated.clear()

    def reset(self):
        self.updated.clear()

    def create_primary_key(cls, db):
        search_id = cls.search_id_iterator.next()

        return (db, search_id)

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
        self._order = []
        for attr in self.slots:
            if hasattr(self, attr.get_name_private()):
                delattr(self, attr.get_name_private())

    def set_search_limit(self, limit, offset):
        self._search_limit = limit, offset

    def search(self):
        db = self.get_database()
        names = self.get_signature()

        return [self.cls(db, **dict(zip(names, row))) for row in self.get_rows()]

    def get_signature(self):
        return [i.name for i in self.get_signature_slots()]

    def get_signature_slots(self):
        return [i for i in self.cls.slots if isinstance(i, DatabaseAttr)]

    def search_sql(self, only_attributes=()):
        slots, attributes, table, joins, args = self._get_sql()
        where, x = self._get_where()
        args.update(x)

        sql = 'SELECT %s FROM %s %s_%s' % (', '.join(only_attributes or attributes), table, self._get_alias(), table)
        if joins:
            sql += ' %s' % ' '.join(joins)
        if where:
            sql += ' WHERE %s' % ' AND '.join(where)

        if self._order:
            order = []
            for how, obj, attr in self._order:
                order.append('%s_%s.%s %s' % (obj._get_alias(), attr.table, obj.cls._get_real_name(attr), how))
            sql += ' ORDER BY %s' % ', '.join(order)


        # FIXME: this is not Oracle compliant
        if self._search_limit:
            sql += ' LIMIT %s OFFSET %s' % self._search_limit

        return sql, args

    def dump_rows(self):
        sql, args = self.search_sql()

        rows = []
        for row in self.get_database().query(sql, args):
            rows.append([str(i) for i in row])
        return rows

    def get_rows(self):
        db = self.get_database()
        sql, args = self.search_sql()
        slots = self.get_signature_slots()

        for row in db.query(sql, args):
            yield [attr.convert_from(db, value) for attr, value in zip(slots, row)]

    def get_all_rows(self):
        db = self.get_database()
        sql, args = self.search_sql()
        slots = []
        for i in self.get_search_objects():
            slots += i.get_signature_slots()

        for row in db.query(sql, args):
            yield [attr.convert_from(db, value) for attr, value in zip(slots, row)]

    def get_split_rows(self):
        indexes = []
        index = 0
        for obj in self.get_search_objects():
            n = len(obj.get_signature_slots())
            indexes.append((index, index + n))
            index += n

        for row in self.get_all_rows():
            yield [row[a:b] for (a, b) in indexes]

    def _get_alias(self):
        return 's%s' % self.get_primary_key()

    def _get_where(self):
        where = []
        args = {}
        alias = self._get_alias()
        for key, value in self.get_alive_slots().items():
            # FIXME: vi m� fiske dette hacket... stygt! -erikgors
            key_alias = '%s%s' % (alias, key)
            operator = '='
            like = False
            if key.endswith('_like'):
                key = key[:-len('_like')]
                like = True
                value = value.upper()
                # FIXME: flere tegn som m� escapes?
                for i in (('_', '\_'), ('%', '\%'), ('*', '%'), ('?', '_')):
                    value = value.replace(*i)
            if key.endswith('_more_than'):
                key = key[:-len('_more_than')]
                operator = '>'
            if key.endswith('_less_than'):
                key = key[:-len('_less_than')]
                operator = '<'
            if key.endswith('_exists'):
                key = key[:-len('_exists')]
                if value:
                    operator = 'IS NOT'
                else:
                    operator = 'IS'
                value = None

            attr = self.cls.get_attr(key)
            name = self.cls._get_real_name(attr)
            arg = '%s_%s' % (alias, name)
            if like:
                where.append('UPPER(%s_%s.%s) LIKE :%s' % (alias, attr.table, name, key_alias))
            else:
                where.append('%s_%s.%s %s :%s' % (alias, attr.table, name, operator, key_alias))
            args[key_alias] = attr.convert_to(value)

        for how, obj, attr1, attr2 in self._operations:
            table = self.cls.primary[0].table
            name1 = '%s_%s.%s' % (obj._get_alias(), attr1.table, obj.cls._get_real_name(attr1))
            name2 = '%s_%s.%s' % (alias, table, self.cls._get_real_name(attr2))
            # FIXME: h�pl�st..
            sql, x = obj.search_sql([name1])
            args.update(x)
            where.append('%s %s (%s)' % (name2, how, sql))

        return where, args

    def _get_sql(self):
        main_alias = self._get_alias()
        all_slots, all_attributes, main_table, all_joins, all_args = self.cls._get_sql(main_alias)

        for how, obj, attr1, attr2 in self._joins:

            # Check if all primary keys are fulfilled
            alive = obj.get_alive_slots()
            for i in obj.cls.primary:
                if i != attr1 and i.name not in alive:
                    raise ClientProgrammingError, '%s is missing primary key: %s' % (obj, i)

            alias = obj._get_alias()
            slots, attributes, table, joins, args = obj._get_sql()
            all_slots += slots
            all_attributes += attributes
            all_args.update(args)

            where, args = obj._get_where()
            all_args.update(args)
            n1 = '%s_%s.%s' % (alias, table, obj.cls._get_real_name(attr1))
            n2 = '%s_%s.%s' % (main_alias, attr2.table, self.cls._get_real_name(attr2))
            where.append('%s = %s' % (n1, n2))

            sql = '%s %s %s_%s' % (how, table, alias, table)
            if joins:
                sql += ' %s' % ' '.join(joins)
            sql += ' ON (%s)' % ' AND '.join(where)
            all_joins.append(sql)


        return all_slots, all_attributes, main_table, all_joins, all_args 

    def _get_join_attrs(self, attr, obj, obj_attr):
        data_type1 = self.cls
        data_type2 = obj.cls

        if attr:
            attr = data_type1.get_attr(attr)
            data_type1 = attr.data_type
        else:
            attr = data_type1.primary[0]

        if obj_attr:
            obj_attr = data_type2.get_attr(obj_attr)
            data_type2 = obj_attr.data_type
        else:
            obj_attr = data_type2.primary[0]

        if not (issubclass(data_type1, data_type2) or issubclass(data_type2, data_type1)):
            raise ClientProgrammingError, 'Is not of same type: %s (%s) and %s (%s)' % (attr.name, data_type1, obj_attr.name, data_type2)

        return attr, obj_attr
            
    def _order_by(self, how, obj, attr):
        self._order.append((how, obj, obj.cls.get_attr(attr)))

    def _add_join(self, how, attr, obj, obj_attr):
        attr, obj_attr = self._get_join_attrs(attr, obj, obj_attr)
        self._joins.append((how, obj, obj_attr, attr))

    def _add_intersection(self, how, attr, obj, obj_attr):
        attr, obj_attr = self._get_join_attrs(attr, obj, obj_attr)
        self._operations.append((how, obj, obj_attr, attr))


def add_join(self, attr, obj, obj_attr):
    self._add_join('JOIN', attr, obj, obj_attr)

def add_left_join(self, attr, obj, obj_attr):
    self._add_join('LEFT JOIN', attr, obj, obj_attr)

def add_intersection(self, attr, obj, obj_attr):
    self._add_intersection('IN', attr, obj, obj_attr)

def add_difference(self, attr, obj, obj_attr):
    self._add_intersection('NOT IN', attr, obj, obj_attr)

def get_search_objects(self):
    objects = [self]
    for how, obj, attr1, attr2 in self._joins:
        objects += obj.get_search_objects()

    return objects

def order_by(self, obj, attr):
    self._order_by('ASC', obj, attr)

def order_by_desc(self, obj, attr):
    self._order_by('DESC', obj, attr)

args = [('attr', str), ('obj', SearchClass), ('obj_attr', str)]
exceptions = [ClientProgrammingError]
for sig, m in (
    (Method('add_join', None, args=args, exceptions=exceptions), add_join),
    (Method('add_left_join', None, args=args, exceptions=exceptions), add_left_join),
    (Method('add_intersection', None, args=args, exceptions=exceptions), add_intersection),
    (Method('add_difference', None, args=args, exceptions=exceptions), add_intersection),
    (Method('order_by', None, args=[('obj', SearchClass), ('attr', str)], exceptions=exceptions), order_by),
    (Method('order_by_desc', None, args=[('obj', SearchClass), ('attr', str)], exceptions=exceptions), order_by_desc),
    (Method('get_search_objects', [SearchClass]), get_search_objects)):

    SearchClass.register_method(sig, m)

registry.register_class(SearchClass)

# arch-tag: c3bdb45f-2d86-4863-8df7-6a3f33776bde
