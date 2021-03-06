#!/usr/bin/env python
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

import sys
import getopt

import cerebrum_path
import cereconf

from Cerebrum.extlib import xmlprinter
from Cerebrum.Utils import XMLHelper
from Cerebrum.utils.atomicfile import MinimumSizeWriter
from Cerebrum.utils.atomicfile import AtomicFileWriter
from Cerebrum.Utils import Factory
from Cerebrum.modules.no.access_FS import make_fs

logger = Factory.get_logger("cronjob")
xml = XMLHelper()
fs = None

KiB = 1024
MiB = KiB**2

def _ext_cols(db_rows):
    # TBD: One might consider letting xmlify_dbrow handle this
    cols = None
    if db_rows:
        cols = list(db_rows[0].keys())
    return cols, db_rows


def write_edu_info(outfile):
    """Lag en fil med informasjon om alle studentenes 'aktiviteter' registrert
    i FS.

    Spesifikt, lister vi opp alle deltagelser ved:

      - undenh
      - undakt
      - kullklasser
      - kull
    """

    logger.info("Writing edu info for all students")
    f = MinimumSizeWriter(outfile)
    f.min_size = 0
    f.write(xml.xml_hdr + "<data>\n")

    for xml_tag, generator in (
        ("undenh", fs.undervisning.list_studenter_alle_undenh),
        ("undakt", fs.undervisning.list_studenter_alle_undakt),
        ("kullklasse", fs.undervisning.list_studenter_alle_kullklasser),
        ("kull", fs.undervisning.list_studenter_alle_kull)):
        logger.debug("Processing %s entries", xml_tag)
        for row in generator():
            keys = row.keys()
            f.write(xml.xmlify_dbrow(row, keys, xml_tag) + "\n")

    f.write("</data>\n")
    f.close()
# end write_edu_info



def write_person_info(outfile):
    logger.info("Writing person info to '%s'" % outfile)
    f = MinimumSizeWriter(outfile)
    f.min_size = 0
    f.write(xml.xml_hdr + "<data>\n")

    # Aktive fagpersoner ved Hi�f
    cols, fagperson = _ext_cols(fs.undervisning.list_fagperson_semester())
    for p in fagperson:
        f.write(xml.xmlify_dbrow(p, xml.conv_colnames(cols), 'fagperson') + "\n")
    # Aktive ordin�re studenter ved Hi�f
    cols, student = _ext_cols(fs.student.list_aktiv())
    for a in student:
        f.write(xml.xmlify_dbrow(a, xml.conv_colnames(cols), 'aktiv') + "\n")
    # Eksamensmeldinger
    cols, student = _ext_cols(fs.student.list_eksamensmeldinger())
    for s in student:
        f.write(xml.xmlify_dbrow(s, xml.conv_colnames(cols), 'eksamen') + "\n")

    f.write("</data>\n")
    f.close()



def write_ou_info(outfile):
    """Lager fil med informasjon om alle OU-er"""
    logger.info("Writing ou info to '%s'" % outfile)
    f = MinimumSizeWriter(outfile)
    f.min_size = 0
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

def write_role_info(outfile):
    """Skriv data om alle registrerte roller"""
    logger.info("Writing role info to '%s'" % outfile)
    f = MinimumSizeWriter(outfile)
    f.min_size = 1*KiB
    f.write(xml.xml_hdr + "<data>\n")
    cols, role = _ext_cols(fs.undervisning.list_alle_personroller())
    for r in role:
	f.write(xml.xmlify_dbrow(r, xml.conv_colnames(cols), 'rolle') + "\n")
    f.write("</data>\n")
    f.close()

def write_undenh_metainfo(outfile):
    "Skriv metadata om undervisningsenheter for innev�rende+neste semester."
    logger.info("Writing undenh_meta info to '%s'" % outfile)
    f = MinimumSizeWriter(outfile)
    f.min_size = 1*KiB
    f.write(xml.xml_hdr + "<undervenhet>\n")
    for semester in ('current', 'next'):
        cols, undenh = _ext_cols(fs.undervisning.list_undervisningenheter(sem=semester))
        for u in undenh:
            f.write(xml.xmlify_dbrow(u, xml.conv_colnames(cols), 'undenhet')
                    + "\n")
    f.write("</undervenhet>\n")
    f.close()

def write_studprog_info(outfile):
    """Lager fil med informasjon om alle definerte studieprogrammer"""
    logger.info("Writing studprog info to '%s'" % outfile)
    f = MinimumSizeWriter(outfile)
    f.min_size = 1*KiB
    f.write(xml.xml_hdr + "<data>\n")
    cols, dta = _ext_cols(fs.info.list_studieprogrammer())
    for t in dta:
        f.write(xml.xmlify_dbrow(t, xml.conv_colnames(cols), 'studprog')
                + "\n")
    f.write("</data>\n")
    f.close()

def write_emne_info(outfile):
    """Lager fil med informasjon om alle definerte emner"""
    logger.info("Writing emne info to '%s'" % outfile)
    f=open(outfile, 'w')
    f.write(xml.xml_hdr + "<data>\n")
    cols, dta =_ext_cols(fs.info.list_emner())
    for t in dta:
        f.write(xml.xmlify_dbrow(t, xml.conv_colnames(cols), 'emne') + "\n")
    f.write("</data>\n")


def write_fnrupdate_info(outfile):
    """Lager fil med informasjon om alle f�dselsnummerendringer"""
    logger.info("Writing fnrupdate info to '%s'" % outfile)
    stream = AtomicFileWriter(outfile, 'w')
    writer = xmlprinter.xmlprinter(stream,
                                   indent_level = 2,
                                   # Human-readable output
                                   data_mode = True,
                                   input_encoding = "latin1")
    writer.startDocument(encoding = "iso8859-1")

    db = Factory.get("Database")()
    const = Factory.get("Constants")(db)

    writer.startElement("data", {"source_system" : str(const.system_fs)})

    data = fs.person.list_fnr_endringer()
    for row in data:
        # Make the format resemble the corresponding FS output as close as
        # possible.
        attributes = { "type" : str(const.externalid_fodselsnr), 
                       "new"  : "%06d%05d" % (row["fodselsdato_naverende"],
                                              row["personnr_naverende"]),
                       "old"  : "%06d%05d" % (row["fodselsdato_tidligere"],
                                              row["personnr_tidligere"]),
                       "date" : str(row["dato_foretatt"]),
                     }
        
        writer.emptyElement("external_id", attributes)
    # od

    writer.endElement("data")
    writer.endDocument()
    stream.close()
# end get_fnr_update_info

def write_misc_info(outfile, tag, func_name):
    """Lager fil med data fra gitt funksjon i access_FS"""
    logger.info("Writing misc info to '%s'" % outfile)
    f=open(outfile, 'w')
    f.write(xml.xml_hdr + "<data>\n")
    cols, dta = _ext_cols(eval("fs.%s" % func_name)())
    for t in dta:
        fix_float(t)
        f.write(xml.xmlify_dbrow(t, xml.conv_colnames(cols), tag) + "\n")
    f.write("</data>\n")

def fix_float(row):
    for n in range(len(row)):
        if isinstance(row[n], float):
            row[n] = int(row[n])

def usage(exitcode=0):
    print """Usage: [options]
    --studprog-file name: override studprog xml filename
    --personinfo-file: override person xml filename
    --roleinfo-file: override role xml filename
    --undenh-file: override 'topics' file
    --emneinfo-file: override emne info
    --edu-info-file: edu info file (undenh/undakt/kullklass)
    --fnr-update-file: override fnr_update file
    --misc-func func: name of function in access_FS to call
    --misc-file name: name of output file for misc-func
    --misc-tag tag: tag to use in misc-file
    --ou-file name: override ou xml filename
    --db-user name: connect with given database username
    --db-service name: connect to given database
    -s: generate studprog xml file
    -o: generate ou xml (sted.xml) file
    -p: generate person file
    -r: generate role file
    -f: generate fnr_update file
    -e: generate emne info file
    -u: generate undervisningsenhet xml file
    -i: generate edu info xml file (student at undenh/undakt/kullklasse)
    """
    sys.exit(exitcode)

def assert_connected(user="CEREBRUM", service="FSHIOF.uio.no"):
    global fs
    if fs is None:
        fs = make_fs()

def main():
    logger.info("Starting import from FS")
    try:
        opts, args = getopt.getopt(sys.argv[1:], "fpsruoei",
                                   ["personinfo-file=", "studprog-file=", 
                                    "roleinfo-file=", "undenh-file=",
                                    "emneinfo-file=",
                                    "fnr-update-file=",
                                    "edu-info-file=",
                                    "misc-func=", 
                                    "misc-file=", "misc-tag=",
                                    "ou-file=", "db-user=", "db-service="])
    except getopt.GetoptError:
        raise
        usage()
        sys.exit(2)

    person_file = None
    studprog_file = None
    ou_file = None
    role_file = None
    undervenh_file = None
    emne_info_file = None
    fnr_update_file = None
    edu_info_file = None
    
    db_user = None         # TBD: cereconf value?
    db_service = None      # TBD: cereconf value?
    for o, val in opts:
        if o in ('--emneinfo-file',):
            emne_info_file = val
        elif o in ('--personinfo-file',):
            person_file = val
        elif o in ('--studprog-file',):
            studprog_file = val
        elif o in ('--roleinfo-file',):
            role_file = val
        elif o in ('--undenh-file',):
            undervenh_file = val
        elif o in ('--fnr-update-file',):
            fnr_update_file = val
        elif o in ('--ou-file',):
            ou_file = val
        elif o in ('--edu-info-file',):
            edu_info_file = val
        elif o in ('--db-user',):
            db_user = val
        elif o in ('--db-service',):
            db_service = val
    assert_connected(user=db_user, service=db_service)
    for o, val in opts:
        if o in ('-p',):
            write_person_info(person_file)
        elif o in ('-s',):
            write_studprog_info(studprog_file)
        elif o in ('-r',):
            write_role_info(role_file)
        elif o in ('-u',):
            write_undenh_metainfo(undervenh_file)
        elif o in ('-e',):
            write_emne_info(emne_info_file)
        elif o in ('-f',):
            write_fnrupdate_info(fnr_update_file)
        elif o in ('-o',):
            write_ou_info(ou_file)
        elif o in ('-i',):
            write_edu_info(edu_info_file)
        # We want misc-* to be able to produce multiple file in one script-run
        elif o in ('--misc-func',):
            misc_func = val
        elif o in ('--misc-tag',):
            misc_tag = val
        elif o in ('--misc-file',):
            write_misc_info(val, misc_tag, misc_func)

    logger.info("Import from FS done")

if __name__ == '__main__':
    main()
