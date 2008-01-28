#!/usr/bin/env python
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

"""
This file is a HiA-specific extension of Cerebrum. It contains code which
import historical account and e-mail data from HiA into Cerebrum. Normally,
it should be run only once (about right after the database has been
created).

The input format for this job is a file with one line per
account/e-mail. Each line has four fields separated by ':'.

<no_ssn>:<name_full>:<uname>:<e-mail address>

... where

no_ssn  -- 11-digit Norwegian social security number (personnummer)
name_full -- persons name
uname   -- account name
keyword -- 'defaultmail' or 'mail'
"""

import getopt
import sys
import string

import cerebrum_path
import cereconf

from Cerebrum import Errors
from Cerebrum.Utils import Factory
from Cerebrum.modules import Email
from Cerebrum.modules.no import fodselsnr
from Cerebrum.modules import PosixUser

def process_line(infile):
    """
    Scan all lines in INFILE and create corresponding account/e-mail entries
    in Cerebrum.
    """
    stream = open(infile, 'r')

    # Iterate over all persons:
    for line in stream:

        logger.debug5("Processing line: |%s|", line)
        fields = string.split(line.strip(), ";")
        print len(fields)
        if len(fields) != 5:
            logger.error("Bad line: %s. Skipping" % line)
            continue
        # fi
        
        fnr, pname, uname, email, foo = fields
        if not fnr == "":
            logger.debug("Processing person %s", fnr)
            try:
                fodselsnr.personnr_ok(fnr)
            except fodselsnr.InvalidFnrError:
                logger.warn("Bad no_ssn %s, skipping", fnr)
                continue

        person.clear()
        gender = constants.gender_male

        if fodselsnr.er_kvinne(fnr):
            gender = constants.gender_female

        y, m, d = fodselsnr.fodt_dato(fnr)

        # Can't just populate like this, we need to search for persons
        # first.
        try:
            person.find_by_external_id(constants.externalid_fodselsnr, fnr)
        except Errors.NotFoundError:
            pass
        
        person.populate(db.Date(y, m, d), gender)
        person.affect_external_id(constants.system_ekstens,
                                  constants.externalid_fodselsnr)
        person.populate_external_id(constants.system_ekstens,
                                    constants.externalid_fodselsnr,
                                    fnr)
        person.write_db()
        
        update_names(fnr, pname)
        
        person.write_db()
        logger.debug("Created new person with fnr %s", fnr)

        p_id = person.entity_id

        account_id = process_user(p_id, uname)

        process_mail(account_id, 'defaultmail', email)
        
# end process_person

def process_user(owner_id, uname):
    """
    Locate account_id of account UNAME owned by OWNER_ID.
    """
    
    if uname == "":
        return None
    # fi
    
    owner_type = constants.entity_person
    
    np_type = None
    try:
        account.clear()
        account.find_by_name(uname)
        logger.debug3("User %s exists in Cerebrum", uname)
    except Errors.NotFoundError:
        account.populate(uname,
                         owner_type,
                         owner_id,
                         np_type,
                         default_creator_id,
                         None)
        account.write_db()
        logger.debug3("User %s created", uname)
    # yrt

    a_id = account.entity_id
    return a_id

def process_mail(account_id, type, addr):
    et = Email.EmailTarget(db)
    ea = Email.EmailAddress(db)
    edom = Email.EmailDomain(db)
    epat = Email.EmailPrimaryAddressTarget(db)

    addr = string.lower(addr)    

    fld = addr.split('@')
    if len(fld) != 2:
        logger.error("Bad address: %s. Skipping", addr)
        return None
    # fi
    
    lp, dom = fld
    try:
        edom.find_by_domain(dom)
        logger.debug("Domain found: %s: %d", dom, edom.entity_id)
    except Errors.NotFoundError:
        edom.populate(dom, "Generated by import_uname_mail.")
        edom.write_db()
        logger.debug("Domain created: %s: %d", dom, edom.entity_id)
    # yrt

    try:
        et.find_by_target_entity(int(account_id))
        logger.debug("EmailTarget found(accound): %s: %d",
                     account_id, et.entity_id)
    except Errors.NotFoundError:
        et.populate(constants.email_target_account, entity_id=int(account_id),
                    entity_type=constants.entity_account)
        et.write_db()
        logger.debug("EmailTarget created: %s: %d",
                     account_id, et.entity_id)
    # yrt

    try:
        ea.find_by_address(addr)
        logger.debug("EmailAddress found: %s: %d", addr, ea.entity_id)
    except Errors.NotFoundError:
        ea.populate(lp, edom.entity_id, et.entity_id)
        ea.write_db()
        logger.debug("EmailAddress created: %s: %d", addr, ea.entity_id)
    # yrt

    if type == "defaultmail":
        try:
            epat.find(et.entity_id)
            logger.debug("EmailPrimary found: %s: %d",
                         addr, epat.entity_id)
        except Errors.NotFoundError:
            if ea.email_addr_target_id == et.entity_id:
                epat.clear()
                epat.populate(ea.entity_id, parent=et)
                epat.write_db()
                logger.debug("EmailPrimary created: %s: %d",
                             addr, epat.entity_id)
            else:
                logger.error("EmailTarget mismatch: ea: %d, et: %d", 
                             ea.email_addr_target_id, et.entity_id)
            # fi
        # yrt
    # fi
    
    et.clear()
    ea.clear()
    edom.clear()
    epat.clear()
# end process_mail
    
def update_names(fnr, name_full):
    person2 = Factory.get("Person")(db)
    person2.clear()
    person2.find_by_external_id(constants.externalid_fodselsnr, fnr)
    person2.affect_names(constants.system_ekstens, constants.name_full)
    person2.populate_name(constants.name_full, name_full)
    
    person2.write_db()    

def usage():
    print """Usage: import_uname_mail.py
    -d, --dryrun  : Run a fake import. Rollback after run.
    -f, --file    : File to parse.
    """
    sys.exit(0)
# end usage



def main():
    global db, constants, account, person, fnr2person_id
    global default_creator_id
    global dryrun, logger, group

    logger = Factory.get_logger("console")
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'f:d',
                                   ['file=',
                                    'dryrun'])
    except getopt.GetoptError:
        usage()
    # yrt

    dryrun = False
    for opt, val in opts:
        if opt in ('-d', '--dryrun'):
            dryrun = True
        elif opt in ('-f', '--file'):
            infile = val
        # fi
    # od

    if infile is None:
        usage()
    # fi

    db = Factory.get('Database')()
    db.cl_init(change_program='import_person')
    group = Factory.get("Group")(db)
    constants = Factory.get('Constants')(db)
    account = Factory.get('Account')(db)
    acc = Factory.get('Account')(db)
    person = Factory.get('Person')(db)

    acc.find_by_name(cereconf.INITIAL_ACCOUNTNAME)
    default_creator_id = acc.entity_id
    process_line(infile)
    if not dryrun:
        db.commit()
# end main


if __name__ == '__main__':
    main()
# fi

# arch-tag: d7992a61-eb09-4683-a072-43e3c6fdf352
