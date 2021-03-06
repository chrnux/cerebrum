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

"""This module contains utilities for ClassFronter XML generation.

NB! This module is used by other institutions as well. Be careful with
shuffling the functionality around.
"""

import re
import time

from Cerebrum import Errors
from Cerebrum.Utils import Factory
from Cerebrum.modules.no.uio.access_FS import FS
from Cerebrum import Database
from Cerebrum.extlib import xmlprinter
from Cerebrum.utils.atomicfile import AtomicFileWriter



def get_member_names(group_name):
    db = Factory.get("Database")()
    group = Factory.get("Group")(db)
    usernames = ()
    try:
        group.find_by_name(group_name)
    except Errors.NotFoundError:
        pass
    else:
        account = Factory.get("Account")(db)
        const = Factory.get("Constants")()
        usernames = list()
        for row in group.search_members(group_id=group.entity_id,
                                        indirect_members=True,
                                        member_type=const.entity_account):
            account.clear()
            account.find(row["member_id"])
            usernames.append(account.account_name)

    return usernames
# end get_member_names



host_config = {
    'internkurs.uio.no': { 'DBinst': 'DLOUIO.uio.no',
                           'admins':
                           get_member_names('classfronter-internkurs-drift'),
                           'export': ['All_users'],
                           },
    'tavle.uio.no': {'DBinst': 'DLOOPEN.uio.no',
                     'admins': get_member_names('classfronter-tavle-drift'),
                     'export': ['All_users'],
                     },
    'kladdebok.uio.no': { 'DBinst': 'DLOUTV.uio.no',
                          'admins':
                          get_member_names('classfronter-kladdebok-drift'),
                          'export': ['FS'],
                          'plain_users': get_member_names('classfronter-kladdebok-plain'),
                          'spread': 'spread_fronter_kladdebok',
                          },
    'petra.uio.no': { 'DBinst': 'DLODEMO.uio.no',
                      'admins': get_member_names('classfronter-petra-drift'),
                      'export': ['FS', 'All_users'],
                      'spread': 'spread_fronter_petra',
                      },
    'blyant.uio.no': { 'DBinst': 'DLOPROD.uio.no',
                       'admins': get_member_names('classfronter-blyant-drift'),
                       'export': ['FS', 'All_users'],
                       'spread': 'spread_fronter_blyant',
                       },
    'fronter.com': { 'DBinst': 'DLOPROD.uio.no',
                       'admins': get_member_names('classfronter-fronterdotcom-drift'),
                       'export': ['FS', 'All_users'],
                       'spread': 'spread_fronter_dotcom',
                       }
    }



def UE2KursID(kurstype, *rest):
    """Lag ureg2000-spesifikk 'kurs-ID' av prim�rn�kkelen til en
    undervisningsenhet, et EVU-kurs eller et kull.  Denne kurs-IDen forblir
    uforandret s� lenge kurset p�g�r; den endres alts� ikke n�r man
    f.eks. kommer til et nytt semester.

    F�rste argument angir hvilken type FS-entitet de resterende argumentene
    stammer fra; enten 'KURS' (for undervisningsenhet), 'EVU' (for EVU-kurs),
    eller 'KULL' (for kull).
    """

    kurstype = kurstype.lower()
    if kurstype == 'evu':
        if len(rest) != 2:
            raise ValueError, \
                  "ERROR: EVU-kurs skal identifiseres av 2 felter, " + \
                  "ikke <%s>" % ">, <".join(rest)
        # EVU-kurs er greie; de identifiseres unikt ved to
        # fritekstfelter; kurskode og tidsangivelse, og er modellert i
        # FS uavhengig av semester-inndeling.
        rest = list(rest)
        rest.insert(0, kurstype)
        return fields2key(*rest)

    elif kurstype == 'kull':
        if len(rest) != 3:
            raise ValueError, ("ERROR: Kull skal alltid identifiseres av 3 "
                               "felter, ikke <%s>" % ">, <".join(rest))
        rest = list(rest)
        rest.insert(0, kurstype)
        return fields2key(*rest)
    
    elif kurstype != 'kurs':
        raise ValueError, "ERROR: Ukjent kurstype <%s> (%s)" % (kurstype, rest)

    # Vi vet her at $kurstype er 'KURS', og vet dermed ogs� hvilke
    # elementer som er med i *rest:
    if len(rest) != 6:
        raise ValueError, \
              "ERROR: Undervisningsenheter skal identifiseres av 6 " + \
              "felter, ikke <%s>" % ">, <".join(rest)

    instnr, emnekode, versjon, termk, aar, termnr = rest
    termnr = int(termnr)
    aar = int(aar)
    tmp_termk = re.sub('[^a-zA-Z0-9]', '_', termk).lower()
    # Finn $termk og $aar for ($termnr - 1) semestere siden:
    if (tmp_termk == 'h_st'):
        if (termnr % 2) == 1:
            termk = 'h�st'
        else:
            termk = 'v�r'
        aar -= int((termnr - 1) / 2)
    elif tmp_termk == 'v_r':
        if (termnr % 2) == 1:
            termk = 'v�r'
        else:
            termk = 'h�st'
        aar -= int(termnr / 2)
    else:
        # Vi krysser fingrene og h�per at det aldri vil benyttes andre
        # verdier for $termk enn 'v�r' og 'h�st', da det i s� fall vil
        # bli vanskelig � vite hvilket semester det var "for 2
        # semestere siden".
        raise ValueError, \
              "ERROR: Unknown terminkode <%s> for emnekode <%s>." % (
            termk, emnekode)

    # $termnr er ikke del av den returnerte strengen.  Vi har benyttet
    # $termnr for � beregne $termk og $aar ved $termnr == 1; det er
    # alts� implisitt i kurs-IDen at $termnr er lik 1 (og dermed
    # un�dvendig � ta med).
    return fields2key(kurstype, instnr, emnekode, versjon, termk, aar)
# end UE2KursID


def fields2key(*fields):
    """Create a key for internal fronter usage.

    We have a number of entities that have to be identified. They all have
    logical 'fields' comprising their IDs. Fields are separated by ':' and are
    all lowercase. This function enforces this restriction.

    @param fields:
      An unspecified number of elements that are joined to make a key. ':' is
      the separator. __str__ is called on each key before joining. The result
      is always lowercased.
    @param fields: tuple
    """

    return (":".join([str(x) for x in fields])).lower()
# end make_key


def str2key(s):
    """L{fields2key}'s counterpart for strings.

    @param s:
      String containing the key
    @type s: basestring
    """

    return s.lower()
# end str2key


def key2fields(key):
    """The opposite operation of L{fields2key}.

    The result is lowercased.

    @param key:
      Key (constructed by L{fields2key} or L{str2key}) to convert to
      fields. ':' is the separator. The resulting fields are lowercased.
    @type key: basestring
    """
    return key.lower().split(":")


class XMLWriter(object):   # TODO: Move to separate file
    # TODO: should produce indented XML for easier readability

    def __init__(self, fname):
        self.__file = AtomicFileWriter(fname, 'w')
        self.gen = xmlprinter.xmlprinter(
            self.__file, indent_level=2, data_mode=1,
            input_encoding='ISO-8859-1')

    def startTag(self, tag, attrs={}):
        a = {}
        # saxutils don't like integers as values (convert to str)
        for k, v in attrs.iteritems():
            a[k] = str(attrs[k])
        self.gen.startElement(tag, a)

    def endTag(self, tag):
        self.gen.endElement(tag)

    def emptyTag(self, tag, attrs={}):
        a = {}
        # saxutils don't like integers as values (convert to str)
        for k, v in attrs.iteritems():
            a[k] = str(v)
        self.gen.emptyElement(tag, a)

    def dataElement(self, tag, data, attrs={}):
        a = {}
        for k, v in attrs.iteritems():
            a[k] = str(v)
        self.gen.dataElement(tag, data, a)

    def comment(self, data):  # TODO: implement
        self.gen.comment(data)

    def startDocument(self, encoding):
        self.gen.startDocument(encoding)

    def endDocument(self):
        self.gen.endDocument()
        self.__file.close()


def semester_number(start_year, start_semester,
                    current_year, current_semester):
    """Return the semester number given a specific start point.

    For entities spanning multiple semester we need to know the semester
    number of (current_year, current_semester) relative to the starting
    point. 
    """
    cs = current_semester.lower()
    ss = start_semester.lower()
    years = int(current_year) - int(start_year)
    correction = 0
    if cs == 'h�st' and ss == 'v�r':
        correction = 1
    elif cs == 'v�r' and ss == 'h�st':
        correction = -1
    return years*2 + correction+1
# end semester_number
