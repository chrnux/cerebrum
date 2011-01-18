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

"""This module implements voip_client functionality for voip.

Each client in voip is an entity capable of being called to/from (such as an
ip-phone device, or a softphone or indeed something completely
different). This module implements an API managing client-related data.

The connection chain between all voip entities looks something like this:

   VoipClient ---[belongs to]---+
                                |
              +-----------------+
              |        
              +--> VoipAddress ---[owned by]---> Person or VoipService

Each voip address in Cerebrum is represented by an entry in voip_address
table, and a number of rows in related tables. This module implements an
interface to these tables, so that voip_address (and associated data) can be
accessed from Python.
"""

import random
import string

import cerebrum_path
import cereconf

from Cerebrum.Utils import argument_to_sql
from Cerebrum.Utils import Factory
from Cerebrum.modules.no.uio.voip.EntityAuthentication import EntityAuthentication
from Cerebrum.modules.EntityTrait import EntityTrait
from Cerebrum.modules.bofhd.errors import CerebrumError





class VoipClient(EntityAuthentication, EntityTrait):
    """voip_client interface.

    This class implements an interface to the voip_client table.
    """

    __read_attr__ = ("__in_db",)
    __write_attr__ = ("voip_address_id", # corresponding VoipAddress
                      "client_type",     # soft/hardphone
                      "sip_enabled",     # emergency(?) flag (T/F)
                      "mac_address",     # syntax -- aa:bb:cc:dd:ee:ff 
                      "client_info",     # specific model code
                      )

    def __init__(self, *rest, **kw):
        super(VoipClient, self).__init__(*rest, **kw)

        self.valid_auth_methods = (self.const.voip_auth_sip_secret,
                                   self.const.voip_auth_sip_old_secret,)
        self.sip_secret_alphabet = (string.letters + string.digits +
                                    ",.;:-_/!#{}[]+?")
        self.sip_secret_length = 15
    # end __init__



    def clear(self):
        self.__super.clear()
        self.clear_class(VoipClient)
        self.__updated = list()
    # end clear



    def _normalize_mac_address(self, mac_address):
        """Force mac address to a specific format.

        We store mac as aa:bb:cc:dd:ee:ff, although we accept several formats:

          - aabbccddeeff
          - aa bb cc dd ee ff
          - aa:bb:cc:dd:ee:ff
        """

        if not mac_address:
            return None

        addr = mac_address.translate(string.maketrans("", ""), " :")
        addr = addr.lower()
        assert all(x in "0123456789abcdef" for x in addr), "Wrong mac character"
        assert len(addr) == 12, "Wrong mac length"
        return ":".join(addr[i:i+2]
                        for i in range(0, 12, 2))
    # end _normalize_mac_address



    def _assert_mac_rules(self):
        """Check that self's mac_address is in sync with the business
        rules."""

        if self.client_type == self.const.voip_client_type_softphone:
            assert self._normalize_mac_address(self.mac_address) is None
            return

        if self.client_type == self.const.voip_client_type_hardphone:
            assert self._normalize_mac_address(self.mac_address)
            return
    # end _assert_mac_rules
    


    def populate(self, voip_address_id, client_type, sip_enabled,
                 mac_address, client_info):
        """Create a new VoipClient in memory."""

        assert sip_enabled in (True, False)
        mac_address = self._normalize_mac_address(mac_address)
        EntityTrait.populate(self, self.const.entity_voip_client)

        try:
            if not self.__in_db:
                raise RuntimeError("populate() called multiple times.")
        except AttributeError:
            self.__in_db = False

        self.voip_address_id = int(voip_address_id)
        self.client_type = int(self.const.VoipClientTypeCode(client_type))
        self.sip_enabled = bool(sip_enabled)
        self.mac_address = mac_address
        self.client_info = int(self.const.VoipClientInfoCode(client_info))
        self._assert_mac_rules()
    # end populate



    def write_db(self):
        """Synchronise the object in memory with the database.
        """

        self._assert_mac_rules()

        self.__super.write_db()
        if not self.__updated:
            return

        is_new = not self.__in_db
        binds = {"entity_type": self.const.entity_voip_client,
                 "entity_id": self.entity_id,
                 "voip_address_id": int(self.voip_address_id),
                 "client_type": int(self.client_type),
                 "sip_enabled": bool(self.sip_enabled) and 'T' or 'F',
                 "mac_address": self._normalize_mac_address(self.mac_address),
                 "client_info": int(self.client_info),}
        if is_new:
            self.execute("""
            INSERT INTO [:table schema=cerebrum name=voip_client]
            VALUES (:entity_type, :entity_id, :voip_address_id,
                    :client_type, :sip_enabled, :mac_address,
                    :client_info)
            """, binds)
        else:
            self.execute("""
            UPDATE [:table schema=cerebrum name=voip_client]
            SET %s
            WHERE entity_id = :entity_id              
            """ % ", ".join("%s=:%s" % (t, t) for t in binds),
                         binds)

        # Reset the cerebrum auto_updater magic
        del self.__in_db
        self.__in_db = True
        self.__updated = list()
        return is_new
    # end write_db



    def delete(self):
        """Remove a specified entry from the voip_client table.
        """

        if self.__in_db:
            self.execute("""
            DELETE FROM [:table schema=cerebrum name=voip_client]
            WHERE entity_id = :entity_id
            """, {"entity_id": self.entity_id})

        self.__super.delete()
    # end delete



    def find(self, entity_id):
        """Locate VoipClient by its entity_id."""

        self.__super.find(entity_id)

        (self.voip_address_id,
         self.client_type,
         sip_enabled,
         self.mac_address,
         self.client_info) = self.query_1("""
         SELECT voip_address_id, client_type, sip_enabled,
                mac_address, client_info
         FROM [:table schema=cerebrum name=voip_client]
         WHERE entity_id = :entity_id
         """, {"entity_id": self.entity_id})

        # FIXMe: Do we really want the API to fail here?
        assert sip_enabled in ('T', 'F')
        self.sip_enabled = sip_enabled == 'T'
        self.__in_db = True
    # end find



    def find_by_mac_address(self, mac_address):
        mac_address = self._normalize_mac_address(mac_address)

        entity_id = self.query_1("""
        SELECT entity_id
        FROM [:table schema=cerebrum name=voip_client]
        WHERE mac_address = :mac_address
        """, {"mac_address": mac_address})

        self.find(entity_id)
    # end find_by_mac_address



    def get_auth_data(self, auth_method):
        """Retrieve the corresponding sip secret.

        Only two secret types are allowed: sip_secret and sip_old_secret.
        """

        assert auth_method in self.valid_auth_methods
        return self.__super.get_auth_data(auth_method)
    # end get_auth_data



    def set_auth_data(self, auth_method, auth_data):
        """Register a new sip secret.
        """

        assert auth_method in self.valid_auth_methods
        return self.__super.set_auth_data(auth_method, auth_data)
    # end set_auth_data

    

    def validate_auth_data(self, auth_method, auth_data):
        """Check that sip secrets match our rules.
        """

        if not isinstance(auth_data, (str, unicode)):
            raise CerebrumError("Invalid type of auth data: %s "
                                "(expected str)" % (type(auth_data)))

        if auth_method not in self.valid_auth_methods:
            return self.__super.validate_auth_data(auth_method, auth_data)

        # Sip secrets have to follow a few rules.
        # all chars are from a preset alphabet
        if not all(x in self.sip_secret_alphabet
                   for x in auth_data):
            raise CerebrumError("Invalid chars in auth_data %s" %
                                str(auth_data))

        # secret is at least 15 characters in length
        if len(auth_data) < self.sip_secret_length:
            raise CerebrumError("auth data %s too short: "
                                "seen %d chars, required %d" %
                                (auth_data, len(auth_data),
                                 self.sip_secret_length))

        return True
    # end validate_auth_data



    def generate_sip_secret(self):
        """Return a freshly generated sip secret.
        """

        alphabet = self.sip_secret_alphabet
        pwd = list()
        while len(pwd) < self.sip_secret_length:
            pwd.append(alphabet[random.randint(0, len(alphabet)-1)])

        # FIXME: call a validate_auth_data here?
        return "".join(pwd)
    # end generate_sip_secret



    def get_voip_attributes(self):
        """Return a dict with all LDAP attributes available for voipAddress.

        The calculation is a bit involved, since we need a lot of crap.
        """

        result = dict()
        for required_key in ("uid", "sipEnabled",
                             "sipMacAddress", "sipSecret", "sipOldSecret",
                             "sipClientInfo", "sipClientType",
                             "voip_address_id",):
            result[required_key] = None

        result["sipClientType"] = str(self.const.VoipClientTypeCode(self.client_type))
        result["sipClientInfo"] = str(self.const.VoipClientInfoCode(self.client_info))
        result["sipOldSecret"] = self.get_auth_data(self.const.voip_auth_sip_old_secret)
        result["sipSecret"] = self.get_auth_data(self.const.voip_auth_sip_secret)
        if self.mac_address:
            result["sipMacAddress"] = self.mac_address.replace(":", "")
        result["sipEnabled"] = bool(self.sip_enabled)
        result["uid"] = str(self.entity_id)
        result["voip_address_id"] = self.voip_address_id
        return result
    # end get_voip_attributes



    def list_voip_attributes(self):
        """Fast version of search() + get_voip_attributes().

        Simply put, with tens of thousands of objects, find() +
        get_voip_attributes() is unfeasible. This method has similar semantics,
        to the combination above, except it returns a generated yielding
        successful dicts, once for each voipClient. Each dict is similar to the
        one returned by get_voip_attributes.
        """

        # So, a few things we need to cache
        const2str = dict()
        for cnst in self.const.fetch_constants(self.const.VoipClientTypeCode):
            assert int(cnst) not in const2str
            const2str[int(cnst)] = str(cnst)
        for cnst in self.const.fetch_constants(self.const.VoipClientInfoCode):
            assert int(cnst) not in const2str
            const2str[int(cnst)] = str(cnst)

        # entity_id -> {<auth type>: <auth_data>}
        client2auth = dict()
        for row in self.list_auth_data((self.const.voip_auth_sip_secret,
                                        self.const.voip_auth_sip_old_secret)):
            client2auth.setdefault(row['entity_id'],
                                   {})[row['auth_method']] = row['auth_data']

        # person_id -> primary_uname
        account = Factory.get("Account")(self._db)
        primary_accounts = set(r["account_id"] for r in
                               account.list_accounts_by_type(primary_only=True))
        pid2uname = dict((r["owner_id"], r["name"])
                         for r in account.search(
                             owner_type=self.const.entity_person)
                         if r["account_id"] in primary_accounts)

        for row in self.search():
            mac = row["mac_address"]
            mac = mac.replace(":", "") if mac else None
            entry = {"sipClientType": const2str[row["client_type"]],
                     "sipClientInfo": const2str[row["client_info"]],
                     "sipOldSecret":
                       client2auth.get(row["entity_id"],
                         {}).get(self.const.voip_auth_sip_old_secret),
                     "sipSecret": 
                       client2auth.get(row["entity_id"],
                         {}).get(self.const.voip_auth_sip_secret),
                     "sipMacAddress": mac,
                     "sipEnabled": bool(row["sip_enabled"] == 'T'),
                     "voip_address_id": row["voip_address_id"],}

            if row["client_type"] == self.const.voip_client_type_softphone:
                owner_id = row["owner_entity_id"]
                entry["uid"] = pid2uname.get(owner_id,
                                             str(row["voip_address_id"]))

            yield entry
    # end list_voip_attributes
    


    def search(self, entity_id=None, voip_address_id=None, voip_owner_id=None,
               client_type=None, mac_address=None, client_info=None):
        """Search for voip_clients subject to certain filter rules.

        All filters are None, scalars, or sequences thereof. None means that
        the filter is not applied. Scalar means we are looking for the exact
        value. Sequence (list, tuple, set) of scalars means that we are
        looking for voip_clients matching ANY one of the specified scalars in
        the filter.

        The filters are self-explanatory.

        @param voip_owner_id:
          This one is a bit special: we are looking for voip_clients where the
          associated voip_address rows are owned by the specified
          voip_owner_id. This is useful to answer queries like 'Locate all
          voip_clients belonging to person Foo'.

        @return:
          An iterable over db_rows with query result.
        """

        binds = dict()
        where = list()
        for name in ("entity_id", "voip_address_id", "client_type",
                     "client_info"):
            if locals()[name] is not None:
                where.append(argument_to_sql(locals()[name],
                                             "vc." + name,
                                             binds, int))

        if mac_address is not None:
            where.append(argument_to_sql(mac_address,
                                         "vc.mac_address",
                                         binds, str))

        if voip_owner_id is not None:
            where.append(argument_to_sql(voip_owner_id,
                                         "va.owner_entity_id",
                                         binds, int))
        if where:
            where = " AND " + " AND ".join(where)
        else:
            where = ""

        return self.query("""
        SELECT vc.entity_type, vc.entity_id, vc.voip_address_id, vc.client_type,
               vc.sip_enabled, vc.mac_address, vc.client_info, va.owner_entity_id,
               ei.entity_type as owner_entity_type
        FROM [:table schema=cerebrum name=voip_client] vc,
             [:table schema=cerebrum name=voip_address] va,
             [:table schema=cerebrum name=entity_info] ei
        WHERE vc.voip_address_id = va.entity_id AND
              va.owner_entity_id = ei.entity_id 
              %s""" % where, binds)
    # end search
# end VoipClient