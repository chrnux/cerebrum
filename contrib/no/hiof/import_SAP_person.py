#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Copyright 2004 University of Oslo, Norway
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


"""

This file is a HiOf-specific extension of Cerebrum. It contains code which
imports person SAP-specific information into Cerebrum.

Import file format.  The files are semicolon (;) separated, counting
from 0 to 36.

 Field  Description
    0   SAP person ID
    3   Name initials
    4   SSN / norwegian f�dselsnr
    5   Birth date
    6   First name
    7   Middle name
    8   Last name
   12   Contact phone private
   13   Contact phone
   14   Contact phone cellular
   15   Contact phone cellular - private
   18   Bostedsadr. C/O
   19   Bostedsadr. Gate
   20   Bostedsadr. husnr.
   21   Bostedsadr. Tillegg
   22   Bostedsadr. Poststed
   23   Bostedsadr. postnr.
   24   Bostedsadr. Land
   25   Forretningsomr�de ID
   28   Work title

FIXME: I wonder if the ID lookup/population logic might fail in a subtle
way, should an update process (touching IDs) run concurrently with this
import.
"""


### TODO
##
## 1. SAPForretningsOmradeKode
##





import cerebrum_path
import cereconf

from Cerebrum import Errors
from Cerebrum.Utils import Factory
# from Cerebrum.modules.no.hia.mod_sap_codes import SAPForretningsOmradeKode
from Cerebrum.modules.no import fodselsnr

import sys
import getopt
import string

FIELDS_IN_ROW = 37



def sap_row_to_tuple(sap_row):
    return string.split(sap_row.strip(), ";")


def locate_person(person, sap_id, no_ssn, const):
    """
    Locate a person who owns both SAP_ID and NO_SSN.

    NB! A situation where both IDs are set, but point to people with
    different person_id's is considered an error.
    """

    logger.debug("Locating person with SAP_id = �%s� and NO_SSN = �%s�",
                 sap_id, no_ssn)

    person_id_from_sap = None
    person_id_from_no_ssn = None

    try:
        person.clear()
        person.find_by_external_id(const.externalid_sap_ansattnr,
                                   sap_id, const.system_sap)
        person_id_from_sap = int(person.entity_id)
    except Errors.NotFoundError:
        logger.debug("No person matches SAP id �%s�", sap_id)

    try:
        person.clear()
        person.find_by_external_id(const.externalid_fodselsnr,
                                   no_ssn)
        person_id_from_no_ssn = int(person.entity_id)
    except Errors.NotFoundError:
        logger.debug("No person matches NO_SSN �%s�", no_ssn)

    # Now, we can compare person_id_from_*. If they are both set, they must
    # point to the same person (otherwise, we'd have two IDs in the *same
    # SAP entry* pointing to two different people in Cerebrum). However, we
    # should also allow the possibility of only one ID being set.
    assert (person_id_from_sap is None or
            person_id_from_no_ssn is None or
            person_id_from_sap == person_id_from_no_ssn), \
           ("Aiee! IDs for logically the same person differ: "
            "(SAP id => person_id %s; NO_SSN => person_id %s)" %
            (person_id_from_sap, person_id_from_no_ssn))

    already_exists = (person_id_from_sap is not None or
                      person_id_from_no_ssn is not None)

    # Make sure, that person is associated with the corresponding db rows
    if already_exists:
        person.clear()
        p_id = person_id_from_sap
        if p_id is None: p_id = person_id_from_no_ssn
        person.find(p_id)

    return already_exists



def match_external_ids(person, sap_id, no_ssn, const):
    """
    Make sure that PERSON's external IDs in Cerebrum match SAP_ID and NO_SSN.
    """

    cerebrum_sap_id = person.get_external_id(const.system_sap,
                                             const.externalid_sap_ansattnr)
    cerebrum_no_ssn = person.get_external_id(const.system_sap,
                                             const.externalid_fodselsnr)

    # There is at most one such ID, get_external_id returns a sequence, though
    if cerebrum_sap_id:
        cerebrum_sap_id = str(cerebrum_sap_id[0]["external_id"])
    if cerebrum_no_ssn:
        cerebrum_no_ssn = str(cerebrum_no_ssn[0]["external_id"])

    if (cerebrum_sap_id and cerebrum_sap_id != sap_id):
        logger.error("SAP id in Cerebrum != SAP id in datafile "
                     "�%s� != �%s�", cerebrum_sap_id, sap_id)
        return False

    #
    # A mismatch in SSN means that Cerebrum's data has to be updated.
    # 
    if (cerebrum_no_ssn and cerebrum_no_ssn != no_ssn):
        logger.info("NO_SSN in Cerebrum != NO_SSN in datafile. Updating "
                     "�%s� -> �%s�", cerebrum_no_ssn, no_ssn)

    return True
        


def populate_external_ids(db, person, fields, const):
    """
    Locate (or create) a person holding the IDs contained in FIELDS and
    register these external IDs if necessary.

    This function both alters the PERSON object and retuns a boolean value
    (True means the ID update/lookup was successful, False means the
    update/lookup failed and nothing can be ascertained about the PERSON's
    state).

    There are two external IDs in SAP -- the Norwegian social security
    number (11-siffret personnummer, no_ssn) and the SAP employee id
    (sap_id). SAP IDs are permanent, no_ssn can change.
    """

    sap_id, no_ssn, birth_date, fo_kode = (fields[0], fields[4],
                                           fields[5], fields[25])

    # if (fo_kode and 
    #     int(SAPForretningsOmradeKode(fo_kode)) ==
    #     int(const.sap_eksterne_tilfeldige)):
    #     logger.debug("Ignored external person: �%s��%s�", sap_id, no_ssn)
    #     return False
    
    try:
        already_exists = locate_person(person, sap_id, no_ssn, const)
    except AssertionError:
        logger.exception("Lookup for (sap_id; no_ssn) == (%s; %s) failed",
                         sap_id, no_ssn)
        return False

    if already_exists:
        logger.debug("A person owning IDs (%s, %s) already exists",
                     sap_id, no_ssn)
        # Now, we *must* check that the IDs registered in Cerebrum match
        # those in SAP dump. I.e. we select the external IDs from Cerebrum
        # and compare them to SAP_ID and NO_SSN. They must either match
        # exactly or be absent.
        if not match_external_ids(person, sap_id, no_ssn, const):
            return False
    else:
        logger.debug("New person for IDs (%s, %s)", sap_id, no_ssn)

    try:
        fodselsnr.personnr_ok(no_ssn)
    except fodselsnr.InvalidFnrError:
        logger.error("No valid check sum for NO_SSN (%s)!" % no_ssn)
        return False        

    year, month, day = (int(birth_date[:4]), int(birth_date[4:6]),
                        int(birth_date[6:]))
    gender = const.gender_male
    if fodselsnr.er_kvinne(no_ssn):
        gender = const.gender_female

    # This would allow us to update birthdays and gender information for
    # both new and existing people.
    person.populate(db.Date(year, month, day), gender)

    person.affect_external_id(const.system_sap,
                              const.externalid_fodselsnr,
                              const.externalid_sap_ansattnr) 
    
    person.populate_external_id(const.system_sap,
                                int(const.externalid_sap_ansattnr),
                                str(sap_id))
    
    person.populate_external_id(const.system_sap,
                                int(const.externalid_fodselsnr),
                                str(no_ssn))
    return True



def populate_names(person, fields, const):
    """
    Extract all name forms from FIELDS and populate PERSON with these.
    """

    # List of names, with respective indices for values from FIELDS
    # TBD: name_middle name variant is not used by update_cached_names.
    #      this means that none of the registered middle names are
    #      visible in export systems (LDAP and such).
    #      until correct (according to norwegian laws) use of middle
    #      names has been determined the we will simply join first name
    #      and middle name and update name_first name variant with
    #      the result
    #    old code:
    mname = string.strip(fields[7])
    if mname:
        fname = string.strip(fields[6]) + ' ' + mname
    else:
        fname = string.strip(fields[6])

    name_types = ((const.name_first, 6),
                  (const.name_middle, 7),
                  (const.name_last, 8),
                  (const.name_initials, 3),
                  (const.name_work_title, 28))
    
    person.affect_names(const.system_sap,
                        *[x[0] for x in name_types]) 

    for name_type, index in name_types:
        if name_type <> const.name_first and name_type <> const.name_middle:
            value = string.strip(fields[index])
            if not value:
                continue
            person.populate_name(name_type, value)
            logger.debug("Populated name type %s with �%s�", name_type, value)
    person.populate_name(const.name_first, fname)
    


def populate_communication(person, fields, const):
    """
    Extract all communication forms from FIELDS and populate PERSON with
    these.
    """
    
    # SAP designation: TLFPRIV
    comm_types = ((const.contact_phone_private, 12),
                  #    TLFINT
                  (const.contact_phone, 13),
                  #    TLFMOB
                  (const.contact_phone_cellular, 14),
                  #    TLFMOBPRIV
                  (const.contact_phone_cellular_private, 15),
                  #    FAX
                  (const.contact_fax, 29))
    for comm_type, index in comm_types:
        value = string.strip(fields[index])
        if not value:
            continue

        person.populate_contact_info(const.system_sap, comm_type, value)
        logger.debug("Populated comm type %s with �%s�", comm_type, value)



def populate_address(person, fields, const):
    """
    Extract the person's address from FIELDS and populate the database with
    it.

    Unfortunately, there is no direct mapping between the way SAP represents
    addresses and the way Cerebrum models them, so we hack away one pretty
    godawful mess.
    """

    address_parts = (("Bostedsadr. C/O", 18),
                     ("Bostedsadr. Gate", 19),
                     ("Bostedsadr. husnr.", 20),
                     ("Bostedsadr. Tillegg", 21),
                     ("Bostedsadr. Poststed", 22),
                     ("Bostedsadr. postnr.", 23),
                     ("Bostedsadr. Land", 24)) 

    address_text = string.join(filter(None, fields[18:22]), 
                               ", ").strip() or None
    city = fields[22].strip() or None
    postal_number = fields[23].strip() or None
    country = None
    if fields[24].strip():
	try:
	    country = int(const.Country(fields[24].strip()))
	except Errors.NotFoundError:
	    logger.warn("Could not find country code for �%s�, please define country in Constants.py",fields[24].strip())

    person.populate_address(const.system_sap,
                            const.address_post,
                            address_text = address_text,
                            postal_number = postal_number,
                            city = city, country = country)
      


def populate_SAP_misc(person, fields, const):
    """
    Populate all SAP specific attributes that do not fall into any other
    categories.

    For now, there is only one attribute -- fo_kode/gsber (person's
    association to a forretningsomr�de)
    """

    fo_kode_external = fields[25].strip()

    # No code, no action
    if not fo_kode_external:
        return
    
    #fo_kode_internal = int(SAPForretningsOmradeKode(fo_kode_external))
    #person.populate_forretningsomrade(fo_kode_internal)
    logger.debug("Populated fo_kode for person_id %s with %s",
                 person.entity_id, fo_kode_external)    



def add_person_to_group(group, person, fields, const):
    """
    Check if person should be visible in catalogs like LDAP or not. If
    latter, add the person to a group specified in cereconf.    
    """
    
    # Test if person should be visible in catalogs like LDAP
    x = fields[36].strip()
    if not x or x == 'Kan publiseres':
        return
    
    # person should not be visible. Add person to group 
    try:
        group_name = cereconf.HIDDEN_PERSONS_GROUP
        group.find_by_name(group_name)
    except AttributeError:
        logger.warn("Cannot add person to group. " +
                    "Group name not set in cereconf.")
        return
    except Errors.NotFoundError:
        logger.warn("Could not find group with name %s" % group_name)
        return
        
    group_operator = const.group_memberop_union
    if group.has_member(person.entity_id, person.entity_type, group_operator):
        logger.info("Person %s is already member of group %s" % (
            person.get_name(const.system_cached, const.name_full) , group_name))
        return
    try:
        group.add_member(person.entity_id, person.entity_type, group_operator)
    except:
        logger.warn("Could not add person %s to group %s" % (
            person.get_name(const.system_cached, const.name_full), group_name))
        return

    logger.info("OK, added %s to group %s" % (
        person.get_name(const.system_cached, const.name_full), group_name))
    


def process_people(filename, db):
    """
    Scan FILENAME and perform all the necessary imports.

    Each line in FILENAME contains SAP information about one person.
    """

    person = Factory.get("Person")(db)
    const = Factory.get("Constants")(db)
    group = Factory.get("Group")(db)

    stream = open(filename, "r")
    for entry in stream:
        fields = sap_row_to_tuple(entry)
        if len(fields) != FIELDS_IN_ROW:
            logger.debug("Strange line: �%s�", entry)
            continue

        # If the IDs are inconsistent with Cerebrum, skip the record
        if not populate_external_ids(db, person, fields, const):
            continue

        # Force a new entity_id for new entries
        person.write_db()
        
        populate_names(person, fields, const)

        # FIXME: We lack affiliation assignment here
        # (based on ORGEH, BEGDA, ENDDA fields)

        populate_communication(person, fields, const)

        populate_address(person, fields, const)

        populate_SAP_misc(person, fields, const)

        # Some persons should be not be visible in catalogs like LDAP.
        # Add them to a group specified in cereconf
        add_person_to_group(group, person, fields, const)

        # Sync person object with the database
        person.write_db()



def main():
    """
    Entry point for this script.
    """ 
        
    global logger
    logger = Factory.get_logger("console")

    options, rest = getopt.getopt(sys.argv[1:],
                                  "s:d",
                                  ["sap-file=",
                                   "dryrun",])
    input_name = None
    dryrun = False
    
    for option, value in options:
        if option in ("-s", "--sap-file"):
            input_name = value
        elif option in ("-d", "--dryrun"):
            dryrun = True

    db = Factory.get("Database")()
    db.cl_init(change_program='import_SAP')

    process_people(input_name, db)

    if dryrun:
        db.rollback()
        logger.info("Rolled back all changes")
    else:
        db.commit()
        logger.info("Committed all changes")





if __name__ == "__main__":
    main()
