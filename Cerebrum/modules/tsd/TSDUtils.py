#!/user/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 University of Oslo, Norway
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
""" Utility functions for TSD.

This is where all utils functionality that is specific for TSD and is needed in
different places, but does not belong to a specific Entity class.

More TSD functionality should be put in here, i.e. some refactoring is needed
when the functionality needed by TSD has settled.

"""

from mx import DateTime

import cerebrum_path
import cereconf

from Cerebrum import Errors
from Cerebrum.modules.hostpolicy import PolicyComponent

def add_host_to_policy_component(db, dnsowner_id, policy_name):
    """ Helper method for giving a host a hostpolicy role.

    Note that this method does not fail if the given `policy_name` doesn't
    exist. Hostpolicies could disappear, or be renamed, which we would not want
    to break the system. Instead, unknown policies are simply not added, i.e.
    this method does nothing in such scenarios.

    :param Cerebrum.Database db:
        The Cerebrum database connector.

    :param int dnsowner_id:
        The `entity_id` of the host that should get the role.

    :param str policy_name:
        The name of the policy role or atom. If it does not exist, it will not
        be given to the host, but no exception will be raised.

    :rtype: bool
    :return:
        True if the policy was found and registered for the host. False if the
        policy weren't added, e.g. because the policy didn't exist.

    """
    pc = PolicyComponent.PolicyComponent(db)
    try:
        pc.find_by_name(policy_name)
    except Errors.NotFoundError:
        return False
    if not pc.search_hostpolicies(policy_id=pc.entity_id,
                                  dns_owner_id=dnsowner_id):
        pc.add_to_host(dnsowner_id)
    pc.write_db()
    return True