

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
import Communication

import omniORB
spine_core = os.path.join(os.path.dirname(__file__), "SpineCore.idl")
omniORB.importIDL(spine_core)

import SpineCore
import SpineCore__POA

import Session
import SessionHandler

from Cerebrum.spine.Account import get_account_by_name
from Cerebrum.spine.SpineLib import Database

from Cerebrum.Utils import Factory
logger = Factory.get_logger()

# The major version number of the Spine server
SPINE_MAJOR_VERSION = 0

# The minor version of the Spine server
SPINE_MINOR_VERSION = 1

class SpineImpl(SpineCore__POA.Spine):
    """Implementation of the Spine interface.
    
    Implements the methods in the Spine interface.
    These are provided to remote clients. This is the first object
    returned to the client, after they have connected.
    """

    def __init__(self):
        self.sessions = {}

    def get_idl(self):
        return Session.idl_source

    def get_idl_md5(self):
        return Session.idl_source_md5

    def get_idl_commented(self):
        return Session.idl_source_commented

    def get_version(self):
        return SpineCore.Version(SPINE_MAJOR_VERSION, SPINE_MINOR_VERSION)
        
    def login2(self, username, password, version, host):
        """Return the user-spesific session.
        
        If the username and password is correct and the user is not
        quarantined, we return the session-object, else we raise the
        exception 'LoginError'.
        """
        # We will always throw the same exception in here. This is important!
        exception = SpineCore.Spine.LoginError('Wrong username or password')
        # Check username
        for char in ['*','?']:
            if char in username or char in password:
                raise exception

        sessiondb = Database.SpineDatabase(type="session")
        try:
            account = get_account_by_name(sessiondb, username)
        except:
            logger.exception("Login failed for %s" % username)
            sessiondb.close()
            raise exception

        # Check password
        if not account.authenticate(password):
            sessiondb.close()
            raise exception

        # Check quarantines
        if account.is_quarantined():
            sessiondb.close()
            raise exception

        session = Session.SessionImpl(account, sessiondb, username, version, host)
        
        session_handler = SessionHandler.get_handler()
        csession = session_handler.add(session)
        
        return csession


# arch-tag: 6c78d470-4b73-491a-a448-c54cc8650148
