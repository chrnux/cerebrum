#!/usr/bin/env python
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

import os
import sys
import urllib
import socket

from omniORB import CORBA, importIDL, importIDLString
VERSION="0.2"


def fixOmniORB():
    """Workaround for bugs in omniorb

    Makes it possible to use obj1 == obj2 instead of having to do
    obj1._is_equivalent(obj2).
    Also makes it possible to use corba objects as keys in
    dictionaries etc.
    """
    import omniORB.CORBA
    import _omnipy
    def __eq__(self, other):
        if self is other:
            return True
        return _omnipy.isEquivalent(self, other)

    def __hash__(self):
        # sys.maxint is the maximum value returned by _hash
        return self._hash(sys.maxint)

    omniORB.CORBA.Object.__hash__ = __hash__
    omniORB.CORBA.Object.__eq__ = __eq__

def fixSpine():
    """Workaround for spine

    Enables automatic logout
    Provides versioning with login
    """
    import SpineIDL, SpineCore
    old_del = SpineIDL._objref_SpineSession.__del__
    def __del__(self):
        try:
            self.logout()
        except:
            pass
        return old_del(self)
    SpineIDL._objref_SpineSession.__del__ = __del__
    
    def login(self, username, password):
        host=socket.gethostbyaddr(socket.gethostname())[0]
        return self.login2(username, password, VERSION, host)
    SpineCore._objref_Spine.login = login


#FIXME: make optional?
fixOmniORB()

path = os.path.dirname(os.path.realpath(__file__))

class SpineClient:
    spine_core = os.path.join(path, 'SpineCore.idl')
    def __init__(self, ior_url=None,
                       use_ssl=None,
                       ca_file=None,
                       key_file=None,
                       ssl_password=None,
                       idl_path=None,
                       automatic=True,
                       config=None,
                       logger=None):
        if not os.path.exists(self.spine_core):
            raise IOError, '%s not found' % spine_core

        if config:
            # Use config-object for default values but allow override.
            ior_url = ior_url or config.get('SpineClient', 'url')
            idl_path = idl_path or config.get('SpineClient', 'idl_path')
            ca_file = ca_file or config.get('SpineClient', 'ca_file')
            key_file = key_file or config.get('SpineClient', 'key_file')
            ssl_password = ssl_password or config.get('SpineClient', 'key_password')
            if use_ssl is None:
                use_ssl = config.getboolean('SpineClient', 'use_ssl')
        
        if logger:    
            self.log= logger
        else:
            import logging
            self.log= logging.getLogger()

        if idl_path not in sys.path:
            # Directory must exist before it's appended to sys.path
            if not os.path.exists(idl_path):
                os.mkdir(idl_path)
            sys.path.append(idl_path)

        self.ior_url = ior_url
        self.use_ssl = use_ssl
        self.ssl_ca_file = ca_file
        self.ssl_key_file = key_file
        self.ssl_password = ssl_password
        self.idl_path = idl_path

        self.md5_file = os.path.join(self.idl_path, 'SpineIDL.md5')
        self.idl_file = os.path.join(self.idl_path, 'SpineIDL.idl')


        if not self.check_md5() and automatic:
            self.bootstrap()

        fixSpine()

    def init_ssl(self):
        try:
            from omniORB import sslTP
        except ImportError:
            self.log.error("Could not import omniORB.sslTP")
            sys.exit(1)
        sslTP.certificate_authority_file(self.ssl_ca_file)
        sslTP.key_file(self.ssl_key_file)
        sslTP.key_file_password(self.ssl_password)

        return CORBA.ORB_init(['-ORBendPoint', 'giop:ssl::'], CORBA.ORB_ID)

    def init(self):
        return CORBA.ORB_init()

    def connect(self):
        """Returns the server object.
        
        Method for connecting and fetch the Spine object.
        The method prefers SSL connections.
        """
        try:
            import SpineCore
        except ImportError:
            importIDL(self.spine_core)
            import SpineCore


        if self.use_ssl:
            orb = self.init_ssl()
        else:
            orb = self.init()

        self.log.debug("Using IOR %s",self.ior_url)
        ior = urllib.urlopen(self.ior_url).read()
        try:
            obj = orb.string_to_object(ior)
        except CORBA.BAD_PARAM, e:
            self.log.error("The ior file read from '%s' has invalid contents: %s",
                         self.ior_url, ior)
            sys.exit(1)

        spine = obj._narrow(SpineCore.Spine)
        if spine is None:
            raise Exception("Could not narrow the spine object")

        return spine

    def check_md5(self):
        try:
            spine = self.connect() 
            return spine.get_idl_md5() == open(self.md5_file).read()
        except IOError:
            return False

    def bootstrap(self):
        spine = self.connect()
        self.log.debug('- connected to: %s', spine)
        self.log.debug('- downloading source')
        source = spine.get_idl_commented()
        self.log.debug('- (%s bytes)', len(source))
        if not os.path.exists(self.idl_path):
            self.log.debug('- Making idl_path: %s', self.idl_path)
            os.makedirs(self.idl_path)
        fd = open(self.idl_file, 'w')
        fd.write(source)
        fd.close()
        self.log.debug('- Compiling to: %s', self.idl_path)
        
        retval= os.system('omniidl -bpython -C %s %s %s 2>%s' % (self.idl_path, self.spine_core, self.idl_file, os.devnull))
        if retval != 0:
            raise Exception, "omniidl command failed"
        
        import SpineIDL, SpineCore
        self.log.debug('- All done: %s %s', SpineIDL, SpineCore) 
        fd = open(self.md5_file, 'w')
        fd.write(spine.get_idl_md5())
        fd.close()

class Search:
    def __init__(self, tr):
        self.tr = tr
        self.searches = {}

    def __getattr__(self, name):
        def wrapped(alias, **args):
            s = getattr(self.tr, 'get_%s_searcher' % name)()
            self.searches[s] = alias
            for key, value in args.items():
                getattr(s, 'set_%s' % key)(value)
            return s

        return wrapped

    def dump(self, searcher):
        names = [self.searches[i] for i in searcher.get_search_objects()]
        for structs in zip(*[i.dump() for i in searcher.get_dumpers()]):
            yield dict(zip(names, structs))

# arch-tag: 2f4948da-4732-11da-8c59-869c4ebe94a5
