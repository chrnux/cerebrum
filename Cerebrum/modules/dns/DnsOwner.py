# -*- coding: iso-8859-1 -*-

from Cerebrum import Utils
from Cerebrum.DatabaseAccessor import DatabaseAccessor
from Cerebrum.Entity import Entity, EntityName
from Cerebrum import Errors
from Cerebrum.modules import dns
from Cerebrum.modules.dns.DnsConstants import _DnsZoneCode

class MXSet(DatabaseAccessor):
    """``DnsOwner.MXSet(DatabaseAccessor)`` handles the dns_mx_set and
    dns_mx_set_members tables.  It uses the standard Cerebrum populate
    logic for handling updates."""

    __metaclass__ = Utils.mark_update

    __read_attr__ = ('__in_db',)
    __write_attr__ = ('name', 'mx_set_id')

    def __init__(self, database):
        super(MXSet, self).__init__(database)
        self.clear()

    def clear_class(self, cls):
        for attr in cls.__read_attr__:
            if hasattr(self, attr):
                if attr not in getattr(cls, 'dontclear', ()):
                    delattr(self, attr)
        for attr in cls.__write_attr__:
            if attr not in getattr(cls, 'dontclear', ()):
                setattr(self, attr, None)

    def clear(self):
        self.clear_class(MXSet)
        self.__updated = []

    def populate(self, name):
        try:
            if not self.__in_db:
                raise RuntimeError, "populate() called multiple times."
        except AttributeError:
            self.__in_db = False
        self.name = name

    def __eq__(self, other):
        assert isinstance(other, MXSet)
        return self.name == other.name

    def write_db(self):
        if not self.__updated:
            return
        is_new = not self.__in_db
        if is_new:
            self.mx_set_id = int(self.nextval('ip_number_id_seq'))
        binds = {'mx_set_id': self.mx_set_id,
                 'name': self.name}
        if is_new:
            # Use same sequence as for ip-numbers for simplicity
            self.execute("""
            INSERT INTO [:table schema=cerebrum name=dns_mx_set]
              (mx_set_id, name)
            VALUES (:mx_set_id, :name)""", binds)
        else:
            self.execute("""
            UPDATE [:table schema=cerebrum name=dns_mx_set]
            SET name=:name
            WHERE mx_set_id=:mx_set_id""", binds)
        del self.__in_db
        
        self.__in_db = True
        self.__updated = []
        return is_new

    def find(self, mx_set_id):
        self.mx_set_id, self.name = self.query_1("""
        SELECT mx_set_id, name
        FROM [:table schema=cerebrum name=dns_mx_set]
        WHERE mx_set_id=:mx_set_id""", {'mx_set_id': mx_set_id})
        try:
            del self.__in_db
        except AttributeError:
            pass
        self.__in_db = True
        self.__updated = []

    def find_by_name(self, name):
        mx_set_id= self.query_1("""
        SELECT mx_set_id
        FROM [:table schema=cerebrum name=dns_mx_set]
        WHERE name=:name""", {'name': name})
        self.find(mx_set_id)

    def list(self):
        return self.query("""
        SELECT mx_set_id, name
        FROM [:table schema=cerebrum name=dns_mx_set]""")

    def list_mx_sets(self, mx_set_id=None, target_id=None):
        where = ['mxs.target_id=d.dns_owner_id',
                 'mxs.target_id=en.entity_id']
        if mx_set_id:
            where.append('mxs.mx_set_id=:mx_set_id')
        if target_id:
            where.append('target_id=:target_id')
        where = " AND ".join(where)
        return self.query("""
        SELECT mxs.mx_set_id, ttl, pri, target_id, en.entity_name AS target_name
        FROM [:table schema=cerebrum name=dns_mx_set_member] mxs,
             [:table schema=cerebrum name=dns_owner] d,
             [:table schema=cerebrum name=entity_name] en
        WHERE %s
        ORDER BY mxs.mx_set_id""" % where, {
            'mx_set_id': mx_set_id,
            'target_id': target_id})

    def add_mx_set_member(self, ttl, pri, target_id):
        binds = {'mx_set_id': self.mx_set_id,
                 'ttl': ttl,
                 'pri': pri,
                 'target_id': target_id}
        self.execute("""
        INSERT INTO [:table schema=cerebrum name=dns_mx_set_member] (%s)
        VALUES (%s)""" % (", ".join(binds.keys()),
                          ", ".join([":%s" % k for k in binds.keys()])),
                     binds)

    def del_mx_set_member(self, target_id):
        return self.execute("""
        DELETE FROM [:table schema=cerebrum name=mx_set_member]
        WHERE mx_set_id=:mx_set_id AND target_id=:target_id""", {
            'mx_set_id': self.mx_set_id, 'target_id': target_id})

    def update_mx_set_member(self, ttl, pri, target_id):
        return self.execute("""
        UPDATE [:table schema=cerebrum name=mx_set_member]
        SET ttl=:ttl, pri=:pri
        WHERE mx_set_id=:mx_set_id AND target_id=:target_id""", {
            'mx_set_id': self.mx_set_id, 'target_id': target_id,
            'ttl': ttl, 'pri': pri})

    def delete(self):
        return self.execute("""
        DELETE FROM [:table schema=cerebrum name=mx_set]
        WHERE mx_set_id=:mx_set_id""", {
            'mx_set_id': self.mx_set_id})
        
class GeneralDnsRecord(object):
    """``DnsOwner.GeneralDnsRecord(object)`` is a mix-in class for
    additional TTL-enabled data like TXT records."""

    def __fill_coldata(self, coldata):
        binds = coldata.copy()
        del(binds['self'])
        binds['field_type'] = int(binds['field_type'])
        cols = [ ("%s" % x, ":%s" % x) for x in binds.keys() ]
        return cols, binds

    def get_general_dns_record(self, dns_owner_id, field_type):
        return self.query_1("""
        SELECT ttl, data
        FROM [:table schema=cerebrum name=dns_general_dns_record]
        WHERE dns_owner_id=:dns_owner_id AND field_type=:field_type""", locals())

    def add_general_dns_record(self, dns_owner_id, field_type, ttl, data):
        cols, binds = self.__fill_coldata(locals())
        self.execute("""
        INSERT INTO [:table schema=cerebrum name=dns_general_dns_record] (%(tcols)s)
        VALUES (%(binds)s)""" % {'tcols': ", ".join([x[0] for x in cols]),
                                 'binds': ", ".join([x[1] for x in cols])},
                     binds)

    def delete_general_dns_record(self, dns_owner_id, field_type=None):
        where = ['dns_owner_id=:dns_owner_id']
        if field_type:
            where.append('field_type=:field_type')
        where = " AND ".join(where)
        return self.execute("""
        DELETE FROM [:table schema=cerebrum name=dns_general_dns_record]
        WHERE  %s """ % where, locals())

    def update_general_dns_record(self, dns_owner_id, field_type, ttl, data):
        cols, binds = self.__fill_coldata(locals())
        self.execute("""
        UPDATE [:table schema=cerebrum name=dns_general_dns_record]
        SET %(defs)s
        WHERE dns_owner_id=:dns_owner_id AND field_type=:field_type""" % {'defs': ", ".join(
            ["%s=%s" % x for x in cols])}, binds)

    def list_general_dns_records(self, field_type=None, dns_owner_id=None):
        where = []
        if field_type is not None:
            field_type = int(field_type)
            where.append("field_type=:field_type")
        if dns_owner_id is not None:
            where.append("dns_owner_id=:dns_owner_id")
        if where:
            where = "WHERE "+" AND ".join(where)
        else:
            where = ""
        return self.query("""
        SELECT dns_owner_id, field_type, ttl, data
        FROM [:table schema=cerebrum name=dns_general_dns_record] %s""" % where,
                          locals())

class DnsOwner(GeneralDnsRecord, EntityName, Entity):
    """``DnsOwner(GeneralDnsRecord, Entity)`` primarily updates the
    DnsOwner table using the standard Cerebrum populate framework.

    The actual name of the machine is stored using EntityName.  Names
    are stored as fully-qualified, including the trailing dot, and all
    share the same namespace (const.dns_namespace).  This makes
    netgroup handling easier.

    The only purpose of the dns_zone table is to group which hosts
    should be included in the forward-map (in the reverse-map this is
    deduced from the ip-number).
    """

    __read_attr__ = ('__in_db',)
    __write_attr__ = ('name', 'mx_set_id', 'zone')

    def clear(self):
        super(DnsOwner, self).clear()
        self.clear_class(DnsOwner)
        self.__updated = []

    def populate(self, zone, name, mx_set_id=None, parent=None):
        """zone may either be a number or a DnsZone constant"""
        if parent is not None:
            self.__xerox__(parent)
        else:
            Entity.populate(self, self.const.entity_dns_owner)
        try:
            if not self.__in_db:
                raise RuntimeError, "populate() called multiple times."
        except AttributeError:
            self.__in_db = False
        self.name = name
        self.mx_set_id = mx_set_id
        self.zone = zone

    def __eq__(self, other):
        assert isinstance(other, DnsOwner)
        return (self.name == other.name and
                self.mx_set_id == other.mx_set_id)
    
    def write_db(self):
        self.__super.write_db()
        if not self.__updated:
            return
        is_new = not self.__in_db

        binds = {
            'e_id': self.entity_id,
            'e_type': int(self.const.entity_dns_owner),
            'name': self.name,
            'mx_set_id': self.mx_set_id}

        # Do some primitive checks to assert that name is a FQDN, and
        # that the zone matches the DN.
        if not self.name[-1] == '.':
            raise ValueError("hostname must be fully qualified")
        if isinstance(self.zone, _DnsZoneCode):
            if (self.zone.postfix is not None and
                not self.name.endswith(self.zone.postfix)):
                raise ValueError("Zone mismatch for %s" % self.name)
            binds['zone_id'] = self.zone.zone_id
        else:
            binds['zone_id'] = self.zone
        if is_new:
            self.execute("""
            INSERT INTO [:table schema=cerebrum name=dns_owner]
              (dns_owner_id, entity_type, mx_set_id, zone_id)
            VALUES (:e_id, :e_type, :mx_set_id, :zone_id)""", binds)
            self.add_entity_name(self.const.dns_owner_namespace, self.name)
        else:
            self.execute("""
            UPDATE [:table schema=cerebrum name=dns_owner]
            SET mx_set_id=:mx_set_id
            WHERE dns_owner_id=:e_id""", binds)
            if 'name' in self.__updated:
                self.update_entity_name(self.const.dns_owner_namespace, self.name)
        del self.__in_db
        
        self.__in_db = True
        self.__updated = []
        return is_new

    def find(self, host_id):
        self.__super.find(host_id)
        self.zone, self.mx_set_id = self.query_1("""
        SELECT zone_id, mx_set_id
        FROM [:table schema=cerebrum name=dns_owner]
        WHERE dns_owner_id=:e_id""", {'e_id': self.entity_id})
        self.name = self.get_name(self.const.dns_owner_namespace)
        try:
            del self.__in_db
        except AttributeError:
            pass
        self.__in_db = True
        self.__updated = []

    def find_by_name(self, name):
        EntityName.find_by_name(self, name, self.const.dns_owner_namespace)

    def delete(self):
        for r in self.list_srv_records(owner_id=self.entity_id):
            self.delete_srv_record(
                r['service_owner_id'], r['pri'], r['weight'], r['port'])
        self.execute("""
        DELETE FROM [:table schema=cerebrum name=dns_owner]
        WHERE dns_owner_id=:dns_owner_id""", {'dns_owner_id': self.entity_id})
        self.__super.delete()

    def list(self):
        return self.query("""
        SELECT dns_owner_id, mx_set_id, en.entity_name AS name
        FROM [:table schema=cerebrum name=dns_owner] d,
             [:table schema=cerebrum name=entity_name] en
        WHERE d.dns_owner_id=en.entity_id""")

    # TBD: Should we have the SRV methods in a separate class?  The
    # methods are currently not connected with the object in any way.

    def __fill_coldata(self, coldata):
        binds = coldata.copy()
        del(binds['self'])            
        cols = [ ("%s" % x, ":%s" % x) for x in binds.keys() ]
        return cols, binds

    def add_srv_record(self, service_owner_id, pri, weight, port, ttl,
                       target_owner_id):
        cols, binds = self.__fill_coldata(locals())
        self.execute("""
        INSERT INTO [:table schema=cerebrum name=dns_srv_record] (%(tcols)s)
        VALUES (%(binds)s)""" % {'tcols': ", ".join([x[0] for x in cols]),
                                 'binds': ", ".join([x[1] for x in cols])},
                     binds)

    def delete_srv_record(self, service_owner_id, pri, weight, port,
                          target_owner_id):
        cols, binds = self.__fill_coldata(locals())
        return self.execute("""
        DELETE FROM [:table schema=cerebrum name=dns_srv_record]
        WHERE %s""" % " AND ".join(["%s=%s" % (x[0], x[1])
                                    for x in cols]), binds)

    def list_srv_records(self, owner_id=None, target_owner_id=None):
        where = ['srv.target_owner_id=d_tgt.dns_owner_id',
                 'srv.service_owner_id=d_own.dns_owner_id',
                 'srv.target_owner_id=en_tgt.entity_id',
                 'srv.service_owner_id=en_own.entity_id']
        if owner_id is not None:
            where.append("service_owner_id=:owner_id")
        if target_owner_id is not None:
            where.append("target_owner_id=:target_owner_id")
        where = " AND ".join(where)
        return self.query("""
        SELECT service_owner_id, pri, weight, port, ttl,
               target_owner_id, en_tgt.entity_name AS target_name,
               en_own.entity_name AS service_name
        FROM [:table schema=cerebrum name=dns_srv_record] srv,
             [:table schema=cerebrum name=dns_owner] d_own,
             [:table schema=cerebrum name=dns_owner] d_tgt,
             [:table schema=cerebrum name=entity_name] en_own,
             [:table schema=cerebrum name=entity_name] en_tgt
        WHERE %s""" % where, {
            'owner_id': owner_id,
            'target_owner_id': target_owner_id} )

    # We don't support update_srv_record as the PK is too wide.

# arch-tag: 5956ec5e-b6e7-4747-9188-233ed7a8007a
