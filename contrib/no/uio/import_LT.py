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
from Cerebrum import Errors
from Cerebrum import Person
from Cerebrum.Utils import Factory
from Cerebrum.modules.no import fodselsnr
from Cerebrum.modules.no.uio import AutoStud

import xml.sax

class LTDataParser(xml.sax.ContentHandler):
    """This class is used to iterate over all users in LT. """

    def __init__(self, filename, call_back_function):
        self.call_back_function = call_back_function        
        xml.sax.parse(filename, self)

    def startElement(self, name, attrs):
        if name == 'data':
            pass
        elif name in ("arbtlf", "komm", "tils", "bilag", "gjest", "rolle"):
            tmp = {}
            for k in attrs.keys():
                tmp[k] = attrs[k].encode('iso8859-1')
            self.p_data[name] = self.p_data.get(name, []) + [tmp]
        elif name == "person":
            self.p_data = {}
            for k in attrs.keys():
                self.p_data[k] = attrs[k].encode('iso8859-1')
        else:
            print "WARNING: unknown element: %s" % name

    def endElement(self, name):
        if name == "person":
            self.call_back_function(self.p_data)

def conv_name(fullname):
    fullname = fullname.strip()
    return fullname.split(None, 1)

ou_cache = {}
def get_sted(stedkode, kinstitusjon=None):
    if not ou_cache.has_key(stedkode):
        ou = Factory.get('OU')(db)
        try:
            fak, inst, gruppe = stedkode[0:2], stedkode[2:4], stedkode[4:6]
            ou.find_stedkode(int(fak), int(inst), int(gruppe))
            addr = ou.get_entity_address(source=const.system_lt,
                                         type=const.address_street)
            if len(addr) > 0:
                addr = addr[0]
                addr = {'address_text': addr['address_text'],
                        'p_o_box': addr['p_o_box'],
                        'postal_number': addr['postal_number'],
                        'city': addr['city'],
                        'country': addr['country']}
            else:
                addr = None
            fax = ou.get_contact_info(source=const.system_lt,
                                      type=const.contact_fax)
            if len(fax) > 0:
                fax = fax[0]['contact_value']
            else:
                fax = None
            ou_cache[stedkode] = {'id': int(ou.ou_id),
                                  'fax': fax,
                                  'addr': addr}
            ou_cache[int(ou.ou_id)] = ou_cache[stedkode]
        except Errors.NotFoundError:
            logger.warn("bad stedkode: %s" % stedkode)
            ou_cache[stedkode] = None
    return ou_cache[stedkode]

def determine_affiliations(person):
    "Determine affiliations in order of significance"
    ret = []
    for t in person.get('tils', ()):
        stedkode =  "%02d%02d%02d" % (int(t['fakultetnr_utgift']),
                                      int(t['instituttnr_utgift']),
                                      int(t['gruppenr_utgift']))
        if t['hovedkat'] == '�VR':
            aff_stat = const.affiliation_status_ansatt_tekadm
        elif t['hovedkat'] == 'VIT':
            aff_stat = const.affiliation_status_ansatt_vit
        else:
            logger.warn("Uknown hovedkat: %s" % t['hovedkat'])
            continue
        sted = get_sted(stedkode)
        if sted is None:
            continue
        ret.append((sted['id'],
                    const.affiliation_ansatt, aff_stat))
    for b in person.get('bilag', ()):
        sted = get_sted(b['stedkode'])
        if sted is None:
            continue
        ret.append((sted['id'], const.affiliation_ansatt,
                    const.affiliation_status_ansatt_bil))
    for g in person.get('gjest', ()):
        if g['gjestetypekode'] == 'EMERITUS':
            aff_stat = const.affiliation_tilknyttet_emeritus
        else:
            logger.warn("Uknown gjestetypekode: %s" % g['gjestetypekode'])
            continue
        sted = get_sted(g['sko'])
        if sted is None:
            continue
        ret.append((sted['id'],
                    const.affiliation_tilknyttet, aff_stat))
    return ret

def determine_contact(person):
    # TODO: we have no documentation on how data are registered in
    # these LT tables, so this is guesswork...
    ret = []
    for t in person.get('arbtlf', ()):
        if int(t['telefonnr']):
            ret.append((const.contact_phone, t['telefonnr']))
        if int(t['linjenr']):
            ret.append((const.contact_phone,
                        "%i%i" % (int(t['innvalgnr']), int(t['linjenr']))))
    for k in person.get('komm', ()):
        if k['kommtypekode'] in ('EKSTRA TLF', 'JOBBTLFUTL'):
            if k.has_key('telefonnr'):
                val = int(k['telefonnr'])
            elif k.has_key('kommnrverdi'):
                val = k['kommnrverdi']
            else:
                continue
            ret.append((const.contact_phone, val))
        if k['kommtypekode'] in ('FAX', 'FAXUTLAND'):
            if k.has_key('telefonnr'):
                val = int(k['telefonnr'])
            elif k.has_key('kommnrverdi'):
                val = k['kommnrverdi']
            else:
                continue
            ret.append((const.contact_fax, val))
    return ret

def process_person(person):
    fnr = fodselsnr.personnr_ok(
        "%02d%02d%02d%05d" % (int(person['fodtdag']), int(person['fodtmnd']),
                              int(person['fodtar']), int(person['personnr'])))
    logger.info2("Process %s " % fnr, append_newline=0)
    new_person.clear()
    gender = const.gender_male
    if(fodselsnr.er_kvinne(fnr)):
        gender = const.gender_female

    (year, mon, day) = fodselsnr.fodt_dato(fnr)
    try:
        new_person.find_by_external_id(const.externalid_fodselsnr, fnr)
    except Errors.NotFoundError:
        pass
    except Errors.TooManyRowsError:
        try:
            new_person.find_by_external_id(
                const.externalid_fodselsnr, fnr, const.system_lt)
        except Errors.NotFoundError:
            pass

    new_person.populate(db.Date(year, mon, day), gender)

    new_person.affect_names(const.system_lt, const.name_first, const.name_last)
    new_person.affect_external_id(const.system_lt, const.externalid_fodselsnr)
    new_person.populate_name(const.name_first, person['fornavn'])
    new_person.populate_name(const.name_last, person['etternavn'])

    new_person.populate_external_id(
        const.system_lt, const.externalid_fodselsnr, fnr)

    # TODO: We currently do nothing with PROSENT_TILSETTING
    affiliations = determine_affiliations(person)
    contact = determine_contact(person)
    if len(affiliations) > 0:      # Legg til fax fra 1ste affiliation
        contact.append((const.contact_fax,
                        get_sted(affiliations[0][0])['fax']))

    if person.has_key('fakultetnr_for_lonnsslip'):
        sko = "%02i%02i%02i" % tuple([int(
            person["%s_for_lonnsslip" % x]) for x in (
            'fakultetnr', 'instituttnr', 'gruppenr')])
        sted = get_sted(sko)
        if sted is not None and sted['addr'] is not None:
            new_person.populate_address(
                const.system_lt, type=const.address_street,
                **sted['addr'])

    op = new_person.write_db()
    if op is None:
        logger.info2("**** EQUAL ****")
    elif op == True:
        logger.info2("**** NEW ****")
    elif op == False:
        logger.info2("**** UPDATE ****")
    db.commit()

def usage(exitcode=0):
    print """Usage: import_LT.py -p personfile [-v]"""
    sys.exit(exitcode)

def main():
    global db, new_person, const, ou, logger
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vp:', ['verbose', 'person-file'])
    except getopt.GetoptError:
        usage(1)

    verbose = 0
    personfile = None
    
    for opt, val in opts:
        if opt in ('-v', '--verbose'):
            verbose += 1
        elif opt in ('-p', '--person-file'):
            personfile = val
    if personfile is None:
        usage(1)

    logger = AutoStud.Util.ProgressReporter("./lti-run.log.%i" % os.getpid(),
                                            stdout=verbose)
    db = Factory.get('Database')()
    db.cl_init(change_program='import_LT')
    const = Factory.get('Constants')(db)

    ou = Factory.get('OU')(db)
    new_person = Person.Person(db)
    LTDataParser(personfile, process_person)

if __name__ == '__main__':
    main()
