#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Copyright 2009 University of Oslo, Norway
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

# $Id: Subnet.py 14318 2011-05-31 12:37:00Z matmeis $

import math

import cereconf
from Cerebrum.Errors import NotFoundError
from Cerebrum.modules.dns.Errors import SubnetError
from Cerebrum.Entity import Entity

from Cerebrum.modules.dns import IPv6Number
from Cerebrum.modules.dns.IPv6Utils import IPv6Calc, IPv6Utils


__doc__ = """
This module contains all functionality relating to information about
IPv6 subnets in Cerebrum.

"""

__version__ = "$Revision: 14318 $"
# $URL: https://cerebrum.svn.sourceforge.net/svnroot/cerebrum/branches/js_uio_dns/Cerebrum/modules/dns/Subnet.py $

class IPv6Subnet(Entity):
    """Represents subnet-entities."""

    __read_attr__ = ('__in_db',)
    __write_attr__ = ('subnet_ip', 'description', 'name_prefix',
                      'vlan_number', 'no_of_reserved_adr', 'dns_delegated')

    def __init__(self, db):
        super(IPv6Subnet, self).__init__(db)
        # The mask of this subnet; calculated from min and max ip's on subnet
        self.subnet_mask = None
        # Set of reserved adresses, represented as longs (i.e. not x.x.x.x)
        self.reserved_adr = set()
        

    def is_valid_subnet(subnet):
        """Validates that a subnet specification is correctly
        formatted and with legal values.

        Raises SubnetError if invalid.

        """
        try:
            ip, mask = subnet.split('/')
        except ValueError:
            raise SubnetError("Not a valid subnet '%s'" % subnet)
        
        if not IPv6Calc.verify(ip):
            raise SubnetError('Invalid adress: %s' % ip)
        
        mask = int(mask)
        if mask < 0 or mask > 128:
            raise SubnetError("Invalid subnet mask '%s'; outside range 0-128" %
                                mask)
        
        return True
    is_valid_subnet = staticmethod(is_valid_subnet)


    def calculate_subnet_mask(ip_min, ip_max):
        """Calculates the subnetmask of a subnet based on the highest
        and lowest IP available to on that subnet.

        ip_min & ip_max are the IP's as integers, returns the
        subnetmask as an integer from 0 to 32 (inclusive).

        """
        net_size = ip_max - ip_min + 1
        return int(128 - math.log(net_size, 2))
    calculate_subnet_mask = staticmethod(calculate_subnet_mask)
    

    def clear(self):
        """Clear all data residing in this Subnet-instance."""
        super(IPv6Subnet, self).clear()
        self.clear_class(IPv6Subnet)
        self.__updated = []


    def populate(self, subnet, description, vlan=None):
        """Populate subnet instance's attributes."""
        Entity.populate(self, self.const.entity_dns_ipv6_subnet)
        # If __in_db is present, it must be True; calling populate on
        # an object where __in_db is present and False is very likely
        # a programming error.
        #
        # If __in_db in not present, we'll set it to False.
        try:
            if not self.__in_db:
                raise RuntimeError, "populate() called multiple times."
        except AttributeError:
            self.__in_db = False
            
        self.subnet_ip, subnet_mask = subnet.split('/')
        self.subnet_mask = int(subnet_mask)
        self.subnet_ip = IPv6Utils.explode(self.subnet_ip)
            
        self.ip_min, self.ip_max = IPv6Calc.ip_range_by_netmask(
                                        self.subnet_ip,
                                        self.subnet_mask)
        self.description = description
        self.vlan = vlan

        # TODO: Fix this
        max_res = max(cereconf.DEFAULT_RESERVED_BY_IPv6_NET_SIZE.values()) 
        self.no_of_reserved_adr = cereconf.DEFAULT_RESERVED_BY_IPv6_NET_SIZE.get(self.subnet_mask, max_res)
        self.calculate_reserved_addresses()


    def check_for_overlaps(self):
        """Checks if there already are subnets in the database that
        overlap with this subnet.

        Overlap is defined as having an ip_min-ip_max range that
        overlaps with an existing (= in DB) subnet's ip_min-ip_max
        range.

        Raises SubnetError if there are overlaps.

        """
        binds = {"min": self.ip_min,
                 "max": self.ip_max}

        overlap_entries = self.query(
            """SELECT subnet_ip, ip_min, ip_max
               FROM [:table schema=cerebrum name=dns_ipv6_subnet]
               WHERE NOT (:max < ip_min OR :min > ip_max)""", binds)

        if overlap_entries:
            overlaps = ["%s/%s" % (o['subnet_ip'],
                                   IPv6Subnet.calculate_subnet_mask(o['ip_min'], o['ip_max']))
                                   for o in overlap_entries]
            raise SubnetError, ("Subnet '%s/%s' overlaps with the following subnet(s): '%s'" %
                                  (self.subnet_ip, self.subnet_mask, "', '".join(overlaps)))


    def calculate_reserved_addresses(self):
        """Populates the list over reserved addresses.
        """
        # If no_of_reserved_adr is 0
        if self.no_of_reserved_adr == 0:
            self.reserved_adr = set()
            return
        
        # First, check that we aren't trying to reserve more addresses
        # than there are in the subnet. Don't count the subnet's
        # address itself, since the number is for counting addresses
        # after it.
        if (self.ip_min + self.no_of_reserved_adr) > self.ip_max:
            raise SubnetError, ("Trying to reserve %i addresses in a subnet " %
                                self.no_of_reserved_adr + 
                                "that has %i addresses available. " %
                                (self.ip_max - self.ip_min) +
                                "You can't do that! Because it's *wrong*")
        
        # Designate the first X adresses in subnet as reserved,
        # where X equals the, number specifically set as reserved addresses.
        self.reserved_adr = set([x + self.ip_min for
                                 x in range(self.no_of_reserved_adr)])


    def has_adresses_in_use(self):
        """Check whether or not there are any IPs in use on this subnet.

        Return 'True' if there are.

        """
        # Need to import Utils here, since Utils imports this module,
        # and we cannot have circular module dependencies.
        from Cerebrum.modules.dns.Utils import Find
        default_zone = self.const.DnsZone("uio")
        find = Find(self._db, default_zone)
        
        if find.find_used_ips(self.subnet_ip):
            return True
        else:
            return False


    def check_reserved_addresses_in_use(self):
        """Raise a SubnetError if this subnet has addresses in use, that are
        really reserved.
        """
        ip_number = IPv6Number.IPv6Number(self._db)
        ip_number.clear()

        res_adr_in_use = []

        for row in ip_number.find_in_range(self.ip_min, self.ip_max):
            current_address = IPv6Calc.ip_to_long(row['aaaa_ip'])
            if current_address in self.reserved_adr:
                res_adr_in_use.append(row['aaaa_ip'])
 
        if res_adr_in_use:
            res_adr_in_use.sort()
            raise SubnetError, ("The following reserved ip's are already in " +
                                "use on (new?) subnet %s/%s: " %
                                (self.subnet_ip, self.subnet_mask) +
                                "'%s'." % (', '.join(res_adr_in_use)))


    def write_db(self, perform_checks=True):
        """Write subnet instance to database.

        If this instance has a ``entity_id`` attribute (inherited from
        class Entity), this Subnet entity is already present in the
        Cerebrum database, and we'll use UPDATE to bring the instance
        in sync with the database.

        Otherwise, a new entity_id is generated and used to insert
        this object.

        """
        self.__super.write_db()
        if not self.__updated:
            return
 
        is_new = not self.__in_db

        # With some DB-interfaces (e.g. psycopg 1), DB-booleans may be
        # returned as ints; make sure that dns_delegated truly is a
        # boolean. This should probably be handled more generally
        # than just here, but this is currently the only place
        # DB-booleans are in use.
        
        # Since self.dns_delegated often is an int when it arrives
        # here, it will need to be "reset" to None before it can be
        # set to a boolean value". Sometimes stuff just works in
        # mysterious ways...
        if self.dns_delegated:
            self.dns_delegated = None
            self.dns_delegated = True
        else:
            self.dns_delegated = None
            self.dns_delegated = False

        if is_new:
            # Only need to check for overlaps when subnet is being
            # added, since a subnet's ip-range is never changed.
            self.check_for_overlaps()

            if perform_checks:
                self.check_reserved_addresses_in_use()
        
            cols = [('entity_type', ':e_type'),
                    ('entity_id', ':ent_id'),
                    ('subnet_ip', ':subnet_ip'),
                    ('ip_min', ':ip_min'),
                    ('ip_max', ':ip_max'),
                    ('no_of_reserved_adr', ':res_adr'),
                    ('description', ':desc')]
            if self.vlan is not None:
                cols.append(('vlan_number', ':vlan'))
            self.execute("""
            INSERT INTO [:table schema=cerebrum name=dns_ipv6_subnet] (%(tcols)s)
            VALUES (%(binds)s)""" % {'tcols': ", ".join([x[0] for x in cols]),
                                     'binds': ", ".join([x[1] for x in cols])},
                                    {'e_type': int(self.const.entity_dns_ipv6_subnet),
                                     'ent_id': self.entity_id,
                                     'subnet_ip': self.subnet_ip,
                                     'ip_min': self.ip_min,
                                     'ip_max': self.ip_max,
                                     'desc': self.description,
                                     'res_adr': self.no_of_reserved_adr,
                                     'vlan': self.vlan})
            self._db.log_change(self.entity_id, self.const.subnet6_create, None)

        else:
            if perform_checks:
                self.check_reserved_addresses_in_use()

            cols = [('description', ':desc'),
                    ('no_of_reserved_adr', ':res_adr'),
                    ('vlan_number', ':vlan'),
                    ('dns_delegated', ':dns_delegated'),
                    ('name_prefix', ':name_pre')]
            binds = {'e_id': self.entity_id,
                     'desc': self.description,
                     'vlan': self.vlan_number,
                     'dns_delegated': self.dns_delegated,
                     'name_pre': self.name_prefix,
                     'res_adr': self.no_of_reserved_adr
                     }
            self.execute("""
            UPDATE [:table schema=cerebrum name=dns_ipv6_subnet]
            SET %(defs)s
            WHERE entity_id=:e_id""" % {'defs': ", ".join(
                ["%s=%s" % x for x in cols if x[0] <> 'entity_id'])},
                         binds)
            self._db.log_change(self.entity_id, self.const.subnet6_mod, None,
                                change_params=binds)
        
        del self.__in_db
        self.__in_db = True
        self.__updated = []
        return is_new


    def delete(self, perform_checks=True):
        if perform_checks:
            if self.has_adresses_in_use():
                raise SubnetError, (
                "Subnet '%s/%s' cannot be deleted; it has addresses in use" %
                                    (self.subnet_ip, self.subnet_mask))
        
        self._db.log_change(self.entity_id, self.const.subnet6_delete, None)
        if self.__in_db:
             self.execute("""
             DELETE FROM [:table schema=cerebrum name=dns_ipv6_subnet]
             WHERE entity_id=:e_id""", {'e_id': self.entity_id})            
        self.__super.delete()


    def new(self):
        """Insert a new subnet into the database."""
        self.populate()
        self.write_db()
        self.find(self.entity_id)


    def find(self, identifier):
        binds = {}

        if identifier is None:
            raise SubnetError("Unable to find subnet identified by '%s'" %
                                identifier)
            
        if 'id:' in identifier or 'entity_id:' in identifier:
            # E.g. 'id:X' or 'entity_id:X';
            where_param = "entity_id = :e_id"
            binds['e_id'] = int(identifier.split(':')[1])
        elif identifier.find('/') > 0:
            # A '/' indicates a subnet spec: just need the ip
            where_param = "subnet_ip = :subnet_ip"
            subnet_ip = identifier.split('/')[0]
            binds['subnet_ip'] = IPv6Utils.explode(subnet_ip)
        else:
            # Last valid type is simply an IP; need to find correct range
            where_param = "ip_min <= :ip AND ip_max >= :ip"
            binds['ip'] = IPv6Calc.ip_to_long(identifier)
            
        try:
            (self.entity_id, self.subnet_ip, self.ip_min, self.ip_max,
             self.description, self.dns_delegated, self.name_prefix,
             self.vlan_number, self.no_of_reserved_adr) = self.query_1(
                """ SELECT entity_id, subnet_ip, ip_min, ip_max, description,
                           dns_delegated, name_prefix, vlan_number,
                           no_of_reserved_adr
                    FROM [:table schema=cerebrum name=dns_ipv6_subnet]
                    WHERE %s""" % where_param, binds)
            
            self.subnet_mask = IPv6Subnet.calculate_subnet_mask(self.ip_min,
                                                                self.ip_max)
            self.calculate_reserved_addresses()
            
        except NotFoundError:
            raise SubnetError("Unable to find subnet identified by '%s'" %
                                identifier)

        self.__in_db = True
        self.__updated = []


    def search(self):
        """Search for subnets that satisfy given criteria.

        Currently, no criteria can be given, hence all subnets are
        returned.

        """
        # Need to insert a dummy value as placeholder for subnet_mask,
        # since we later wish to calculate the proper value for it,
        # and db_row won't allow us to insert new keys into the
        # result's rows.
        result = self.query(
            """SELECT entity_id, subnet_ip, 1 AS subnet_mask, ip_min, ip_max,
                      description, dns_delegated, name_prefix, vlan_number,
                      no_of_reserved_adr
               FROM [:table schema=cerebrum name=dns_ipv6_subnet]""")
        
        for row in result:
            row["subnet_mask"] = IPv6Subnet.calculate_subnet_mask(row['ip_min'],
                    row['ip_max'])

        return result

if __name__ == '__main__':
    pass