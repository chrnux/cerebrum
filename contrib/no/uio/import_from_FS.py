#!/usr/bin/env python2.2
# -*- coding: iso-8859-1 -*-

# Copyright 2002, 2003 University of Oslo, Norway
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

import cerebrum_path

import re
import os
import sys
import getopt
import cereconf

from Cerebrum import Database
from Cerebrum import Errors
from Cerebrum.Utils import XMLHelper
from Cerebrum.modules.no.uio.access_FS import FS

default_person_file = "/cerebrum/dumps/FS/persons.xml"
default_emne_file = "/cerebrum/dumps/FS/emner.xml"
default_topics_file = "/cerebrum/dumps/FS/topics.xml"
default_studieprogram_file = "/cerebrum/dumps/FS/studieprogrammer.xml"
default_regkort_file = "/cerebrum/dumps/FS/regkort.xml"
default_ou_file = "/cerebrum/dumps/FS/ou.xml"
default_fnrupdate_file = "/cerebrum/dumps/FS/fnr_udpate.xml"

xml = XMLHelper()
fs = None

def write_person_info(outfile):
    """Lager fil med informasjon om alle personer registrert i FS som
    vi muligens ogs� �nsker � ha med i Cerebrum.  En person kan
    forekomme flere ganger i filen."""

    # TBD: Burde vi cache alle data, slik at vi i stedet kan lage en
    # fil der all informasjon om en person er samlet under en egen
    # <person> tag?
    
    f=open(outfile, 'w')
    f.write(xml.xml_hdr + "<data>\n")
    # Fagpersoner
    cols, fagpersoner = fs.GetKursFagpersonundsemester()
    for p in fagpersoner:
        f.write(xml.xmlify_dbrow(p, xml.conv_colnames(cols), 'fagperson') + "\n")

    # Studenter med opptak, privatister (=opptak i studiepgraommet
    # privatist) og Alumni
    cols, students = fs.GetStudinfOpptak()
    for s in students:
	# The Oracle driver thinks the result of a union of ints is float
        fix_float(s)
        f.write(xml.xmlify_dbrow(s, xml.conv_colnames(cols), 'opptak') + "\n")
    # Studenter med alumni opptak til et studieprogram
    cols, students = fs.GetAlumni()
    for s in students:
        f.write(xml.xmlify_dbrow(s, xml.conv_colnames(cols), 'alumni') + "\n")

    # Studenter med privatist opptak til et studieprogram
    cols, students = fs.GetPrivatistStudieprogram()
    for s in students:
        fix_float(s)
        f.write(xml.xmlify_dbrow(s, xml.conv_colnames(cols), 'privatist_studieprogram') + "\n")

    # Aktive studenter
    cols, students = fs.GetStudinfAktiv()
    for s in students:
        # The Oracle driver thinks the result of a union of ints is float
        fix_float(s)
        f.write(xml.xmlify_dbrow(s, xml.conv_colnames(cols), 'aktiv') + "\n")

    # Privatister (=eksamensmeldt i emne de ikke har opptak til)
    cols, students = fs.GetStudinfPrivatist()
    for s in students:
        f.write(xml.xmlify_dbrow(s, xml.conv_colnames(cols), 'privatist_emne') + "\n")

    # Semester-registrering
    cols, students = fs.GetStudinfRegkort()
    for s in students:
        f.write(xml.xmlify_dbrow(s, xml.conv_colnames(cols), 'regkort') + "\n")

    # Eksamensmeldinger
    cols, students = fs.GetAlleEksamener()
    for s in students:
        f.write(xml.xmlify_dbrow(s, xml.conv_colnames(cols), 'eksamen') + "\n")

    # EVU students
    # En del EVU studenter vil v�re gitt av s�ket over

    cols, evustud = fs.GetStudinfEvu()
    for e in evustud:
        f.write(xml.xmlify_dbrow(e, xml.conv_colnames(cols), 'evu') + "\n")

    # Studenter i permisjon (ogs� dekket av GetStudinfOpptak)
    cols, permstud = fs.GetStudinfPermisjon()
    for p in permstud:
        f.write(xml.xmlify_dbrow(p, xml.conv_colnames(cols), 'permisjon') + "\n")

    # Personer som har f�tt tilbud
    cols, tilbudstud = fs.GetStudinfTilbud()
    for t in tilbudstud:
        f.write(xml.xmlify_dbrow(t, xml.conv_colnames(cols), 'tilbud') + "\n")
    
    f.write("</data>\n")

def write_ou_info(outfile):
    """Lager fil med informasjon om alle OU-er"""
    f=open(outfile, 'w')
    f.write(xml.xml_hdr + "<data>\n")
    cols, ouer = fs.GetAlleOUer(cereconf.DEFAULT_INSTITUSJONSNR)  # TODO
    for o in ouer:
        sted = {}
        for fs_col, xml_attr in (
            ('faknr', 'fakultetnr'),
            ('instituttnr', 'instituttnr'),
            ('gruppenr', 'gruppenr'),
            ('stedakronym', 'akronym'),
            ('stedakronym', 'forkstednavn'),
            ('stednavn_bokmal', 'stednavn'),
            ('faknr_org_under', 'fakultetnr_for_org_sted'),
            ('instituttnr_org_under', 'instituttnr_for_org_sted'),
            ('gruppenr_org_under', 'gruppenr_for_org_sted'),
            ('adrlin1', 'adresselinje1_intern_adr'),
            ('adrlin2', 'adresselinje2_intern_adr'),
            ('postnr', 'poststednr_intern_adr'),
            ('adrlin1_besok', 'adresselinje1_besok_adr'),
            ('adrlin2_besok', 'adresselinje2_besok_adr'),
            ('postnr_besok', 'poststednr_besok_adr')):
            if o[fs_col] is not None:
                sted[xml_attr] = xml.escape_xml_attr(o[fs_col])
        komm = []
        for fs_col, typekode in (
            ('telefonnr', 'EKSTRA TLF'),
            ('faxnr', 'FAX')):
            if o[fs_col]:               # Skip NULLs and empty strings
                komm.append({'kommtypekode': xml.escape_xml_attr(typekode),
                             'kommnrverdi': xml.escape_xml_attr(o[fs_col])})
        # TODO: Kolonnene 'url' og 'bibsysbeststedkode' hentes ut fra
        # FS, men tas ikke med i outputen herfra.
        f.write('<sted ' +
                ' '.join(["%s=%s" % item for item in sted.items()]) +
                '>\n')
        for k in komm:
            f.write('<komm ' +
                    ' '.join(["%s=%s" % item for item in k.items()]) +
                    ' />\n')
        f.write('</sted>\n')
    f.write("</data>\n")

def write_topic_info(outfile):
    """Lager fil med informasjon om alle XXX"""
    # TODO: Denne filen blir endret med det nye opplegget :-(
    f=open(outfile, 'w')
    f.write(xml.xml_hdr + "<data>\n")
    cols, topics = fs.GetAlleEksamener()
    for t in topics:
        # The Oracle driver thinks the result of a union of ints is float
        fix_float(t)
        f.write(xml.xmlify_dbrow(t, xml.conv_colnames(cols), 'topic') + "\n")
    f.write("</data>\n")

def write_regkort_info(outfile):
    """Lager fil med informasjon om semesterregistreringer for
    innev�rende semester"""
    f=open(outfile, 'w')
    f.write(xml.xml_hdr + "<data>\n")
    cols, regkort = fs.GetStudinfRegkort()
    for r in regkort:
        f.write(xml.xmlify_dbrow(r, xml.conv_colnames(cols), 'regkort') + "\n")
    f.write("</data>\n")

def write_studprog_info(outfile):
    """Lager fil med informasjon om alle definerte studieprogrammer"""
    f=open(outfile, 'w')
    f.write(xml.xml_hdr + "<data>\n")
    cols, dta = fs.GetStudieproginf()
    for t in dta:
        f.write(xml.xmlify_dbrow(t, xml.conv_colnames(cols), 'studprog') + "\n")
    f.write("</data>\n")

def write_emne_info(outfile):
    """Lager fil med informasjon om alle definerte emner"""
    f=open(outfile, 'w')
    f.write(xml.xml_hdr + "<data>\n")
    cols, dta = fs.GetEmneinf()
    for t in dta:
        f.write(xml.xmlify_dbrow(t, xml.conv_colnames(cols), 'emne') + "\n")
    f.write("</data>\n")

def write_fnrupdate_info(outfile):
    """Lager fil med informasjon om alle f�dselsnummerendringer"""
    f=open(outfile, 'w')
    f.write(xml.xml_hdr + "<data>\n")
    cols, dta = fs.GetFnrEndringer()
    for t in dta:
        f.write(xml.xmlify_dbrow(t, xml.conv_colnames(cols), 'fnr') + "\n")
    f.write("</data>\n")

def fix_float(row):
    for n in range(len(row)):
        if isinstance(row[n], float):
            row[n] = int(row[n])

def usage(exitcode=0):
    print """Usage: [options]
    --person-file name: override person xml filename
    --topics-file name: override topics xml filename
    --studprog-file name: override studprog xml filename
    --emne-file name: override emne xml filename
    --regkort-file name: override regkort xml filename
    --fnr-update-file name: override fnr-update xml filename
    --ou-file name: override ou xml filename
    --db-user name: connect with given database username
    --db-service name: connect to given database
    -p: generate person xml file
    -t: generate topics xml file
    -e: generate emne xml file
    -f: generate fnr xml update file
    -s: generate studprog xml file
    -r: generate regkort xml file
    -o: generate ou xml file
    """
    sys.exit(exitcode)

def assert_connected(user="ureg2000", service="FSPROD.uio.no"):
    global fs
    if fs is None:
        db = Database.connect(user=user, service=service,
                              DB_driver='Oracle')
        fs = FS(db)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ptsroef",
                                   ["person-file=", "topics-file=",
                                    "studprog-file=", "regkort-file=",
                                    'emne-file=', "ou-file=", "db-user=",
                                    'fnr-update-file=',
                                    "db-service="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    person_file = default_person_file
    topics_file = default_topics_file
    studprog_file = default_studieprogram_file
    regkort_file = default_regkort_file
    emne_file = default_emne_file
    ou_file = default_ou_file
    fnrupdate_file = default_fnrupdate_file
    db_user = None         # TBD: cereconf value?
    db_service = None      # TBD: cereconf value?
    for o, val in opts:
        if o in ('--person-file',):
            person_file = val
        elif o in ('--topics-file',):
            topics_file = val
        elif o in ('--emne-file',):
            emne_file = val
        elif o in ('--studprog-file',):
            studprog_file = val
        elif o in ('--regkort-file',):
            regkort_file = val
        elif o in ('--ou-file',):
            ou_file = val
        elif o in ('--fnr-update-file',):
            fnrupdate_file = val
        elif o in ('--db-user',):
            db_user = val
        elif o in ('--db-service',):
            db_service = val
    assert_connected(user=db_user, service=db_service)
    for o, val in opts:
        if o in ('-p',):
            write_person_info(person_file)
        elif o in ('-t',):
            write_topic_info(topics_file)
        elif o in ('-s',):
            write_studprog_info(studprog_file)
        elif o in ('-f',):
            write_fnrupdate_info(fnrupdate_file)
        elif o in ('-e',):
            write_emne_info(emne_file)
        elif o in ('-r',):
            write_regkort_info(regkort_file)
        elif o in ('-o',):
            write_ou_info(ou_file)

if __name__ == '__main__':
    main()
