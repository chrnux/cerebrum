#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright 2012 University of Oslo, Norway
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

"""Script for creating accounts for all persons that matches given criterias. If
a person has previously had an account which is now deactivated, it will be
restored.

Note that a person will only get one account top. TBD: or should it be possible
to override this?

TODO: add support for restore of accounts.

TODO: add functionality for only affecting new person affiliations instead, e.g.
only new employeed from the last 7 days. This is usable e.g. for UiO.

"""

import sys
import os.path
import getopt
from mx import DateTime

import cerebrum_path
import cereconf

from Cerebrum import Errors, Constants
from Cerebrum.Utils import Factory

logger = Factory.get_logger('cronjob')
db = Factory.get('Database')()
db.cl_init(change_program="generate_accounts")
co = Factory.get('Constants')(db)

def usage(exitcode=0):
    print """Usage: %(file)s --aff AFFS [options]

    %(doc)s

    --aff AFFILIATIONS      Only persons with the given affiliations and/or
                            statuses will get an account. Can be comma
                            separated. Example:

                                ANSATT,TILKNYTTET/ekstern,STUDENT/fagperson

    --new-trait TRAITNAME   If set, gives every new account the given trait.
                            Usable e.g. for sending a welcome SMS for every new
                            account.

    --commit                Actually commit the work. The default is dryrun.

    -h --help               Show this and quit.
    """ % {'file': os.path.basename(sys.argv[0]),
           'doc': __doc__}
    sys.exit(exitcode)

def str2aff(affstring):
    """Get a string with an affiliation or status and return its constant."""
    aff = affstring.split('/', 1)
    if len(aff) > 1:
        aff = co.PersonAffStatus(aff[0], aff[1])
    else:
        aff = co.PersonAffiliation(affstring)
    try:
        int(aff)
    except Errors.NotFoundError:
        raise Exception("Unknown affiliation: %s" % affstring)
    return aff

def create_account(pe, ac, creator_id, new_trait=None):
    """Give a person a new account, or restore one of its old ones, if such an
    account exists. Note that we here assume that a person only should have
    one account automatically created.

    """
    ac.clear()
    #for row in ac.search(owner_id=pe.entity_id, expire_start=None):
    #    logger.debug("Person %d already has account: %s", pe.entity_id,
    #                 row['name'])
    #    # TODO: should we just assume that persons only should have one
    #    # automatically generated account?
    #    ac.find(row['account_id'])
    #    if ac.

    #    return True

    name = (pe.get_name(co.system_cached, co.name_first),
            pe.get_name(co.system_cached, co.name_last))
    names = ac.suggest_unames(domain=co.account_namespace, fname=name[0], lname=name[1])
    if len(names) < 1:
        logger.warn('Person %d has no name, skipping', pe.entity_id)
        return
    ac.create(name=names[0], owner_id=pe.entity_id, creator_id=creator_id)
    logger.debug("Account %s created", names[0])

    if new_trait:
        ac.populate_trait(new_trait, date=DateTime.now())

    # give the account the person's affiliations
    for row in pe.list_affiliations(person_id=pe.entity_id):
        ac.set_account_type(ou_id=row['ou_id'], affiliation=row['affiliation'])
        ac.write_db()
        logger.debug("Gave %s aff %s to ou_id=%s", names[0],
                     co.PersonAffiliation(row['affiliation']), row['ou_id'])
    return True

def process(affiliations, commit=False, new_trait=None):
    """Go through the database for new persons and give them accounts."""
    logger.info("generate_accounts started")

    ac = Factory.get('Account')(db)
    pe = Factory.get('Person')(db)

    ac.find_by_name(cereconf.INITIAL_ACCOUNTNAME)
    creator_id = ac.entity_id

    logger.debug('Caching existing accounts')
    has_account = set(row['owner_id'] for row in
                      ac.search(owner_type=co.entity_person, expire_start=None))
    logger.debug("%d people already have an account" % len(has_account))

    # sort by affiliation and status
    statuses = tuple(af for af in affiliations 
                     if isinstance(af, Constants._PersonAffStatusCode))
    affs = tuple(af for af in affiliations 
                 if isinstance(af, Constants._PersonAffiliationCode))

    if statuses:
        for row in pe.list_affiliations(status=statuses):
            if row['person_id'] in has_account:
                continue
            pe.clear()
            pe.find(row['person_id'])
            create_account(pe, ac, creator_id, new_trait)
            has_account.add(row['person_id'])
    if affs:
        peaffs = pe.list_affiliations(affiliation=affs)
        logger.debug("%d affiliations to process" % len(peaffs))
        for row in peaffs:
            if row['person_id'] in has_account:
                continue
            pe.clear()
            pe.find(row['person_id'])
            create_account(pe, ac, creator_id, new_trait)
            has_account.add(row['person_id'])

    if commit:
        db.commit()
        logger.info("Changes commited")
    else:
        db.rollback()
        logger.info("Rolled back changes")
    logger.info("generate_accounts done")

def main():
    opts, junk = getopt.getopt(sys.argv[1:], "h",
                               ("help",
                                "aff=",
                                "new-trait=",
                                "commit"))
    affiliations = list()
    commit = False
    new_trait = None

    for opt, val in opts:
        if opt in ("-h", "--help",):
            usage()
        elif opt in ("--aff",):
            affiliations.extend((str2aff(a) for a in val.split(',')))
        elif opt in ("--commit",):
            commit = True
        elif opt in ("--new-trait",):
            new_trait = int(co.EntityTrait(val))
        else:
            print "Unknown argument: %s" % opt
            usage(1)

    if not affiliations:
        print "No affiliations given"
        usage(1)
    process(affiliations, commit, new_trait)

if __name__ == '__main__':
    main()
