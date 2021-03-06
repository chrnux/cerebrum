# -*- coding: iso-8859-1 -*-

# Copyright 2003 University of Oslo, Norway
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

import re
import time

from Cerebrum.Utils import Factory
from Cerebrum.modules.no.uio.access_FS import FS
from Cerebrum import Database
from Cerebrum.extlib import xmlprinter
from Cerebrum import Person
from Cerebrum import Errors

# TODO: This file should not have UiO hardcoded data in it
SYDRadmins = ['baardj', 'frankjs', 'jazz']
DMLadmins = ['lindaj', 'hallgerb', 'maskoger', 'jonar', 'helgeu',
             'kaugedal', 'rinos', 'monahst']
AllAdmins = SYDRadmins + DMLadmins
host_config = {
    'hiafronter.fronter.no': { 'DBinst': 'DLOPROD.uio.no',
                       'admins': AllAdmins,
                       'export': ['FS', 'All_users'],
                       'spread': 'spread_hia_fronter'
                       },
    }

#class AccessFronter(object):
#    def __init__(self, db):
#        self.db = db

#    def ListUserInfo(self):
#        return self.db.query("""
#SELECT username, password, firstname, lastname, email
#FROM persontbl2 p
#WHERE username IS NOT NULL AND
#      importid IS NOT NULL AND
#      EXISTS (SELECT 'x' FROM memberstbl m WHERE m.personid = p.id)""")
    
#    def ListGroupInfo(self):
#        return self.db.query("""
#SELECT c.importid, c.title, c.allowsflag, p.importid AS parent_importid
#FROM structuregrouptbl c, structuregrouptbl p
#WHERE c.parent = p.id AND
#      c.importid IS NOT NULL
#UNION
#SELECT importid, title, allowsflag, importid
#FROM structuregrouptbl
#WHERE parent <= 0 AND
#      importid IS NOT NULL""")

#    def GetGroupMembers(self, gid):
#        return self.db.query("""
#SELECT p.username
#FROM persontbl2 p, memberstbl m
#WHERE m.groupid = :gid AND
#      m.personid = p.id AND
#      p.importid IS NOT NULL""", {'gid': gid})
#
#    def ListAllGroupMembers(self):
#        return self.db.query("""
#SELECT g.importid, p.username
#FROM persontbl2 p, structuregrouptbl g, memberstbl m
#WHERE g.importid IS NOT NULL AND
#      g.id = m.groupid AND
#      p.id = m.personid AND
#      p.importid IS NOT NULL""")
#
#    def ListGroupsACL(self):
#        return self.db.query("""
#SELECT s.importid AS structid, g.importid AS groupid, a.group_access, a.room_access
#FROM structuregrouptbl s, structuregrouptbl g, structureacl a
#WHERE s.importid IS NOT NULL AND
#      s.id = a.structid AND
#      g.id = a.groupid AND
#      g.importid IS NOT NULL""")

#    def ListRoomInfo(self):
#        return self.db.query("""
#SELECT r.importid AS room, r.title, s.importid AS structid, r.profile
#FROM projecttbl2 r, structuregrouptbl s
#WHERE r.structureid = s.id AND
#      r.importid IS NOT NULL""")
#
#    def ListRoomsACL(self):
#        return self.db.query("""
#SELECT r.importid AS roomid, g.importid AS groupid, a.read_access, a.write_access,
#       a.delete_access, a.change_access
#FROM projecttbl2 r, structuregrouptbl g, acl a
#WHERE r.importid IS NOT NULL AND
#      r.id = a.prjid AND
#      g.id = a.groupid AND
#      g.importid IS NOT NULL""")

#    def GetProfileId(self, title):
#        try:
#            return self.db.query_1("""
#            SELECT id FROM ProfileTbl WHERE title=:title""", {'title': title})
#        except Errors.NotFoundError:
#            # Bruk "Vanlig prosjektmal" fra masterdata.
#            return 10

class FronterUtils(object):
    def UE2RomID(prefix, aar, termk, instnr, sko, romtype,
                 emnekode, versjon, termnr):
        """Lag rom-ID for undervisningsenhet.

        Lag Cerebrum-spesifikk 'rom-ID' av elementene i prim�rn�kkelen
        til en undervisningsenhet.  Denne rom-IDen forblir uforandret
        s� lenge kurset p�g�r; for flersemesterkurs vil den alts� ikke
        endres n�r man f.eks. kommer til ny undervisningsenhet
        pga. nytt semester.

        F�rste argument angir (case-sensitivt) prefiks for rom-IDen;
        de resterende argumentene vil alle bli konvertert til
        lowercase i den endelige IDen."""

        termnr = int(termnr)
        aar = int(aar)
        termk = termk.lower()
        # Rusle bakover i tid til vi kommer til undervisningsenheten i
        # samme kurs som denne, men med terminnr 1.  Pass dog p� �
        # ikke g� lenger tilbake enn h�st 2004 (det f�rste semesteret
        # HiA hadde automatisk synkronisering fra Cerebrum til
        # ClassFronter).
        def forrige_semester(termk, aar):
            if termk == 'h�st':
                return ('v�r', aar)
            elif termk == 'v�r':
                return ('h�st', aar - 1)
            else:
                # Vi krysser fingrene og h�per at det aldri vil
                # benyttes andre verdier for termk enn 'v�r' og
                # 'h�st', da det i s� fall vil bli vanskelig � vite
                # hvilket semester det var "for 2 semestere siden".
                raise ValueError, \
                      "ERROR: Unknown terminkode <%s> for emnekode <%s>." % (
                    termk, emnekode)

        while termnr > 1 and (termk, aar) != ('h�st', 2004):
            (termk, aar) = forrige_semester(termk, aar)
            termnr -= 1

        # I motsetning til ved UiO, m� termnr p� HiA tas med som en
        # del av den returnerte kurs-ID-strengen, da vi risikerer � ha
        # termnr forskjellig fra 1 for kurs med kursid i semesteret
        # h�st 2004.
        rom_id = ":".join([str(x).lower() for x in
                           (aar, termk, instnr, sko, romtype,
                            emnekode, versjon, termnr)])
        return ':'.join((prefix, rom_id))
    UE2RomID = staticmethod(UE2RomID)

class Fronter(object):
    STATUS_ADD = 1
    STATUS_UPDATE = 2
    STATUS_DELETE = 3

    ROLE_READ = '01'
    ROLE_WRITE = '02'
    ROLE_DELETE = '03'
    ROLE_CHANGE = '07'

    EMNE_PREFIX = 'KURS'

class XMLWriter(object):   # TODO: Move to separate file
    # TODO: should produce indented XML for easier readability
    def __init__(self, fname):
        self.gen = xmlprinter.xmlprinter(
            file(fname, 'w'), indent_level=2, data_mode=1,
            input_encoding='ISO-8859-1')

    def startTag(self, tag, attrs={}):
        a = {}
        for k in attrs.keys():   # saxutils don't like integers as values
            a[k] = "%s" % attrs[k]
        self.gen.startElement(tag, a)

    def endTag(self, tag):
        self.gen.endElement(tag)

    def emptyTag(self, tag, attrs={}):
        a = {}
        for k in attrs.keys():   # saxutils don't like integers as values
            a[k] = "%s" % attrs[k]
        self.gen.emptyElement(tag, a)

    def dataElement(self, tag, data, attrs={}):
        self.gen.dataElement(tag, data, attrs)

    def comment(self, data):  # TODO: implement
        self.gen.comment(data)
    
    def startDocument(self, encoding):
        self.gen.startDocument(encoding)

    def endDocument(self):
        self.gen.endDocument()

class FronterXML(object):
    def __init__(self, fname, cf_dir=None, debug_file=None, debug_level=None,
                 fronter=None, include_password=True):
        self.xml = XMLWriter(fname)
        self.xml.startDocument(encoding='ISO-8859-1')
        self.rootEl = 'enterprise'
        self.DataSource = 'cerebrum@hia.no'
        self.cf_dir = cf_dir
        self.debug_file = debug_file
        self.debug_level = debug_level
        self.fronter = fronter
        self.include_password = include_password
        #self.cf_id = self.fronter.DBinst.split(".")[0]
	self.cf_id = 'hiafronter'

    def start_xml_head(self):
	self.xml.comment("Eksporterer data for HiA\n")
	self.xml.startTag(self.rootEl)
        self.xml.startTag('properties')
        self.xml.dataElement('datasource', self.DataSource)
        self.xml.dataElement('datetime', time.strftime("%Y-%m-%d"))
        self.xml.endTag('properties')

    def start_xml_file(self, kurs2enhet):
        self.xml.comment("Eksporterer data om f�lgende emner:\n  " + 
                    "\n  ".join(kurs2enhet.keys()))
        self.xml.startTag(self.rootEl)
        self.xml.startTag('properties')
        self.xml.dataElement('datasource', self.DataSource)
        self.xml.dataElement('target', "ClassFronter/%s@hia.no" % self.cf_id)
        # :TODO: Tell Fronter (again) that they need to define the set of
        # codes for the TYPE element.
        # self.xml.dataElement('TYPE', "REFRESH")
        self.xml.dataElement('datetime', time.strftime("%Y-%m-%d"))
        self.xml.startTag('extension')
        self.xml.emptyTag('debug', {
            'debugdest': 0, # File
            'logpath': self.debug_file,
            'debuglevel': self.debug_level})
        self.xml.emptyTag('databasesettings', {
            'database': 0,	# Oracle
            'jdbcfilename': "%s/%s.dat" % (self.cf_dir, self.cf_id)
            })
        self.xml.endTag('extension')
        self.xml.endTag('properties')

    def user_to_XML(self, id, recstatus, data):
        """Lager XML for en person"""
        self.xml.startTag('person', {'recstatus': recstatus})
        self.xml.startTag('sourcedid')
        self.xml.dataElement('source', self.DataSource)
        self.xml.dataElement('id', id)
        self.xml.endTag('sourcedid')
        if (recstatus == Fronter.STATUS_ADD
            or recstatus == Fronter.STATUS_UPDATE):
            self.xml.startTag('name')
            self.xml.dataElement('fn', data['FN'])
            self.xml.startTag('n')
            self.xml.dataElement('family', data['FAMILY'])
            self.xml.dataElement('given', data['GIVEN'])
            self.xml.endTag('n')
            self.xml.endTag('name')
            self.xml.dataElement('email', data['EMAIL'])
            if data["MOBILE"]:
                self.xml.dataElement('tel', data["MOBILE"],
                                     {"teltype": "3"})
            # All persons are authenticated through LDAP,
            # that corresponds to pwencryptiontype="5" in the XML-entry
            if self.include_password:
                self.xml.dataElement('userid', id, {'pwencryptiontype': '5'})
            # All persons here have User access, so the value can be hardcoded.
            self.xml.emptyTag('systemrole', {'systemroletype': 'User'})
        self.xml.endTag('person')

    def group_to_XML(self, id, recstatus, data):
        # Lager XML for en gruppe
        if recstatus == Fronter.STATUS_DELETE:
            return
        self.xml.startTag('group', {'recstatus': recstatus})
        self.xml.startTag('sourcedid')
        self.xml.dataElement('source', self.DataSource)
        self.xml.dataElement('id', id)
        self.xml.endTag('sourcedid')
        if (recstatus == Fronter.STATUS_ADD or
            recstatus == Fronter.STATUS_UPDATE):
            self.xml.startTag('grouptype')
            self.xml.dataElement('scheme', 'FronterStructure1.0')
            # Unfortunately (?) allow_room/contact can have 'False' as value
            # associated with them. However, the DTD allows numbers only for
            # this attribute. 
            allow_room = data.get('allow_room', 0)
            if allow_room:
                allow_room = 1
            else:
                allow_room = 0
            allow_contact = data.get('allow_contact', 0)
            if allow_contact:
                allow_contact = 2
            else:
                allow_contact = 0
            self.xml.emptyTag('typevalue',
                              {'level': allow_room | allow_contact})
            self.xml.endTag('grouptype')
            self.xml.startTag('description')
            if (len(data['title']) > 60):
                self.xml.emptyTag('short')
                self.xml.dataElement('long', data['title'])
            else:
                self.xml.dataElement('short', data['title'])
            self.xml.endTag('description')
            self.xml.startTag('relationship', {'relation': 1})
            self.xml.startTag('sourcedid')
            self.xml.dataElement('source', self.DataSource)
            self.xml.dataElement('id', data['parent'])
            self.xml.endTag('sourcedid')
            self.xml.emptyTag('label')
            self.xml.endTag('relationship')
        self.xml.endTag('group')

    def room_to_XML(self, id, recstatus, data):
        # Lager XML for et rom
        #
        # Gamle rom skal aldri slettes automatisk.
        if recstatus == Fronter.STATUS_DELETE:
            return 
        self.xml.startTag('group', {'recstatus': recstatus})
        self.xml.startTag('sourcedid')
        self.xml.dataElement('source', self.DataSource)
        self.xml.dataElement('id', id)
        self.xml.endTag('sourcedid')
        if (recstatus == Fronter.STATUS_ADD or
            recstatus == Fronter.STATUS_UPDATE):
            self.xml.startTag('grouptype')
            self.xml.dataElement('scheme', 'FronterStructure1.0')
            self.xml.emptyTag('typevalue', {'level': 4})
            self.xml.endTag('grouptype')
            if True:
                # (recstatus == Fronter.STATUS_ADD):
                # Romprofil settes kun ved opprettelse av rommet, og vil
                # aldri senere tvinges tilbake til noen bestemt profil.
                self.xml.startTag('grouptype')
                self.xml.dataElement('scheme', 'Roomprofile1.0')
                self.xml.emptyTag('typevalue', {'level': data['profile']})
                self.xml.endTag('grouptype')

        self.xml.startTag('description')
        if (len(data['title']) > 60):
            self.xml.emptyTag('short')
            self.xml.dataElement('long', data['title'])
        else:
            self.xml.dataElement('short', data['title'])

        self.xml.endTag('description')
        self.xml.startTag('relationship', {'relation': 1})
        self.xml.startTag('sourcedid')
        self.xml.dataElement('source', self.DataSource)
        self.xml.dataElement('id', data['parent'])
        self.xml.endTag('sourcedid')
        self.xml.emptyTag('label')
        self.xml.endTag('relationship')
        self.xml.endTag('group')

    def personmembers_to_XML(self, gid, recstatus, members):
        # lager XML av medlemer
        self.xml.startTag('membership')
        self.xml.startTag('sourcedid')
        self.xml.dataElement('source', self.DataSource)
        self.xml.dataElement('id', gid)
        self.xml.endTag('sourcedid')
        for uname in members:
            self.xml.startTag('member')
            self.xml.startTag('sourcedid')
            self.xml.dataElement('source', self.DataSource)
            self.xml.dataElement('id', uname)
            self.xml.endTag('sourcedid')
            self.xml.dataElement('idtype', '1')	# The following member ids are persons.
            self.xml.startTag('role', {'recstatus': recstatus,
                                       'roletype': Fronter.ROLE_READ})
            self.xml.dataElement('status', '1')
            self.xml.startTag('extension')
            self.xml.emptyTag('memberof', {'type': 1}) # Member of group, not room.
            self.xml.endTag('extension')
            self.xml.endTag('role')
            self.xml.endTag('member')
        self.xml.endTag('membership')

    def groupmembers_to_XML(self, gid, recstatus, members):
        """Export a bunch of group members to XML.

        UiA asked Cerebrum around 2007-12-17, if it would be possible to give
        certain groups special permissions wrt. the student
        group. '...:studieleder' and '...:foreleser' groups should have the
        'rapporttilgang i evaluering' permission wrt the '...:student' group.

        The recommended way of doing this was communicated in an e-mail from
        2007-12-17 by Lars Nesland. Simply put, we introduce an extra
        <MEMBERSHIP> that expresses these permissions.

        @type gid: basestring
        @param gid:
          Group id (a string used to uniquely identify the group).

        @type recstatus: int
        @param recstatus:
          Operation status (add, remove or update). We use FRONTER_UPDATE only.

        @type members: sequence of group names (basestrings)
        @param members:
          Group names to acquire special permission wrt. L{gid}.
        """

        if not members:
            return

        self.xml.startTag('membership')
        self.xml.startTag('sourcedid')
        self.xml.dataElement('source', self.DataSource)
        self.xml.dataElement('id', gid)
        self.xml.endTag('sourcedid')
        for gname in members:
            self.xml.startTag('member')
            self.xml.startTag('sourcedid')
            self.xml.dataElement('source', self.DataSource)
            self.xml.dataElement('id', gname)
            self.xml.endTag('sourcedid')
            # The following member id is a group.
            self.xml.dataElement('idtype', '2')	
            self.xml.startTag('role', {'recstatus': recstatus,
                                       'roletype': Fronter.ROLE_DELETE})
            self.xml.dataElement('status', '1')
            self.xml.startTag('extension')
            # Member of group, not room.
            self.xml.emptyTag('memberof', {'type': 1})
            # 'Rapporttilgang til evaluering' permissions
            self.xml.emptyTag('groupaccess',
                              {'contactAccess': '150'})
            self.xml.endTag('extension')
            self.xml.endTag('role')
            self.xml.endTag('member')
        self.xml.endTag('membership')
    # end groupmembers_to_XML
    
    def acl_to_XML(self, node, recstatus, groups):
        self.xml.startTag('membership')
        self.xml.startTag('sourcedid')
        self.xml.dataElement('source', self.DataSource)
        self.xml.dataElement('id', node)
        self.xml.endTag('sourcedid')
        for gname in groups.keys():
            self.xml.startTag('member')
            self.xml.startTag('sourcedid')
            self.xml.dataElement('source', self.DataSource)
            self.xml.dataElement('id', gname)
            self.xml.endTag('sourcedid')
            self.xml.dataElement('idtype', '2')	# The following member ids are groups.
            acl = groups[gname]
            if acl.has_key('role'):
                self.xml.startTag('role', {'recstatus': recstatus,
                                           'roletype': acl['role']})
                self.xml.dataElement('status', '1')
                self.xml.startTag('extension')
                self.xml.emptyTag('memberof', {'type': 2}) # Member of room.
            else:
                self.xml.startTag('role', {'recstatus': recstatus})
                self.xml.dataElement('status', '1')
                self.xml.startTag('extension')
                self.xml.emptyTag('memberof', {'type': 1}) # Member of group.
                self.xml.emptyTag('groupaccess',
                                  {'contactAccess': acl['gacc'],
                                   'roomAccess': acl['racc']})
            self.xml.endTag('extension')
            self.xml.endTag('role')
            self.xml.endTag('member')
        self.xml.endTag('membership')

    def end(self):
        self.xml.endTag(self.rootEl)
        self.xml.endDocument()
        
