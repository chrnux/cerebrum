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
#

import os, sys, traceback, unittest
from test import test_support
try:
    import SpineClient
except ImportError:
    print >> sys.stderr, \
    "Fatal error in TestBase.py: \n\t\
            Couldn't import SpineClient.  Make sure PYTHONPATH is correct."
    sys.exit(1)
import ConfigParser

conf = ConfigParser.ConfigParser()
conf.read(('../client.conf.template', '../client.conf', 'client.conf'))

username  = conf.get('login', 'username')
password  = conf.get('login', 'password')

spine = SpineClient.SpineClient(config=conf).connect()

class SpineObjectTest(unittest.TestCase):
    """
    Super class for all tests that involve a single object.

    To use the test class, you must overload the createObject and deleteObject
    methods, which will be called before and after each test, respectively.
    """

    def setUp(self):
        self.open = False
        self.session = spine.login(username, password)
        self.createObject()

    def tearDown(self):
        self.deleteObject()
        self.session.logout()

    def createObject(self):
        raise RuntimeError('Subclass does not implement the createObject method.')

    def deleteObject(self):
        raise RuntimeError('Subclass does not implement the deleteObject method.')


    def get_tr(self):
        if not self.open:
            self.tr = self.session.new_transaction()
            self.open = True
        return self.tr

    def commit(self):
        if self.open:
            self.tr.commit()
            self.open = False

    def rollback(self):
        if self.open:
            self.tr.rollback()
            self.open = False

def create_name(obj):
    n = str(id(obj))
    return 'tn%s' % n[3:8]
