#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 University of Oslo, Norway
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
"""Webservice functionality for Resource management in the TSD project.

Resources are registered in Cerebrum, but they are administered by other
systems. For those systems to be able to retrieve the information, we are giving
it through a SOAP webservice.

"""

# TODO: check if something could be removed from here:
import random, hashlib
import string, pickle
from mx.DateTime import RelativeDateTime, now
import twisted.python.log

import cereconf
import cerebrum_path
from Cerebrum import Errors
from Cerebrum.Utils import Factory
from Cerebrum.modules.dns import IPv6Number

from Cerebrum.modules.cis import Utils
log = Utils.SimpleLogger()

class ResourceService(object):
    """The functionality for the Resource service.

    Note that this main class should be independent of what server we use. It is
    important that each thread gets its own instance of this class, to avoid
    race conditions.

    Another thing to remember is that database connections should be closed.
    This is to avoid having old and idle database connections, as the garbage
    collector can't destroy the instances, due to twisted's reuse of threads.

    """
    def __init__(self, operator_id):
        """Constructor. Since we are using access control, we need the
        authenticated entity's ID as a parameter.

        """
        self.db = Factory.get('Database')()
        self.db.cl_init(change_program='resource_service')
        self.co = Factory.get('Constants')(self.db)
        #self.grp = Factory.get("Group")(self.db)
        self.ipv6 = IPv6Number(self.db)
        # TODO: could we save work by only using a single, shared object of
        # the auth class? It is supposed to be thread safe.
        #self.ba = BofhdAuth(self.db)
        self.operator_id = operator_id

    def close(self):
        """Explicitly close this instance, as python's garbage collector can't
        close the database connections when Twisted is reusing the threads.

        """
        if hasattr(self, 'db'):
            try:
                self.db.close()
            except Exception, e:
                log.warning("Problems with db.close: %s" % e)
        else:
            # TODO: this could be removed later, when it is considered stable
            log.warning("db doesn't exist")

    def search_mac_addresses(self, hostname, mac_address):
        """Search for hostnames and their MAC addresses."""
        # TODO
        return ()

    def register_mac_address(self, hostname, mac_address):
        """Register a MAC address for a given host."""
        by_mac = None
        if mac_address:
            by_mac = self.ipv6.find_by_mac(mac_address)

        # TODO
        return False
        # find the host by its hostname
        # register the address
        # host.write_db()
        # db.commit()
        return True

    def get_vlan_info(self, hostname):
        """Get the VLAN info about a given host."""
        # TODO
        return ()

