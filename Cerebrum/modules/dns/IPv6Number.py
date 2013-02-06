# -*- coding: iso-8859-1 -*-

import struct
import socket
import re

from Cerebrum import Entity
from Cerebrum.DatabaseAccessor import DatabaseAccessor
from Cerebrum import Utils
from Cerebrum.modules.dns.Errors import DNSError
from Cerebrum.modules.bofhd.errors import CerebrumError

class IPv6Number(Entity.Entity):
    """``IPv6Number.IPv6Number(DatabaseAccessor)`` primarely updates the
    dns_ipv6_number table.  It also has methods for handling the
    reverse-map entries in dns_override_reversemap_ipv6.  It uses the
    standard Cerebrum populate logic for handling updates."""

    __read_attr__ = ('__in_db',)
    __write_attr__ = ('aaaa_ip', 'mac_adr')

    def __normalize_address(self, aaaa_ip):
        # We check if the address is valid:
        try:
            socket.inet_pton(socket.AF_INET6, aaaa_ip)
            #return socket.inet_ntop(socket.AF_INET6, aaaa_ip)
        except socket.error:
            raise CerebrumError, 'Invalid IPv6 address'
        # Then we'll expand it. This makes searching easier:
        ip = aaaa_ip.split(':')
        eip = []
        for i in range(0, len(ip)):
            if len(ip[i]) == 0:
                eip += ['0000' for x in range(0, 9-len(ip))]
            elif len(ip[i]) < 4:
                tmp = '%4s' % ip[i]
                tmp = tmp.replace(' ', '0')
                eip += [tmp]
            else:
                eip += [ip[i]]
        return ':'.join(eip)

    def clear(self):
        self.__super.clear()
        self.clear_class(IPv6Number)
        self.__updated = []


    def populate(self, aaaa_ip=None, parent=None, mac_adr=None):
        if parent is not None:
            self.__xerox__(parent)
        else:
            Entity.Entity.populate(self, self.const.entity_dns_ipv6_number)
        try:
            if not self.__in_db:
                raise RuntimeError, "populate() called multiple times."
        except AttributeError:
            self.__in_db = False
        for k in locals().keys():
            if k != 'self':
                setattr(self, k, locals()[k])

    def __eq__(self, other):
        assert isinstance(other, IPv6Number)
        if (self.aaaa_ip != other.aaaa_ip):
            return False
        return self.__super.__eq__(other)

    def write_db(self):
        self.__super.write_db()
        if not self.__updated:
            return
        is_new = not self.__in_db

        if 'aaaa_ip' in self.__updated:  # normalize the address
            self.aaaa_ip = self.__normalize_address(self.aaaa_ip)

        if 'mac_adr' in self.__updated and self.mac_adr is not None:
            self.mac_adr = self._verify_mac_format(self.mac_adr)

        cols = [('ipv6_number_id', ':ipv6_number_id'),
                ('aaaa_ip', ':aaaa_ip'),
                ('mac_adr', ':mac_adr')]
        binds = {'ipv6_number_id': self.entity_id,
                 'aaaa_ip': self.aaaa_ip,
                 'mac_adr': self.mac_adr}

        if is_new:
            self.execute("""
            INSERT INTO [:table schema=cerebrum name=dns_ipv6_number] (%(tcols)s)
            VALUES (%(binds)s)""" % {'tcols': ", ".join([x[0] for x in cols]),
                                     'binds': ", ".join([x[1] for x in cols])},
                         binds)
            self._db.log_change(self.entity_id, self.const.ipv6_number_add,
                                None, change_params={'aaaa_ip': self.aaaa_ip})
        else:
            self.execute("""
            UPDATE [:table schema=cerebrum name=dns_ipv6_number]
            SET %(defs)s
            WHERE ipv6_number_id=:ipv6_number_id""" % {'defs': ", ".join(
                ["%s=%s" % x for x in cols])}, binds)
            self._db.log_change(self.entity_id, self.const.ipv6_number_add,
                                None, change_params={'aaaa_ip': self.aaaa_ip})
        del self.__in_db

        if 'mac_adr' in self.__updated:
            self._db.log_change(self.entity_id, self.const.mac_adr_set,
                                None, change_params={'mac_adr': self.mac_adr})
            
        self.__in_db = True
        self.__updated = []
        return is_new

    def find(self, ipv6_number_id):
        self.__super.find(ipv6_number_id)

        (self.aaaa_ip, self.mac_adr) = self.query_1("""
        SELECT aaaa_ip, mac_adr
        FROM [:table schema=cerebrum name=dns_ipv6_number]
        WHERE ipv6_number_id=:ipv6_number_id""", {'ipv6_number_id' : ipv6_number_id})
        #self.hostname = self.get_name(self.const.hostname_namespace)
        try:
            del self.__in_db
        except AttributeError:
            pass
        self.__in_db = True
        self.__updated = []


    def find_by_ip(self, aaaa_ip):
        aaaa_ip = self.__normalize_address(aaaa_ip)

        ipv6_number_id = self.query_1("""
        SELECT ipv6_number_id
        FROM [:table schema=cerebrum name=dns_ipv6_number]
        WHERE aaaa_ip=:aaaa_ip""", {'aaaa_ip': aaaa_ip})
        self.find(ipv6_number_id)


    def find_by_mac(self, mac):
        return self.query("""
        SELECT aaaa_ip, mac_adr
        FROM [:table schema=cerebrum name=dns_ipv6_number]
        WHERE mac_adr=:mac_adr""", {'mac_adr': mac})

    def find_in_range(self, start, stop):
        return self.query("""
        SELECT ipv6_number_id, aaaa_ip, mac_adr
        FROM [:table schema=cerebrum name=dns_ipv6_number]
        WHERE aaaa_ip >= :start AND aaaa_ip <= :stop""", {
            'start': start,
            'stop': stop})

    def list(self, start=None, stop=None):
        where_list = []
        if start is not None:
            where_list.append("aaaa_ip >= :start")
        if stop is not None:
            where_list.append("aaaa_ip <= :stop")
        if where_list:
            where = "WHERE " + " AND ".join(where_list)
        else:
            where = ""
        
        return self.query("""
        SELECT ipv6_number_id, aaaa_ip, mac_adr
        FROM [:table schema=cerebrum name=dns_ipv6_number]
        %s""" % where, {'start': start, 'stop': stop})


    def delete(self):
        assert self.entity_id
        self.execute("""
        DELETE FROM [:table schema=cerebrum name=dns_ipv6_number]
        WHERE ipv6_number_id=:ipv6_number_id""", {'ipv6_number_id': self.entity_id})
        self._db.log_change(self.entity_id, self.const.ipv6_number_add, None)
        self.__super.delete()


    def _verify_mac_format(self, mac_adr):
        """Checks that the given MAC-address is written with an
        acceptable format. If so, it returns the MAC address on the
        standardized format.

        Acceptable formats:
        * Valid seperators are ':', '-', '.' and ' '
        * Numbers are hexa-decimal. Capitalization doesn't matter
        * Seperators between every 2 or 4 numbers

        Standardized format:
        * Only ':' used as seperator, between every two numbers
        * Only lowercase hexa-decimal numbers.
        
        @type mac_adr: string
        @param mac_adr: The MAC address that is to be verified

        @rtype: string
        @return: The MAC-address as formatted to the standard format

        @raise DNSError: If mac_adr isn't formatted in any valid way

        """
        # Prepare error message for possible later use
        error_msg = ("Invalid MAC-address: '%s'. " % mac_adr +
                     "Try something like '01:23:45:67:89:ab' instead")

        # Standardize case
        mac_adr = mac_adr.lower()
        # Standardize seperator character
        for char in ('-', '.', ' '):
            mac_adr = mac_adr.replace(char, ":")
        # Standardize if using Cisco format or no seperators at all
        for index in (2, 5, 8, 11, 14):
            try:
                if not mac_adr[index] == ':':
                    mac_adr = mac_adr[0:index] + ':' + mac_adr[index:]
            except IndexError:
                raise DNSError(error_msg)
        
        if not re.search("^([a-f0-9]{2}:){5}[a-f0-9]{2}$", mac_adr):
            raise DNSError(error_msg)

        return mac_adr
        

    # Now that the actual IP is no longer stored in the a_record
    # table, one might argue that the below methods should be moved to
    # another class


    def __fill_coldata(self, coldata):
        binds = coldata.copy()
        del(binds['self'])            
        cols = [ ("%s" % x, ":%s" % x) for x in binds.keys() ]
        return cols, binds


    def add_reverse_override(self, ipv6_number_id, dns_owner_id):
        cols, binds = self.__fill_coldata(locals())
        self.execute("""
        INSERT INTO [:table schema=cerebrum name=dns_override_reversemap_ipv6] (%(tcols)s)
        VALUES (%(binds)s)""" % {'tcols': ", ".join([x[0] for x in cols]),
                                 'binds': ", ".join([x[1] for x in cols])},
                     binds)
        self._db.log_change(ipv6_number_id, self.const.ipv6_number_add, dns_owner_id)


    def delete_reverse_override(self, ipv6_number_id, dns_owner_id):
        if not dns_owner_id:
            where = "dns_owner_id IS NULL"
        else:
            where = "dns_owner_id=:dns_owner_id"
        return self.execute("""
        DELETE FROM [:table schema=cerebrum name=dns_override_reversemap_ipv6]
        WHERE ipv6_number_id=:ipv6_number_id AND %s""" % where,
                            locals())
        self._db.log_change(ipv6_number_id, self.const.ipv6_number_del,
                            dns_owner_id)


    def update_reverse_override(self, ipv6_number_id, dns_owner_id):
        self.execute("""
        UPDATE [:table schema=cerebrum name=dns_override_reversemap_ipv6]
        SET dns_owner_id=:dns_owner_id
        WHERE ipv6_number_id=:ipv6_number_id""", locals())
        self._db.log_change(ipv6_number_id, self.const.ipv6_number_update, dns_owner_id)


    def list_override(self, ip_number_id=None, start=None, stop=None, dns_owner_id=None):
        where = []
        if ip_number_id:
            where.append("ovr.ipv6_number_id=:ipv6_number_id")
        if start is not None:
            where.append("dip.aaaa_ip >= :start")
        if stop is not None:
            where.append("dip.aaaa_ip <= :stop")
        if dns_owner_id is not None:
            where.append("ovr.dns_owner_id = :dns_owner_id")            
        if where:
            where = "AND " + " AND ".join(where)
        else:
            where = ''
        return self.query("""
        SELECT ovr.ipv6_number_id, ovr.dns_owner_id, dip.aaaa_ip,
               en.entity_name AS name
        FROM [:table schema=cerebrum name=dns_override_reversemap_ipv6] ovr JOIN
             [:table schema=cerebrum name=dns_ipv6_number] dip ON (
               ovr.ipv6_number_id=dip.ipv6_number_id %s)
             LEFT JOIN [:table schema=cerebrum name=entity_name] en ON
               ovr.dns_owner_id=en.entity_id
        """ % where, {'ipv6_number_id': ip_number_id, 'dns_owner_id': dns_owner_id,
                      'start': start, 'stop': stop})