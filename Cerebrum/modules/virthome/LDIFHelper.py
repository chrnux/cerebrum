#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright 2007 University of Oslo, Norway
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
""" LDIFHelper contains an object that select users+groups for export, and
generate structured data for LDIFutils """

import cerebrum_path
import cereconf

from Cerebrum.Utils import Factory
from Cerebrum.modules.LDIFutils import ldapconf

def object2utf8(obj):
    """ Force all string-like values in obj to be utf-8 encoded. """
    if isinstance(obj, str):
        return unicode(obj, "latin-1").encode("utf-8")
    if isinstance(obj, unicode):
        return obj.encode("utf-8")
    if isinstance(obj, (tuple, list, set)):
        return type(obj)(object2utf8(x) for x in obj)
    if isinstance(obj, dict):
        return dict((object2utf8(key), object2utf8(obj[key]))
                    for key in obj)
    return obj
# end object2utf8

class LDIFHelper(object):
    """ Utility class for common functionality in LDIF exports. """

    def __init__(self, logger):
        """ Fetches all users and groups with the required spreads to qualify
        for LDAP export 
        
        @type logger: Cerebrum.Logger
        """

        self.db = Factory.get("Database")()
        self.const = Factory.get("Constants")(self.db)
        self.logger = logger

        # groups must be populated before users, since the latter relies on the
        # former due to data precaching.
        self.groups = self._load_groups()
        self.users = self._load_users()
    # end __init__


    def _uname2dn(self, uname):
        return ",".join(("uid=" + uname, ldapconf("USER", "dn")))
    # end _uname2dn


    def _gname2dn(self, gname):
        return ",".join(("cn=" + gname, ldapconf("GROUP", "dn")))
    # _gname2dn


    def _load_groups(self):
        """Cache a dict with group_id -> group_name for all LDAP-exportable
        groups. 

        See L{_load_users} for a related method.

        @rtype: dict (int -> dict-like object)
        @return:
          A dict mapping group_id to group info for all groups with
          LDAP-exportable spreads. The latter is controlled by
          cereconf.LDAP_GROUP.
        """

        group = Factory.get("Group")(self.db)
        spreads = tuple(self.const.human2constant(x)
                        for x in ldapconf("GROUP", "spreads", ()))
        self.logger.debug("Collecting groups for LDAP export. "
                     "Spreads: %s", ", ".join(str(x) for x in spreads))
        return dict((x["group_id"], x)
                    for x in group.search(spread=spreads))
    # end _load_groups
    

    def _load_users(self):
        """Cache enough user information for the export to progress."""


        account = Factory.get("Account")(self.db)
        spreads = tuple(self.const.human2constant(x)
                        for x in ldapconf("USER", "spreads", ()))
        self.logger.debug("Collecting users for LDAP export. "
                     "Spreads: %s", ", ".join(str(x) for x in spreads))
        users = dict()
        account = Factory.get("Account")(self.db)
        for spread in spreads:
            for row in account.search(spread=spread):
                users[row["account_id"]] = {"uname": row["name"],
                                            "np_type": row["np_type"],}

        users = self._get_contact_info(users)
        users = self._get_password_info(users)
        users = self._get_membership_info(users)
        return users
    # end _load_users


    def _get_contact_info(self, users):
        """Update users with name and e-mail data."""

        account = Factory.get("Account")(self.db)
        contact2tag = {self.const.virthome_contact_email: "mail",
                       self.const.human_first_name: "givenName",
                       self.const.human_last_name: "sn",}
                
        self.logger.debug("Collecting email/name info for LDAP export")
        for eci in account.list_contact_info(
                       source_system=self.const.system_virthome,
                       contact_type=tuple(contact2tag)):
            account_id = eci["entity_id"]
            if account_id not in users:
                continue

            contact_type = int(eci["contact_type"])
            contact_value = eci["contact_value"]
            tag = contact2tag[contact_type]
            users[account_id][tag] = contact_value

        self.logger.debug("Calculating cn and adjusting VA names")
        suffix = " (unverified)"
        for account_id in users:
            vals = users[account_id]
            first = vals.get("givenName") or ""
            last = vals.get("sn") or ""
            if not first and not last:
                full = vals["uname"]
            else:
                full = " ".join((first, last))

            if vals["np_type"] == self.const.virtaccount_type:
                first = first + suffix
                last = last + suffix
                full = full + suffix

            vals["givenName"] = first
            vals["sn"] = last
            vals["cn"] = full
            
        return users
    # end _get_contact_info


    def _get_password_info(self, users):
        """Collect md5 hashes for VA-s."""

        self.logger.debug("Collecting password information")
        account = Factory.get("Account")(self.db)
        for row in account.list_account_authentication(
                              auth_type=self.const.auth_type_md5_crypt):
            account_id = row["account_id"]
            if account_id not in users:
                continue

            if users[account_id]["np_type"] != self.const.virtaccount_type:
                continue
            
            users[account_id]["userPassword"] = ("{crypt}" + row["auth_data"],)
        return users
    # end _get_password_info


    def _get_membership_info(self, users):
        """Collect group memberships information."""
        
        group = Factory.get("Group")(self.db)
        self.logger.debug("Collecting user membership information")

        # crap. this is going to be VERY expensive...
        for row in group.search_members(member_type=self.const.entity_account):
            group_id = row["group_id"]
            if group_id not in self.groups:
                continue

            account_id = row["member_id"]
            if account_id not in users:
                continue

            gname = self._gname2dn(self.groups[group_id]["name"])
            users[account_id].setdefault("uioMemberOf", list()).append(gname)
        return users
    # end _get_membership_info


    def yield_groups(self):
        """Generate group dicts with all LDAP-relevant information.
        """

        group = Factory.get("Group")(self.db)
        for group_id in self.groups:
            gi = self.groups[group_id]
            group_name = gi["name"]
            entry = {"dn": (self._gname2dn(group_name),),
                     "cn": (group_name,),
                     "objectClass": ldapconf("GROUP", "objectClass"),
                     "description": (gi["description"],),}
            entry.update(self._get_member_info(group_id, group))
            if not entry.get("member"):
                continue

            entry = object2utf8(entry)
            yield entry
    # end _extend_group_information


    def _get_member_info(self, group_id, group):
        """ Retrieve all members of a group.
        We need to respect LDAP-spreads for users and groups alike.

        @rtype: dict (str -> sequence of DNs)
        @return:
          A dict with one entry, 'member' -> sequence of members in the
          respective group.
        """

        # TBD: Maybe this ought to be cached? 
        members = tuple(self._uname2dn(self.users[x["member_id"]]["uname"])
                                for x in group.search_members(group_id=group_id)
                                if x["member_id"] in self.users)
        if members:
            return {"member": members}
        return {}
    # end _get_member_info


    def yield_users(self):
        """ Yield all users qualified for export to LDAP. """

        def _mangle(attrs):
            if not isinstance(attrs, (list, set, tuple)):
                return (attrs,)
            return attrs
        
        for user_id in self.users:
            attrs = self.users[user_id]
            tmp = {"dn": (self._uname2dn(attrs["uname"]),),
                   "uid": (attrs["uname"],),
                   "eduPersonPrincipalName": (attrs["uname"],),
                   "mail": (attrs["mail"],),
                   "objectClass": ldapconf("USER", "objectClass"),}

            for key in ("cn", "sn", "givenName", "userPassword", "uioMemberOf",):
                if key in attrs:
                    tmp[key] = _mangle(attrs[key])

            tmp = object2utf8(tmp)
            yield tmp
    # end generate_users
# end UserLDIF
