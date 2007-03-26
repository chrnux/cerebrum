#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Copyright 2005 University of Oslo, Norway
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
This module provides an interface to store objects representing XML
information in Cerebrum. It is intended to go together with xml2object
module (and its various incarnations (SAP, LT, etc.).
"""
import types

import cerebrum_path
import cereconf

from Cerebrum import Errors
from Cerebrum.Utils import Factory
from Cerebrum.modules.no.Stedkode import Stedkode

from xml2object import DataAddress, DataContact
from xml2object import HRDataPerson
from sapxml2object import SAPPerson





class XML2Cerebrum:

    def __init__(self, db, source_system, ou_ldap_visible = True):
        self.db = db
        # IVR 2007-01-22 TBD: Do we really want this here? Should db
        # not have this set already?
        self.db.cl_init(change_program="XML->Cerebrum")
        self.source_system = source_system
        self.ou_ldap_visible = ou_ldap_visible
        
        self.stedkode = Stedkode(db)
        self.person = Factory.get("Person")(db)
        self.constants = Factory.get("Constants")(db)
        self.lang_priority = ("no", "en")

        const = self.constants
        # Hammer in contact information
        self.xmlcontact2db = { DataContact.CONTACT_PHONE: const.contact_phone,
                               DataContact.CONTACT_FAX: const.contact_fax,
                               DataContact.CONTACT_URL: const.contact_url,
                               DataContact.CONTACT_EMAIL: const.contact_email,
                               DataContact.CONTACT_PRIVPHONE:
                                   const.contact_phone_private, }
        self.xmladdr2db = { DataAddress.ADDRESS_BESOK: const.address_street,
                            DataAddress.ADDRESS_POST: const.address_post,
                            DataAddress.ADDRESS_PRIVATE: 
                                const.address_post_private }
    # end __init__


    def store_person(self, xmlperson, affiliations, work_title):
        """Store all information we can from xmlperson.

        xmlperson is a class inheriting from xml2object.DataPerson,
        representing the person we want to register. affiliations is a
        dictionary of all affiliations for this person for the given
        source_system. 

        The method returns a pair (status, p_id), where status is the update
        status of the operation, and p_id is the entity_id in Cerebrum of a
        person corresponding to xmlperson.
        """
        
        person = self.person
        const = self.constants
        source_system = self.source_system
        
        gender2db = { xmlperson.GENDER_MALE : const.gender_male,
                      xmlperson.GENDER_FEMALE : const.gender_female, }
        name2db = { xmlperson.NAME_FIRST : const.name_first,
                    xmlperson.NAME_LAST  : const.name_last,
                    xmlperson.NAME_TITLE : const.name_personal_title, }
        
        idxml2db = { HRDataPerson.NO_SSN : const.externalid_fodselsnr,
                     SAPPerson.SAP_NR    : const.externalid_sap_ansattnr, }
        xmlcontact2db = self.xmlcontact2db

        person.clear()
        # Can this fail?
        fnr = xmlperson.get_id(xmlperson.NO_SSN)
        try:
            person.find_by_external_id(const.externalid_fodselsnr, fnr)
        except Errors.NotFoundError:
            pass
        except Errors.TooManyRowsError:
            try:
                person.find_by_external_id(const.externalid_fodselsnr, fnr,
                                           source_system)
            except Errors.NotFoundError:
                pass
            # yrt
        # yrt
            
        person.populate(xmlperson.birth_date, gender2db[xmlperson.gender])
        person.affect_names(source_system, *name2db.values())
        # TBD: This may be too permissive 
        person.affect_external_id(source_system, *idxml2db.values())

        # We *require* certain names
        for id in (xmlperson.NAME_FIRST, xmlperson.NAME_LAST,):
            assert xmlperson.get_name(id, None) is not None
            # There should be exactly one, actually
            name = xmlperson.get_name(id).value
            person.populate_name(name2db[id], name)
        # od

        # ... and allow others to be missing
        if xmlperson.get_name(xmlperson.NAME_TITLE):
            # FIXME: How many names can potentially match?
            person.populate_name(name2db[xmlperson.NAME_TITLE],
                                 xmlperson.get_name(xmlperson.NAME_TITLE).value) 
        # fi

        # TBD: The implicit assumption here is that idxml2db contains all the
        # mappings
        for xmlkind, value in xmlperson.iterids():
            person.populate_external_id(source_system, idxml2db[xmlkind], value)
        # od
        op = person.write_db()

        if work_title:
            person.affect_names(source_system, const.name_work_title)
            person.populate_name(const.name_work_title, work_title)
        # fi 

        #
        # FIXME: LT data.
        # 
        # This one isn't pretty. The problem is that in LT some of the
        # addresses (e.g. ADDRESS_POST) have to be derived from the addresses
        # of the "corresponding" OUs. This breaks quite a few abstractions in
        # this code.
        #
        
        for addr_kind in (DataAddress.ADDRESS_BESOK, DataAddress.ADDRESS_POST,
                          DataAddress.ADDRESS_PRIVATE):
            addr = xmlperson.get_address(addr_kind)
            if not addr:
                continue

            # FIXME: country-table is not populated in the database. We cannot
            # write anything to the country-slot, until that table is
            # populated.
            person.populate_address(source_system,
                                    type = self.xmladdr2db[addr_kind],
                                    address_text = addr.street or None,
                                    postal_number = addr.zip or None,
                                    city = addr.city or None,)
        # od 

        person.populate_affiliation(source_system)
        for value in affiliations.itervalues():
            ou_id, aff, aff_stat = value
            person.populate_affiliation(source_system, ou_id, 
                                        int(aff), int(aff_stat))
        # od

        person.populate_contact_info(source_system)
        for ct in xmlperson.itercontacts():
            person.populate_contact_info(source_system,
                                         xmlcontact2db[ct.kind],
                                         ct.value, ct.priority)
        # od
        op2 = person.write_db()

        if op is None and op2 is None:
            status = "EQUAL"
        elif op == True:
            status = "NEW"
        else:
            status = "UPDATE"
        # fi

        return status, person.entity_id
    # end store_person


    def __extract_name_lang(self, xmlou, kind, length=None):
        """Pull a certain name out of the XML OU object.

        If a name with a given language does not exist, we just ignore the language.
        """

        pri = self.lang_priority
        name = xmlou.get_name_with_lang(kind, *pri)
        if name is None:
            name = xmlou.get_name(kind)
            # there may be several names, we need just one. pick one at
            # random, if no other information is available
            if isinstance(name, (list, tuple)):
                name = name[0]

            if name:
                name = name.value
        # fi

        if name and length:
            name = name[:length]

        return name
    # end __extract_name_lang


    def store_ou(self, xmlou, old_ou_cache=None):
        """Store all information we can from xmlou.

        xmlou is a class inheriting from xml2object.DataOU.

        old_ou_cache is a cache of ou_ids that already exist in cerebrum (and
        that we might want to clear).

        NB! No parent information is stored in this method.

        The method returns a pair (status, ou_id), where status is the update
        status of the operation, and ou_id is the entity_id in Cerebrum of an
        OU corresponding to xmlou.
        """

        ou = self.stedkode
        ou.clear()
        const = self.constants

        # We need sko, katalog_merke, acronym, short_name,
        # display_name, sort_name. Also parent.
        sko = xmlou.get_id(xmlou.NO_SKO)
        acronym = self.__extract_name_lang(xmlou, xmlou.NAME_ACRONYM, 15)
        short = self.__extract_name_lang(xmlou, xmlou.NAME_SHORT, 30)
        name = self.__extract_name_lang(xmlou, xmlou.NAME_LONG, 512)
        display_name = self.__extract_name_lang(xmlou, xmlou.NAME_LONG, 80)
        sort_name = self.__extract_name_lang(xmlou, xmlou.NAME_LONG, 80)
               
        try:
            ou.find_stedkode(sko[0], sko[1], sko[2],
                             cereconf.DEFAULT_INSTITUSJONSNR)
        except Errors.NotFoundError:
            pass
        else:
            #
            # Although it is impossible for an OU *not* to be in cache when we
            # find its sko in find_stedkode() above, *IF* the data source
            # duplicates an OU (clear error in the data source), then this
            # situation still may happen.
            if old_ou_cache and int(ou.ou_id) in old_ou_cache:
                del old_ou_cache[int(ou.ou_id)]
                for r in ou.get_entity_quarantine():
                    if (r['quarantine_type'] == const.quarantine_ou_notvalid or
                        r['quarantine_type'] == const.quarantine_ou_remove):
                        ou.delete_entity_quarantine(r['quarantine_type'])
                    # fi
                # od
            # fi
        # yrt

        # TBD: Do we need a more generic interface to 'visibility'
        # information?
        katalog_merke = 'F'
        if getattr(xmlou, "publishable", False) or self.ou_ldap_visible:
            katalog_merke = 'T'
        # fi

        ou.populate(name, sko[0], sko[1], sko[2],
                    institusjon = cereconf.DEFAULT_INSTITUSJONSNR,
                    katalog_merke = katalog_merke,
                    acronym = acronym, short_name = short,
                    display_name = display_name, sort_name = sort_name)

        # Hammer in all addresses
        xmladdr2db = self.xmladdr2db
        for addr_kind, addr in xmlou.iteraddress():
            ou.populate_address(self.source_system, xmladdr2db[addr_kind],
                                address_text = addr.street,
                                postal_number = addr.zip,
                                city = addr.city,
                                # TBD: country code table i Cerebrum is empty
                                country = None)
        # od

        # Hammer in contact information
        xmlcontact2db = self.xmlcontact2db
        for contact in xmlou.itercontacts():
            ou.populate_contact_info(self.source_system,
                                     xmlcontact2db[contact.kind],
                                     contact.value,
                                     contact_pref = contact.priority)
        # od
        op = ou.write_db()
        
        if op is None:
            status = "EQUAL"
        elif op:
            status = "NEW"
        else:
            status = "UPDATE"
        # fi

        return status, ou.entity_id
    # end store_ou
# end XML2Cerebrum
        
        
        


# arch-tag: 67a1b79a-6600-4e09-aaaf-41c1f4dc4d40

