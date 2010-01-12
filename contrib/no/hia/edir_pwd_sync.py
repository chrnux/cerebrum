#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright 2002-2010 University of Oslo, Norway
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

# account_add, account_rem, account_mod?
# group add account, group rem account
# group_add, group_rem
# quarantine_add, quarantine_rem, quarantine_mod

#
import sys, os, getopt, time, string, pickle, re, ldap, ldif

import cerebrum_path
import cereconf
from Cerebrum import Constants
from Cerebrum.modules.no.hia import EdirUtils
from Cerebrum.modules.no.hia import EdirLDAP
from Cerebrum import Errors
from Cerebrum import Group
from Cerebrum import Entity
from Cerebrum.extlib import logging
from Cerebrum.Utils import Factory
from Cerebrum.modules import CLHandler

def main():
    global db, constants, account
    global edir_util, logger
    
    db = Factory.get('Database')()
    constants = Factory.get('Constants')(db)
    account = Factory.get("Account")(db)
    cl_handler = CLHandler.CLHandler(db)
    logger = Factory.get_logger('cronjob')

    cl_events = []

    passwd = db._read_password(cereconf.NW_LDAPHOST,
                               cereconf.NW_ADMINUSER.split(',')[:1][0])
    ldap_handle = EdirLDAP.LDAPConnection(db, cereconf.NW_LDAPHOST,
                                          cereconf.NW_LDAPPORT,
                                          binddn=cereconf.NW_ADMINUSER,
                                          password=passwd, scope='sub')
    edir_util = EdirUtils.EdirUtils(db, ldap_handle)

    try:
        cl_events = cl_handler.get_events('edirpwdsync', (constants.account_password,))
        if cl_events == []:
            logger.info("Nothing to do.")
            ldap_handle.close_connection()
            sys.exit(0)
            
        for event in cl_events:
            if event['change_type_id'] == constants.account_password:
                pwd = pickle.loads(event['change_params'])['password']
                passwd = unicode(pwd, 'iso-8859-1').encode('utf-8')
                account.clear()
                try:
                    account.find(event['subject_entity'])
                except Errors.NotFoundError:
                    logger.warn("No such account %s", event['subject_entity'])
                    cl_handler.confirm_event(event)
                    continue
                if account.has_spread(constants.spread_hia_novell_user):
                    edir_util.account_set_password(account.account_name, passwd)
                cl_handler.confirm_event(event)
    except TypeError, e:
        logger.warn("No such event, %s" % e)
        return None
    cl_handler.commit_confirmations()

    ldap_handle.close_connection()
    
if __name__ == '__main__':
    main()
