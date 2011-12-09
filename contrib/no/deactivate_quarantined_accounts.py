#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Copyright 2011 University of Oslo, Norway
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

#
# This script checks all accounts for a given type of quarantine. If
# such quarantine exists and it has been created before the date
# implied by the since-parameter the account is deactivated.  Only
# active quarantines are considered.  
# 
# If anything but removal of spreads and setting of expire_data <
# today is needed for deactivation and institution specific
# deactivate() should be implemented in modules/no/INST/Account.py
# (institution-specific account mixin).

import sys
import getopt

import time, mx.DateTime as dt

import cerebrum_path
import cereconf
from Cerebrum import Errors
from Cerebrum.Utils import Factory

logger = Factory.get_logger("cronjob")
database = Factory.get("Database")()
database.cl_init(change_program="deactivate-qua")
constants = Factory.get("Constants")(database)
# we could probably generalise and use entity here, but for now we
# need only look at accounts
account = Factory.get("Account")(database)
today = dt.today()


def fetch_all_relevant_accounts(qua_type, since):
    # by using only_active we may inadverently allow accounts with
    # disabled quarantines to live for prolonged periods of
    # time. TODO: is this actually a problem? Jazz, 2011-11-03
    logger.debug("only quarantines older than %s days", since)
    has_quarantine = account.list_entity_quarantines(entity_types=constants.entity_account, 
                                                     quarantine_types=qua_type, 
                                                     only_active=True)
    relevant_accounts = []
    
    for x in has_quarantine:
        tmp = today - x['start_date']
        since_start = int(tmp.days)
        logger.debug("Days since quarantine started: %s", since_start)
        delta = int(since) - since_start
        if delta <= 0:
            logger.debug("in range; quarantine %s days old, %s days required; adding %s to deactivate list",
                         since_start, since, x['entity_id'])
            relevant_accounts.append(x['entity_id'])
        else:
            logger.debug("Quarantine for %s is only %s days old (should be %s), skipping",
                         x['entity_id'], since_start, since)
            continue
    return relevant_accounts
        
def usage(exitcode=0):
    print """Usage: deactivate_quarantined_accounts.py -q quarantine_type -s #days [-d]
    Deactivate all accounts where quarantine q has been set for at least #days
    Default values are: quarantine_generell and 30 days

    -q, --quarantine: quarantine type, i.e. quarantine_generell
    -s, --since:      nr of days since quarantine started 
    -d, --dryrun:     do a roll-back in stead of writing to the database
    -h, --help:       show this and quit
    """
    sys.exit(exitcode)
    
def main():
    options, junk = getopt.getopt(sys.argv[1:],
                                  "q:s:dh",
                                  ("quarantine=",
                                   "dryrun",
                                   "help",
                                   "since=",))
    dryrun = False
    # default quarantine type
    quarantine = int(constants.quarantine_generell)
    # number of days since quarantine has started
    since = 30
    
    for option, value in options:
        if option in ("-q", "--quarantine",):
            quarantine = int(constants.Quarantine(value))
        elif option in ("-d", "--dryrun",):
            dryrun = True
        elif option in ("-s", "--since",):
            since = value
        elif option in ("-h", "--help",):
            usage()
        else:
            usage()
    
    logger.info("Fetching relevant accounts")
    rel_accounts = fetch_all_relevant_accounts(quarantine, since)
    logger.info("Got %s accounts to deactivate", len(rel_accounts))

    for a in rel_accounts:
        account.clear()
        try:
            account.find(int(a))
        except Errors.NotFoundError:
            logger.warn("Could not find account_id %s, skipping", a)
            continue
        account.deactivate()
        logger.info("Deactivated account %s", account.account_name)

    if dryrun:
        database.rollback()
        logger.info("rolled back all changes")
    else:
        database.commit()
        logger.info("changes commited")

if __name__ == '__main__':
    main()