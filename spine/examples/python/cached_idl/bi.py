#!/usr/bin/python -i
# -*- encoding: iso-8859-1 -*-

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

"""
This is an example client that uses python interactive mode to work against
spine.  It adds some shortcuts to often used functionality, but is basically
just a convenient way to connect to Spine and test out things from the 
command line.

For command line completion and such, add the following three lines to your
~/.pythonrc.py:
import rlcompleter
import readline
readline.parse_and_bind("tab: complete")

Make sure PYTHONPATH contains the path to SpineClient.py and that SpineCore.idl
is in the same directory as SpineClient.py.
"""


import user
import sys, os
import ConfigParser
conf = ConfigParser.ConfigParser()
conf.read(('client.conf.template', 'client.conf'))

try:
    import SpineClient
    from TestObjects import *
except:
    print >> sys.stderr, "\n".join(
       ("Importing SpineClient or TestObjects failed.",
        "Please make sure cerebrum/spine/test and",
        "cerebrum/spine/client is in your PYTHONPATH",
        "environment variable."))
    sys.exit(1)
        
class Session(object):
    def __init__(self, ior_file=None, username=None, password=None):
        print "Loggin in..."
        self.username = username or conf.get('login', 'username')
        self.password = password or conf.get('login', 'password')
        ior_file = ior_file or conf.get('corba', 'url')
        cache_dir = conf.get('cache', 'cache_dir')
        self.spine = SpineClient.SpineClient(ior_file, idl_path=cache_dir).connect()
        self.session = self.spine.login(self.username, self.password)
        self.tr = self.session.new_transaction()
        self.cmds = self.tr.get_commands()
    
    def __del__(self):
        print "Logging out..."
        self.tr.rollback()
        self.session.logout()

    def pga(self):
        p = DummyPerson(self.session)
        a = DummyAccount(self.session, p)
        g = DummyGroup(self.session)
        g.add_member(a.get_id())
        return p,g,a
s = Session()
