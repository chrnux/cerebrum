#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Copyright 2011 University of Oslo, Norway
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

# $Id$
""" 
The Constants defined for the HostPolicy module, depending on the DNS module.
"""

from Cerebrum import Constants
from Cerebrum.modules.CLConstants import _ChangeTypeCode

__version__ = "$Revision$"
# $URL$
# $Source$

class _PolicyRelationshipCode(Constants._CerebrumCode):
    "Mappings stored in the hostpolicy_relationship_code table"
    _lookup_table = '[:table schema=cerebrum name=hostpolicy_relationship_code]'

class Constants(Constants.Constants):
    entity_hostpolicy_atom = Constants._EntityTypeCode(
        'hostpolicy_atom',
        'hostpolicy_atom - see table "cerebrum.hostpolicy_component" and friends.')
    entity_hostpolicy_role = Constants._EntityTypeCode(
        'hostpolicy_role',
        'hostpolicy_role - see table "cerebrum.hostpolicy_component" and friends.')


    hostpolicy_component_namespace = Constants._ValueDomainCode('hostpol_comp_ns',
                                                                'Domain for hostpolicy-components')


    hostpolicy_mutually_exclusive = _PolicyRelationshipCode(
        "hostpol_mutex", "Source policy and target policy are mutually exclusive")
    hostpolicy_contains = _PolicyRelationshipCode(
        "hostpol_contains", "Source policy contains target policy")

    # ChangeLog constants
    hostpolicy_atom_create = _ChangeTypeCode(
        'hostpolicy', 'atom_create', 'create atom %(subject)s')
    hostpolicy_atom_mod = _ChangeTypeCode(
        'hostpolicy', 'atom_mod', 'modify atom %(subject)s')
    hostpolicy_atom_delete = _ChangeTypeCode(
        'hostpolicy', 'atom_delete', 'delete atom %(subject)s')
    hostpolicy_role_create = _ChangeTypeCode(
        'hostpolicy', 'role_create', 'create role %(subject)s')
    hostpolicy_role_mod = _ChangeTypeCode(
        'hostpolicy', 'role_mod', 'modify role %(subject)s')
    hostpolicy_role_delete = _ChangeTypeCode(
        'hostpolicy', 'role_delete', 'delete role %(subject)s')

    hostpolicy_relationship_add = _ChangeTypeCode(
        'hostpolicy', 'relationship_add', 'add relationship %(subject)s -> %(dest)s')
        # TODO: type is not given here
    hostpolicy_relationship_remove = _ChangeTypeCode(
        'hostpolicy', 'relationship_remove', 'remove relationship %(subject)s -> %(dest)s')
        # TODO: type is not given here

    hostpolicy_policy_add = _ChangeTypeCode(
        'hostpolicy', 'policy_add', 'add policy %(dest)s to host %(subject)s')
    hostpolicy_policy_remove = _ChangeTypeCode(
        'hostpolicy', 'policy_remove', 'remove policy %(dest)s from host %(subject)s')



PolicyRelationshipCode = _PolicyRelationshipCode
