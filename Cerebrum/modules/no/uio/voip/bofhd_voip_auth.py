#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2010 University of Oslo, Norway
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

"""This module implements the necessary authentication bits for voip bofhd
extension. 

A number of voip bofhd commands are restricted to certain users. This module
implements the necessary framework to support that.
"""



import cerebrum_path
import cereconf

from Cerebrum.Utils import Factory
from Cerebrum.modules.bofhd import auth
from Cerebrum.modules.bofhd.errors import PermissionDenied

from Cerebrum.modules.no.uio.voip.voipAddress import VoipAddress
from Cerebrum.modules.no.uio.voip.voipClient import VoipClient



class BofhdVoipAuth(auth.BofhdAuth):
    """Permissions checks for voip bofhd commands."""


    def __init__(self, database):
        super(BofhdVoipAuth, self).__init__(database)

        self.voip_sysadmins = cereconf.BOFHD_VOIP_ADMINS
    # end __init__


    def _is_voip_admin(self, account_id):
        return account_id in self._get_group_members(self.voip_sysadmins)
    # end _is_voip_admin


    ########################################################################
    # voip_address related permissions
    #
    def can_alter_number(self, account_id):
        """Whether account_id """
        if self.is_superuser(account_id):
            return True

        if self._is_voip_admin(account_id):
            return True

        raise PermissionDenied("Account id=%s cannot add/remove contact information."
                               % str(account_id))
    # end can_alter_number
        

    def can_alter_voip_address(self, account_id):
        """Whether account_id can change system information of a
        voip_address. 
        """

        if self.is_superuser(account_id):
            return True

        if self._is_voip_admin(account_id):
            return True

        raise PermissionDenied("Account id=%s cannot manipulate voip_addresses."
                               % str(account_id))
    # end can_alter_voip_address


    def can_alter_voip_address_pin(self, operator_id, address_owner_id):
        """Whether operator_id can change owner_id's address' pin code.

        A person can alter pin code of his/her own voip_address.

        A voip admin can alter anything.

        A superuser can alter anything.
        """

        if self.is_superuser(operator_id):
            return True

        if self._is_voip_admin(operator_id):
            return True

        #
        # Is operator_id one of address_owner_id's accounts?
        accs = Factory.get("Account")(self._db).list_accounts_by_owner_id(
            address_owner_id)
        accs = [x["account_id"] for x in accs]
        if operator_id in accs:
            return True

        raise PermissionDenied("Account id=%s cannot change pin of "
                               "person/voip_service id=%s" %
                               str(operator_id), str(address_owner_id))
    # end can_alter_voip_address_pin
    

    ########################################################################
    # voip_client related permissions
    #
    def can_create_voip_client(self, account_id):
        """Whether account_id is allowed to create/delete voip_clients."""

        if self.is_superuser(account_id):
            return True

        if self._is_voip_admin(account_id):
            return True
        
        raise PermissionDenied("Account id=%s cannot manipulate voip_clients." %
                               str(account_id))
    # end can_create_voip_client


    def can_view_voip_client(self, account_id):
        """Everybody can see information about voip_clients.

        FIXME: ORLY?
        """
        return True
    # end can_view_voip_client


    def can_alter_voip_client(self, account_id):
        """Whether account_id can change some info about a client."""

        if self.is_superuser(account_id):
            return True

        if self._is_voip_admin(account_id):
            return True

        raise PermissionDenied("Account id=%s cannot manipulate voip_clients")
    # end can_alter_voip_client


    def can_reset_client_secrets(self, account_id, client_id):
        """Whether account_id can reset sip*secrets.

        Resetting means deleting old ones and registering random news
        ones. This operation is meaningless for sip_client's owner.
        """
        
        if self.is_superuser(account_id):
            return True

        if self._is_voip_admin(account_id):
            return True

        raise PermissionDenied("Account id=%s cannot reset sip*Secret of "
                               "voip_client id=%s"  % (account_id, client_id))
    # end can_reset_client_secrets


    def can_set_new_secret(self, account_id, client_id):
        """Whether account_id can set a new sipSecret on client_id.
        """
        if self.is_superuser(account_id):
            return True

        if self._is_voip_admin(account_id):
            return True

        # We allow resetting a pin to the owner of client_id.
        # 
        # The test goes like this: find voip_address to which client_id is
        # bound. Compare it to account_id's owner_id. For non-personal
        # accounts this test is bound to fail.
        acc = Factory.get("Account")(self._db)
        acc.find(account_id)
        
        client = VoipClient(self._db)
        client.find(client_id)
        address = VoipAddress(self._db)
        address.find(client.voip_address_id)

        if address.owner_entity_id == acc.owner_entity_id:
            return True

        raise PermissionDenied("Account id=%s cannot change sipSecret of "
                               "voip_client id=%s" % (account_id, client_id))
    # end can_set_new_secret
    
    
    ########################################################################
    # voip_service related permissions
    #
    def can_create_voip_service(self, account_id):
        """Whether account_id is allowed to create/delete voip_services."""

        if self.is_superuser(account_id):
            return True

        if self._is_voip_admin(account_id):
            return True

        raise PermissionDenied("Account id=%s cannot manipulate voip-services." %
                               str(account_id))
    # end can_create_voip_service
   

    def can_view_voip_service(self, account_id):
        """Everybody can see information about voip_services."""
        return True
    # end can_view_voip_service
    

    def can_alter_voip_service(self, account_id):
        """Whether account_id is allowed to update info about voip_services."""

        if self.is_superuser(account_id):
            return True
        if self._is_voip_admin(account_id):
            return True

        raise PermissionDenied("Account id=%s cannot manipulate voip-services." %
                               str(account_id))
    # end can_alter_voip_service
# end BofhdVoipAuth


    