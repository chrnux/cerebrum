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

# FIXME: Remove PgSQL dependency
import pyPgSQL.PgSQL
import Cerebrum
from Cerebrum.extlib import sets

from Builder import Attribute
from Searchable import Searchable
from Dumpable import Dumpable
from SpineClass import SpineClass
from SpineExceptions import DatabaseError, NotFoundError

__all__ = [
    'DatabaseAttr', 'DatabaseClass', 'ConvertableAttribute',
]

class ConvertableAttribute(object):
    """Mixin for attributes which need to be converted.

    This mixin is for attributes which may need to be converted when loaded or
    saved in the database. Attributes which inherit this class should accept
    convert_to and convert_from in their __init__-method, so they can be
    overridden for that specific attribute.
    """
    
    def convert_to(self, value):
        if isinstance(value, SpineClass):
            key = value.get_primary_key()
            assert len(key) == 1
            return key[0]
        else:
            return value

    def convert_from(self, value):
        if value is None:
            return None
        # Depends on the db-driver, should be done in a cleaner way.
        if isinstance(value, pyPgSQL.PgSQL.PgNumeric):
            value = int(value)
        return self.data_type(value)

class DatabaseAttr(Attribute, ConvertableAttribute):
    """Object representing an attribute from the database.

    Used to represent an attribute which can be found in the database.
    The value of this attribute will be loaded/saved from/to the
    database.

    You can include your own methods for converting to and from the
    database with the attr 'convert_to' and 'convert_from'.

    Since this attribute has knowledge of the database, you can use it
    with the generic search/create/delete-methods found in DatabaseClass.
    """
    
    def __init__(self, name, table, data_type, exceptions=None, write=False,
                 convert_to=None, convert_from=None, optional=False):

        if exceptions is None:
            exceptions = []
        exceptions += [DatabaseError]

        Attribute.__init__(self, name, data_type, exceptions=exceptions,
                write=write, optional=optional)

        self.table = table

        if convert_to is not None:
            self.convert_to = convert_to
        if convert_from is not None:
            self.convert_from = convert_from

def get_real_name(map, attr, table=None):
    """Finds the real name for attr in map.

    Map should be a dict with dicts in it, where the table is the key in
    the outer dict, and you have DatabaseAttr.name as key in the inner
    dict, the value of the inner dict should be the real name the slot has
    in the database. The map is also used when primary-keys have diffrent
    name in diffrent databases.
    """
    if table is None:
        table = attr.table
    if table in map and attr.name in map[table]:
        return map[table][attr.name]
    else:
        return attr.name

class DatabaseClass(SpineClass, Searchable, Dumpable):
    """Mixin class which adds support for the database.

    This class adds support for working directly against the database,
    with generic load/save for attributes, generic create/delete for
    classes, and generic searching.
    
    All SQL-calls in Spine/cerebrum should be implementet here.
    """
    
    db_attr_aliases = {}
    db_table_order = []

    def __wrapped_execute(self, sql, keys):
        """Wraps around the execute call on the database to catch exceptions
        and rethrow proper Spine exceptions."""
        db = self.get_database()
        try:
            return db.execute(sql, keys)
        except Cerebrum.Errors.DatabaseConnectionError, e:
            raise DatabaseError('Connection to the database failed', str(e), sql)
        except Cerebrum.Errors.DatabaseException, e:
            raise DatabaseError('Error during query', str(e), sql)
        except Cerebrum.Database.DatabaseError, e:
            raise DatabaseError('Error during query', str(e), sql)

    def __wrapped_query(self, sql, keys):
        """Wraps around the query call on the database to catch exceptions
        and rethrow proper Spine exceptions."""
        db = self.get_database()
        try:
            return db.query(sql, keys)
        except Cerebrum.Errors.DatabaseConnectionError, e:
            raise DatabaseError('Connection to the database failed', str(e), sql)
        except Cerebrum.Errors.DatabaseException, e:
            raise DatabaseError('Error during query', str(e), sql)
        except Cerebrum.Database.DatabaseError, e:
            raise DatabaseError('Error during query', str(e), sql)

    def __wrapped_query_1(self, sql, keys):
        """Wraps around the query_1 call on the database to catch exceptions
        and rethrow proper Spine exceptions."""
        db = self.get_database()
        try:
            return db.query_1(sql, keys)
        except Cerebrum.Errors.NotFoundError, e:
            raise NotFoundError(*e.args)
        except Cerebrum.Errors.TooManyRowsError, e:
            raise TooManyMatchesError(*e.args)
        except Cerebrum.Errors.DatabaseConnectionError, e:
            raise DatabaseError('Connection to the database failed', str(e), sql)
        except Cerebrum.Errors.DatabaseException, e:
            raise DatabaseError('Error during query', str(e), sql)
        except Cerebrum.Database.DatabaseError, e:
            raise DatabaseError('Error during query', str(e), sql)

    def _load_db_attributes(self, attributes=None):
        """Load 'attributes' from the database.

        This method load attributes in 'attributes' from the database
        through one SQL call.
        """
        if attributes is None:
            attributes = self._db_load_attributes

        tables = sets.Set([i.table for i in attributes])

        sql = 'SELECT '
        sql += ', '.join(['%s.%s AS %s' % (attr.table, self._get_real_name(attr), attr.name) for attr in attributes])
        sql += ' FROM '
        sql += ', '.join(tables)
        sql += ' WHERE '

        tmp = []
        for table in tables:
            tmp.append(' AND '.join(['%s.%s = :%s' % (table, self._get_real_name(attr, table), attr.name) for attr in self.primary]))
        sql += ' AND '.join(tmp)

        keys = {}
        for i in self.primary:
            keys[i.name] = i.convert_to(getattr(self, i.get_name_private()))

        row = self.__wrapped_query_1(sql, keys)
        
        if len(attributes) == 1:
            row = {attributes[0].name:row}

        for i in attributes:
            value = row[i.name]
            value = i.convert_from(value)
            setattr(self, i.get_name_private(), value)

    def _save_all_db(self):
        """Save all attributes to the database.
        
        This method will save all attributes in this class which have
        been updated, and is a subclass of DatabaseAttr, through one
        SQL-call for each db-table.
        """
        for table, attributes in self._get_sql_tables().items():
            # only update tables with changed attributes
            changed_attributes = []
            for i in self.updated:
                if i in attributes and i in self._db_save_attributes:
                    changed_attributes.append(i)

            if not changed_attributes:
                continue

            sql = 'UPDATE %s SET %s' % (
                table,
                ', '.join(['%s=:%s' % (self._get_real_name(attr), attr.name) for attr in changed_attributes])
            )

            sql += ' WHERE '
            tmp = []
            for attr in self.primary:
                tmp.append('%s.%s = :%s' % (table, self._get_real_name(attr, table), attr.name))
            sql += ' AND '.join(tmp)

            keys = {}
            for i in self.primary + changed_attributes:
                keys[i.name] = attr.convert_to(getattr(self, i.get_name_private()))

            self.__wrapped_execute(sql, keys)

    def _delete(self):
        """Generic method for deleting this instance from the database.
        
        Creates the SQL query and executes it to remove the rows in the
        database which this instance fills. The reverse of db_table_order
        is used if set, and primary slots is used to create the where clause.
        """
        table_order = self.db_table_order[:].reverse()

        # Prepare primary keys for each table to delete from
        tables = {}
        for attr in self.primary:
            if not isinstance(attr, DatabaseAttr):
                continue
            if attr.table not in tables:
                tables[attr.table] = {}
            value = attr.convert_to(getattr(self, attr.get_name_get())())
            tables[attr.table][self._get_real_name(attr)] = value
        
        # If db_table_order is set, we delete in the opposite order.
        for table in (table_order or tables.keys()):
            sql = "DELETE FROM %s WHERE " % table
            sql += " AND ".join(['%s = :%s' % (a, a) for a in tables[table].keys()])
            self.__wrapped_execute(sql, tables[table])

    def _create(cls, db, *args, **vargs):
        """Generic method for creating instances in the database.
        
        Creates the SQL query and executes it to create instances of the
        class 'cls' in the database. This method is "private" because you
        need to supply the primary key for the new instance. You should
        also check that enough arguments are given to create a new
        instance.

        Example of "public" create method:
        def create_example(self, example):
            db = self.get_database()
            id = int(db.nextval('example'))
            Example._create(db, id, example)
            return Example(id, write_locker=self.get_writelock_holder())

        Notice the write_locker argument when returning the new object.
        """
        map = cls.map_args(*args, **vargs)
        tables = cls._get_sql_tables()

        for table in (cls.db_table_order or tables.keys()):
            tmp = {}
            for attr in [attr for attr in tables[table] if attr in map.keys()]:
                tmp[cls._get_real_name(attr, table)] = attr.convert_to(map[attr])
            sql = "INSERT INTO %s (%s) VALUES (:%s)" % (
                    table, ", ".join(tmp.keys()), ", :".join(tmp.keys()))
            self.__wrapped_execute(sql, tmp)

    _create = classmethod(_create)

    def _get_sql_tables(cls):
        tables = {}
        for attr in cls.slots:
            if not isinstance(attr, DatabaseAttr):
                continue
            if attr.table not in tables:
                tables[attr.table] = []
            tables[attr.table].append(attr)
            
        return tables

    _get_sql_tables = classmethod(_get_sql_tables)

    def _get_real_name(cls, *args, **vargs):
        return get_real_name(cls.db_attr_aliases, *args, **vargs)

    _get_real_name = classmethod(_get_real_name)

    def create_search_method(cls):
        """Generic method for searching for instances of class 'cls'.

        Used when creating a searchclass for class 'cls', to add a method
        which searches for instances of the class.
        """
        def search(self, _sql_only=False, sql_where='', *args, **vargs):
            """Search for instances of the original class.

            Creates SQL query for finding instances of the original class
            which matches arguments given in args and vargs.
            Returns a list of objects returned from the SQL query.
            
            If the DatabaseAttr has the attribute 'like', string comparison
            is used and wildcards are supported in the where clause. 'less'
            and 'more' gives '<' and '>' in the where clause.
            """
            map = self.map_args(*args, **vargs) # Dict with Attribute: value

            tables = []
            attrs = []
            for attr in cls.slots:
                if not isinstance(attr, DatabaseAttr) or attr.optional:
                    continue
                if attr.table not in tables:
                    tables.append(attr.table)
                attrs.append(attr)
            
            def _get_real_name(*args, **vargs):
                return get_real_name(self.db_attr_aliases, *args, **vargs)

            unique_key = 's%s' % id(self)
            
            def convert_value(attr, value):
                """Returns the where query for the attr & key.
                
                Prepares the value to be inserted into the query,
                and returns the where clause for the query.
                """
                args = (attr.table, _get_real_name(attr), unique_key + attr.name)
                value = attr.convert_to(value)
                if getattr(attr, 'like', False):
                    whr = 'LOWER(%s.%s) LIKE :%s' % args
                    value = value.replace("*","%").replace("?", "_")
                    value = value.lower()
                elif getattr(attr, 'less', False):
                    whr = '%s.%s < :%s' % args
                elif getattr(attr, 'more', False):
                    whr = '%s.%s > :%s' % args
                elif getattr(attr, 'exists', False):
                    if value:
                        whr = '%s.%s is not :%s' % args
                    else:
                        whr = '%s.%s is :%s' % args
                    value = None
                else:
                    whr = '%s.%s = :%s' % args
                return (whr, value)
        
            # Prepare the where clause and values to supply with the sql query
            where = []
            if sql_where:
                where.append(sql_where)
            values = {}
            for attr, value in map.items():
                if not isinstance(attr, DatabaseAttr):
                    raise Exception('unable to search with attribute %s' % attr)
                whr, val = convert_value(attr, value)
                where.append(whr)
                values[unique_key + attr.name] = val

                # Then we need to add it
                if attr.optional:
                    if attr.table not in tables:
                        tables.append(attr.table)
                    attrs.append(attr)

            table = tables[0]
            for i in cls.primary:
                tmp = '%s.%s = %%s.%%s' % (table, _get_real_name(i, table))
                for table in tables[1:]:
                    where.append(tmp % (table, _get_real_name(i, table)))
            
            # Create sql query
            sql = 'SELECT '

            join = ''
            for key, op in [('_intersections', 'INTERSECT'), ('_differences', 'EXCEPT'), ('_unions', 'UNION')]:
                for s in getattr(self, key, ()):
                    i, j = s.search(_sql_only=True)
                    join += ' %s (%s)' % (op, i)
                    values.update(j)

            if join or _sql_only:
                attrs = cls.primary

            if self.mark and _sql_only:
                sql += '%s.%s AS %s' % (self.mark.table, _get_real_name(self.mark), self.mark.name)
            else:
                sql += ', '.join(['%s.%s AS %s' % (attr.table, _get_real_name(attr),
                                                   attr.name) for attr in attrs])
            sql += ' FROM '
            sql += ', '.join(tables)
            if where:
                sql += ' WHERE '
                sql += ' AND '.join(where)

            sql += join

            if _sql_only:
                return sql, values

            # Build objects from the query result, and return them in a list.
            try:
                rows = self.get_database().query(sql, values)
            except Cerebrum.Errors.DatabaseConnectionError, e:
                raise DatabaseError('Connection to the database failed', str(e), sql)
            except Cerebrum.Errors.DatabaseException, e:
                raise DatabaseError('Error during query', str(e), sql)
            except Cerebrum.Database.DatabaseError, e:
                raise DatabaseError('Error during query', str(e), sql)

            objects = []
            for row in rows:
                tmp = {}
                for attr in attrs:
                    value = row[attr.name]
                    tmp[attr.name] = attr.convert_from(value)
                objects.append(cls(**tmp))

            return objects
        return search
    
    create_search_method = classmethod(create_search_method)
    
    def build_methods(cls):
        """Create get/set methods for slots."""
        if '_db_load_attributes' not in cls.__dict__:
            cls._db_load_attributes = []
            cls._db_save_attributes = []

        for attr in cls.slots:
            if not isinstance(attr, DatabaseAttr):
                continue

            if attr.optional:
                def create_load(attr):
                    def load_db_attribute(self):
                        self._load_db_attributes([attr])
                    return load_db_attribute
                load = create_load(attr)
            else:
                load = cls._load_db_attributes
            save = cls._save_all_db

            if not hasattr(cls, attr.get_name_load()):
                if not attr.optional:
                    cls._db_load_attributes.append(attr)
                setattr(cls, attr.get_name_load(), load)

            if attr.write and not hasattr(cls, attr.get_name_save()):
                cls._db_save_attributes.append(attr)
                setattr(cls, attr.get_name_save(), save)

        super(DatabaseClass, cls).build_methods()
        cls.build_search_class()
        cls.build_dumper_class()
 
    build_methods = classmethod(build_methods)

# arch-tag: 9e06972b-c3b1-45ff-bdad-e32d35d3ab81
