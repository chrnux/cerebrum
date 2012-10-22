#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# Copyright 2009, 2012 University of Oslo, Norway
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
import sys
import getopt
from os.path import join as pj

import cerebrum_path
import cereconf
from Cerebrum import Database
from Cerebrum import Errors
from Cerebrum.extlib import xmlprinter
from Cerebrum.Utils import XMLHelper, MinimumSizeWriter, AtomicFileWriter
from Cerebrum.modules.no.hine.access_FS import FS
from Cerebrum.Utils import Factory

basefsdir = pj("/cerebrum", "hine", "dumps", "FS")
default_ou_file = pj(basefsdir, "ou.xml")
default_person_file = pj(basefsdir, "person.xml")
default_studieprogram_file = pj(basefsdir, "studieprog.xml")

xml = XMLHelper()
fs = None

def _ext_cols(db_rows):
    # TBD: One might consider letting xmlify_dbrow handle this
    cols = None
    if db_rows:
        cols = list(db_rows[0].keys())
    return cols, db_rows

def write_ou_info(outfile):
    """Lager fil med informasjon om alle OU-er"""
    f = MinimumSizeWriter(outfile)
    f.set_minimum_size_limit(0)
    f.write(xml.xml_hdr + "<data>\n")
    cols, ouer = _ext_cols(fs.info.list_ou(cereconf.DEFAULT_INSTITUSJONSNR)) 
    for o in ouer:
        sted = {}
        for fs_col, xml_attr in (
            ('faknr', 'fakultetnr'),
            ('instituttnr', 'instituttnr'),
            ('gruppenr', 'gruppenr'),
            ('stedakronym', 'akronym'),
            ('stedakronym', 'forkstednavn'),
            ('stednavn_bokmal', 'stednavn'),
            ('stedkode_konv', 'stedkode_konv'),
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
            ('faxnr', 'FAX'),
            ('emailadresse','EMAIL'),
            ('url', 'URL')):
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
    f.close()

def write_person_info(outfile):
    f = MinimumSizeWriter(outfile)
    f.set_minimum_size_limit(0)
    f.write(xml.xml_hdr + "<data>\n")

#    # Aktive fagpersoner ved HIH
#    cols, fagperson = _ext_cols(fs.undervisning.list_fagperson_semester())
#    for p in fagperson:
#        f.write(xml.xmlify_dbrow(p, xml.conv_colnames(cols), 'fagperson') + "\n")
    # Aktive ordinære studenter ved HIH
    cols, student = _ext_cols(fs.student.list_aktiv())
    for a in student:
        f.write(xml.xmlify_dbrow(a, xml.conv_colnames(cols), 'aktiv') + "\n")
#    # Eksamensmeldinger
#    cols, student = _ext_cols(fs.student.list_eksamensmeldinger())
#    for s in student:
#        f.write(xml.xmlify_dbrow(s, xml.conv_colnames(cols), 'eksamen') + "\n")
     # EVU-studenter ved HIH
     # For now, HiH does not want to import information about EVU students
     # cols, student = _ext_cols(fs.evu.list())
     # for e in student:
     #     f.write(xml.xmlify_dbrow(e, xml.conv_colnames(cols), 'evu') + "\n")

    f.write("</data>\n")
    f.close()

def write_studprog_info(outfile):
    """Lager fil med informasjon om alle definerte studieprogrammer"""
    f = MinimumSizeWriter(outfile)
    f.set_minimum_size_limit(10*KiB)
    f.write(xml.xml_hdr + "<data>\n")
    cols, dta = _ext_cols(fs.info.list_studieprogrammer())
    for t in dta:
        f.write(xml.xmlify_dbrow(t, xml.conv_colnames(cols), 'studprog')
                + "\n")
    f.write("</data>\n")
    f.close()

def usage(exitcode=0):
    print """Usage: [options]
    --ou-file name: override ou xml filename
    --personinfo-file: override person xml filename
    --studprog-file name: override studprog xml filename
    
    -o: generate ou xml (sted.xml) file
    -p: generate person file
    -s: generate studprog xml file
    """
    sys.exit(exitcode)


def assert_connected():
    global fs
    if fs is None:
        fs = Factory.get('FS')()


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ops",
                   ["ou-file=", "personinfo-file=", "studprog-file="])
    except getopt.GetoptError, ge:
        print ge
        usage()
        sys.exit(2)

    ou_file = default_ou_file
    person_file = default_person_file
    studieprogram_file = default_studieprogram_file
    for o, val in opts:
        if o in ('--ou-file',):
            ou_file = val
        elif o in ('--personinfo-file',):
            person_file = val
        elif o in ('--studprog-file',):
            studprog_file = val

    assert_connected()
    for o, val in opts:
        if o in ('-o',):
            write_ou_info(ou_file)
        elif o in ('-p',):
            write_person_info(person_file)
        elif o in ('-s',):
            write_studprog_info(studprog_file)

 
if __name__ == '__main__':
    main()
