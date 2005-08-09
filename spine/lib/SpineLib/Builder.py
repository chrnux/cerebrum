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
import Cerebrum.Errors
from SpineExceptions import AccessDeniedError, DatabaseError, AlreadyLockedError, NotFoundError, ReadOnlyAttributeError, ServerProgrammingError, TooManyMatchesError, TransactionError, ObjectDeletedError

__all__ = ['Attribute', 'Method', 'Builder']

class Attribute(object):
    """Representation of an attribute in Spine.

    Attributes are used to collect metainfo about attributes which Spine
    should provide to clients and internally for Spine-classes.

    After Spine-classes are build, Spine will generate get/load-methods
    for attributes of this class, or subclass, which are listed, in a
    class or subclass of Builder, in primary and slots. Attributes which
    are writeable, will also get set/save-methods.
    """
    
    def __init__(self, name, data_type, exceptions=None, write=False, optional=False):
        """Initiate the attribute.

        name        - the name of the attribute in a string.
        data_type   - should be a class or a type, like Entity, list, str, None.
        exceptions  - list with all exceptions accessing this attribute might raise.
        write       - should be True if the clients are allowed to change this attribute.
        optional    - for attributes which is not mandatory to be set.

        optional attributes have exists-comparisation in searchobjects.
        """
        if exceptions is None:
            exceptions = []
        self.name = name
        assert type(data_type) != str
        assert type(exceptions) is list
        assert write in (True, False)
        assert optional in (True, False)

        self.data_type = data_type
        # Add the 'standard' exceptions to the attribute
        self.exceptions = exceptions + [
            AlreadyLockedError, DatabaseError, TransactionError, 
            AccessDeniedError, ServerProgrammingError,
            ObjectDeletedError,
        ]
        if optional:
            self.exceptions.append(NotFoundError)
            self.exceptions.append(TooManyMatchesError)
        self.write = write
        self.optional = optional

    def get_name_get(self):
        """The name provided to clients for reading the attribute value."""
        return 'get_' + self.name

    def get_name_set(self):
        """The name provided to clients for storing the attribute value."""
        return 'set_' + self.name

    def get_name_private(self):
        """Internal name for storing the value of the attribute."""
        return '_' + self.name

    def get_name_load(self):
        """Internal method for loading the value of the attribute."""
        return 'load_' + self.name

    def get_name_save(self):
        """Internal method for saving the value of the attriute."""
        return 'save_' + self.name

    def __repr__(self):
        return '%s(%s, %s)' % (self.__class__.__name__, `self.name`, `self.data_type`)

class Method(object):
    """Representation of a method in Spine.

    Methods are used to collect metainfo about methods which should be
    provided to clients. Information like arguments and return-tyoe is
    used when generating idl for use in corba.

    The methods will be wrapped to allow for authentication and access
    control.

    If the method is "write" and the object is a subclass of Locking, the
    object will be locked for writing before the method is called.
    """
    
    def __init__(self, name, data_type, args=None, exceptions=None, write=False):
        """Initiate the method.

        name        - the name of the method as a string.
        data_type   - the return type, should be a class or type: str, list, Entity.
        args        - a list with lists of arguments, like (("name", str), ("blipp", list")).
        exceptions  - list with all exceptions accessing this attribute might raise.
        write       - should be True for methods which change and object and/or require write locks.
        """
        if args is None:
            args = ()
        if exceptions is None:
            exceptions = []
        
        self.name = name
        assert type(data_type) != str
        assert type(exceptions) is list
        assert write in (True, False)

        self.data_type = data_type
        self.args = args
        self.exceptions = exceptions + [
            AlreadyLockedError, DatabaseError, TransactionError, 
            AccessDeniedError, ServerProgrammingError,
            ObjectDeletedError
        ]
        self.write = write
        self.doc = None

    def __repr__(self):
        return '%s(%s, %s)' % (self.__class__.__name__, `self.name`, `self.data_type`)

def create_lazy_get_method(attr):
    """Returns a method which will load the attribute if not already loaded."""
    def lazy_get(self):
        lazy = object() # a unique object.
        value = getattr(self, attr.get_name_private(), lazy)
        if value is lazy:
            loadmethod = getattr(self, attr.get_name_load(), None)
            if loadmethod is not None:
                loadmethod()
            value = getattr(self, attr.get_name_private(), None)
        return value
    return lazy_get

def create_set_method(attr):
    """Returns a method which will save the value, if its updated."""
    def set(self, value):
        # make sure the variable has been loaded
        orig = getattr(self, attr.get_name_get())

        if orig is not value: # we only set a new value if it is different
            # set the variable
            setattr(self,attr.get_name_private(), value)
            # mark it as updated
            self.updated.add(attr)
    return set

class Builder(object):
    """Core class for Spine for providing building functionality.
    
    Provides functionality for building methods for attributes, and for
    registering methods and attributes to the class.

    Attributes which subclasses should implement:
    'primary' should contain attributes which are unique for objects.
    'slots' should contain the rest of the attributes for the class.
    'method_slots' should contain methods which are implemented with
    the same name in the class.

    'builder_parents' and 'builder_children' are used for inheritance
    in CORBA.
    """
    
    primary = []
    slots = []
    method_slots = []

    builder_parents = None
    builder_children = None

    def __init__(self, *args, **vargs):
        map = self.map_args(*args, **vargs)
        
        # set all variables give in args and vargs
        for attr, value in map.items():
            var = attr.get_name_private()
            if not hasattr(self, var):
                setattr(self, var, value)

        # used to track changes
        if not hasattr(self, 'updated'):
            self.updated = sets.Set()

    def map_args(cls, *args, **vargs):
        """Returns a dict with attribute:value."""
        slotMap = dict([(i.name, i) for i in cls.slots])

        map = dict(zip(cls.slots, args))

        for key, value in vargs.items():
            attr = slotMap.get(key)
            if attr is None:
                continue
            map[attr] = value

        return map

    map_args = classmethod(map_args)

    def get_attr(cls, name):
        """Get the attribute in slots with name 'name'."""
        for attr in cls.slots:
            if attr.name == name:
                return attr
        raise ServerProgrammingError('Attribute %s not found in %s' % (name, cls))

    get_attr = classmethod(get_attr)

    def save(self):
        """Save all changed attributes."""
        saved = sets.Set()
        for attr in self.updated:
            save_method = getattr(self, attr.get_name_save(), None)
            if save_method not in saved and save_method is not None:
                save_method()
                saved.add(save_method)
        self.updated.clear()

    def reset(self, write_only=True):
        """Reset all changed attributes.
        
        Use write_only=False to reset attributes who are not writeable.
        Usefull for methods which alters the values the attributes represent
        without going through the usual Spine-API-methods.
        """
        loaded = sets.Set()
        for attr in self.slots:
            if attr not in self.primary:
                if write_only and not attr.write:
                    continue
                if hasattr(self, attr.get_name_private()):
                    delattr(self, attr.get_name_private())
        self.updated.clear()

    def create_primary_key(cls, *args, **vargs):
        """Create primary key from args and vargs.

        Used by the caching facility to identify a unique object.
        """
        names = [i.name for i in cls.primary]
        for var, value in zip(names, args):
            vargs[var] = value

        key = []
        for i in names:
            try:
                key.append(vargs[i])
            except KeyError:
                raise ServerProgrammingError('Argument %s missing during construction of primary key. Did you forget to pass an argument or a reference to the database?' % i)
        return tuple(key)

    create_primary_key = classmethod(create_primary_key)
 
    def register_attribute(cls, attribute, load=None, save=None, get=None,
                           set=None, overwrite=False, register=True):
        """Registers an attribute.

        attribute contains the name and data_type as it will be in the API
        load - loads the value for this attribute
        save - saves a new attribute
        get  - returns the value
        set  - sets the value. Validation can be done here.

        load/save/get/set must take self as first argument.

        overwrite - decides whether to overwrite existing definitions.

        If the attribute does not exist, it will be added to the class.
        If overwrite=True load/save/get/set will be overwritten if they
        allready exists.

        If get and set is None, the default behavior is for set and get to use
        self._`attribute.name`. load will then be run automatically by get if the
        attribute has not yet been loaded.

        If attribute is not write, save will not be used.
        """

        var_private = attribute.get_name_private()
        var_get = attribute.get_name_get()
        var_set = attribute.get_name_set()
        var_load = attribute.get_name_load()
        var_save = attribute.get_name_save()

        if get is None:
            get = create_lazy_get_method(attribute)

        if set is None and attribute.write:
                set = create_set_method(attribute)

        def quick_register(var, method):
            if method is not None: # no use setting the method to None
                if hasattr(cls, var) and not overwrite:
                    raise ServerProgrammingError('Accessor method %s already exists in %s' % (var, cls.__name__))
                setattr(cls, var, method)

        quick_register(var_load, load)
        quick_register(var_save, save)
        quick_register(var_get, get)
        if attribute.write:
            quick_register(var_set, set)

        if register:
            cls.slots.append(attribute)

    register_attribute = classmethod(register_attribute)

    def register_method(cls, method, method_func, overwrite=False):
        """Registers a method.
        
        Registers the method 'method', and points it towards the method
        'method_func'. If overwrite is True, an already existing method
        with the same name will be overwritten.
        """
        if hasattr(cls, method.name) and not overwrite:
            raise ServerProgrammingError('Method %s already exists in %s' % (method.name, cls.__name__))
        setattr(cls, method.name, method_func)
        method.doc = method_func.__doc__
        for m in cls.method_slots:
            if m.name == method.name:
                cls.method_slots.remove(m)
        cls.method_slots.append(method)
        if cls.builder_children is not None:
            for i in cls.builder_children:
                i.method_slots.append(method)
    register_method = classmethod(register_method)

    def build_methods(cls):
        """Create get/set methods for all slots."""
        if cls.primary != cls.slots[:len(cls.primary)]:
            cls.slots = cls.primary + cls.slots

        for attr in cls.slots:
            get = getattr(cls, attr.get_name_get(), None)
            set = getattr(cls, attr.get_name_set(), None)
            cls.register_attribute(attr, get=get, set=set, overwrite=True, register=False)

    build_methods = classmethod(build_methods)

# arch-tag: fa55df79-985c-4fab-90f8-d1fefd85fdbb
