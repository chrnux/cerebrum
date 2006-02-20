#! /usr/bin/env python
# -*- coding: iso8859-1 -*-
#
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

Thie file performs group membership synchronization between several external
databases and cerebrum.

The updates are performed for the following sources/groups:

External db	table/source				Cerebrum group
----------------------------------------------------------------------
OFPROD		select user_name FROM applsys.fnd_user	ofprod
FSPROD		select username FROM all_users		fsprod
AJPROD		select username FROM all_users		ajprod
LTPROD		select username FROM all_users		ltprod
OAPRD		select user_name FROM applsys.fnd_user	oaprd
OEPATST		[1], [2]

[1]   basware-users:
      select USER_NETWORK_NAME FROM basware.ip_group_user
      WHERE GROUP_NAME = 'BasWareBrukere' AND upper(DOMAIN) = 'UIO'
[2]   basware-masters:
      SELECT USER_NETWORK_NAME FROM basware.ip_group_user
      WHERE GROUP_NAME = 'Masterbrukere' AND upper(DOMAIN) = 'UIO'

After the update, each group in cerebrum contains only the members listed in
the corresponding external database. That is, if

A -- usernames in the external db but not in cerebrum
B -- usernames in the external db AND cerebrum
C -- usernames NOT in the external db but IN cerebrum

... then only A+B shall be in cerebrum (that is, in the corresponding
cerebrum group from the table above) after the update.

This script produces no output (apart from debug/error messages). All update
information is written back to cerebrum:

<external dbs> -+---> dbfg_update.py ---+
                ^                       |
                |                       |
<cerebrum db> --+                       |
      ^---------------------------------+

Each of the updates can be turned on/off from the command line.
"""

import sys
import string
import getopt
import time

import cerebrum_path
import cereconf
import traceback

import Cerebrum
from Cerebrum import Database
from Cerebrum.Utils import Factory
from Cerebrum.Utils import AtomicFileWriter
from Cerebrum.modules.no.uio.access_LT import LT
from Cerebrum.modules.no.uio.access_FS import FS
from Cerebrum.modules.no.uio.access_OF import OF
from Cerebrum.modules.no.uio.access_AJ import AJ
from Cerebrum.modules.no.uio.access_OA import OA
from Cerebrum.modules.no.uio.access_OEP import OEP





def sanitize_group(cerebrum_group, constants):
    """
    This helper function removes 'unwanted' members of CEREBRUM_GROUP.

    The groups handled by this script are flat and should contain only union
    members. That is:

    * all group members (of CEREBRUM_GROUP) are deleted (union or not)
    * all intersection members are deleted.
    * all difference members are deleted.
    """

    union, intersection, difference = cerebrum_group.list_members()
    removed_count = 0

    # First, let's get rid of group union members
    for entity_type, entity_id in union:
        if int(entity_type) == int(constants.entity_group):
            logger.error("Aiee! Group id %s is a member of group %s",
                         entity_id, cerebrum_group.group_name)
            cerebrum_group.remove_member(int(entity_id),
                                         constants.group_memberop_union)
            removed_count += 1
        # fi
    # od

    # ... then all intersection members
    for entity_type, entity_id in intersection:
        logger.error("Aiee! %s is an intersection member of %s",
                     entity_id, cerebrum_group.group_name)
        cerebrum_group.remove_member(int(entity_id),
                                     constants.group_memberop_intersection)
        removed_count += 1
    # od
    
    # ... and at last all difference members
    for entity_type, entity_id in difference:
        logger.error("Aiee! %s is a difference member of %s",
                     entity_id, cerebrum_group.group_name)
        cerebrum_group.remove_member(int(entity_id),
                                     constants.group_memberop_difference)
        removed_count += 1
    # od

    logger.info("%d entity(ies) was(were) sanitized from %s",
                removed_count, cerebrum_group.group_name)
# end sanitize_group



def synchronize_group(external_group, cerebrum_group_name):
    """
    This is where all the work is done.

    This function implements direct/immediate (rather then transitive)
    membership only.

    The synchronization is carried out in the following fashion:

    * Construct a set G_c of all members of CEREBRUM_GROUP_NAME
    * for each m in <external_group>:
          if <m does not exist in cerebrum>:
              # Here, an account exists in the external source, but not in
              # Cerebrum. We simply ignore these cases.
              <complain>
          elif <m does not exist in G_c>:
              # Here, the account exists in Cerebrum, but it is not a member
              # of the required group. Therefore we add it.
              <add m to the group>
          # fi

          # This marks m as processed
          <remove m from G_c>
      # od

    * At this step, everything still in G_c exists in Cerebrum, but not in
      the external source. Such entries must be removed from Cerebrum.
      for each n in G_c:
          <remove n from group>
      # od

    Adding an account to a group means:
      1. adding it as a direct 'union'-member.
      2. removing it as a direct 'difference'-member.

    Removing an account from a group means:
      1. removing it as a direct 'union'-member.
      2. removing it as a direct 'intersection'-member.

    NB! All the groups 'touched' by this script are flat. That is, only user
    accounts are members of these groups (not other groups). Furthermore,
    only union-membership is permitted.

    All group-, intersect- and difference members are removed
    automatically. This is intentional.
    """

    try:
        cerebrum_db = Factory.get("Database")()
        cerebrum_db.cl_init(change_program="dbfg_update")
        cerebrum_group = Factory.get("Group")(cerebrum_db)
        cerebrum_account = Factory.get("Account")(cerebrum_db)
        constants = Factory.get("Constants")

        cerebrum_group.find_by_name(cerebrum_group_name)
    except Cerebrum.Errors.NotFoundError:
        logger.error("Aiee! Group %s not found in cerebrum. " +
                     "We will not be able to synchronize it")
        return
    # yrt

    sanitize_group(cerebrum_group, constants)

    new_count = 0
    external_count = 0

    current = construct_group(cerebrum_group)
    for row in external_group():
        external_count += 1

        # FIXME: Ugh! Username cases are different here and there. This
        # assumes that there are no two different accounts whose name
        # differs only in the case. However, there are also accounts with
        # mixed cased in cerebrum. Basically, this means that such accounts
        # would be left out of group synchronization.
        #
        # External sources hand us usernames in uppercase.
        account_name = string.lower(row.fields.username)

        # Find it in cerebrum
        try:
            cerebrum_account.clear()
            # NB! This one searches among expired and non-expired users
            cerebrum_account.find_by_name(account_name)
        except Cerebrum.Errors.NotFoundError:
            logger.info("%s exists in the external source, but not in Cerebrum",
                        account_name)
        else:
            # Here we now that the account exists in Cerebrum.
            # Is it a member of CEREBRUM_GROUP_NAME already?
            if ((account_name not in current) and
                (not cerebrum_account.get_account_expired())):
                # New member for the group! Add it to Cerebrum
                add_to_cerebrum_group(cerebrum_account, cerebrum_group,
                                      constants)
                new_count += 1
            else:
                # Mark this account as processed
                if account_name in current:
                    del current[account_name]
                # fi
            # fi
        # yrt
    # od

    # Now, all that is left in CURRENT does NOT exist in EXTERNAL_GROUP.
    logger.info("Added %d new account(s) to %s",
                new_count, cerebrum_group.group_name)
    logger.info("%d account(s) from %s need to be removed",
                len(current), cerebrum_group.group_name)
    logger.info("%d account(s) in the external source", external_count)
    for account_name, account_id in current.items():
        try:
            cerebrum_account.clear()
            cerebrum_account.find_by_name(account_name)
        except Cerebrum.Errors.NotFoundError:
            logger.error("Aiee! account (%s, %s) spontaneously disappeared " + 
                         "from (%s, %s)?",
                         account_name, account_id,
                         cerebrum_group.group_name, cerebrum_group.entity_id)
        else:
            remove_from_cerebrum_group(cerebrum_account, cerebrum_group, constants)
        # yrt
    # od

    if dryrun:
        cerebrum_db.rollback()
        logger.info("All changes rolled back")
    else:
        cerebrum_db.commit()
        logger.info("Commited all changes")
    # fi
# end synchronize_group



def remove_from_cerebrum_group(account, group, constants):
    """
    Removes ACCOUNT.ENTITY_ID as a union/intersection member of
    GROUP.ENTITY_ID
    """

    try:
        # Since GROUP is 'sanitized' prior to calling this method, is there
        # any point in remove the intersection members? (there are none)
        for operation in [ constants.group_memberop_union,
                           constants.group_memberop_intersection ]:
            group.remove_member(int(account.entity_id),
                                int(operation))
        # od
    except:
        # FIXME: How safe is it to do any updates if this happens?
        type, value, tb = sys.exc_info()
        logger.error("Aiee! Removing %s from %s failed: %s, %s, %s",
                     account.account_name,
                     group.group_name,
                     str(type), str(value),
                     string.join(traceback.format_tb(tb)))
    # yrt
# end remove_from_cerebrum_group
        


def add_to_cerebrum_group(account, group, constants):
    """
    Adds the ACCOUNT.ENTITY_ID as a (union) member of GROUP.ENTITY_ID.

    Also, removes difference member ACCOUNT from GROUP, should such a member
    exist (it should not, really, but this is just a precaution).
    """

    logger.debug("Adding 'union' account member %s (%s) to group %s (%s)",
                 account.entity_id, account.account_name,
                 group.entity_id, group.group_name)

    try:
        # Add a new union member

        # NB! Removal has to be done before addition in this case.
        # Otherwise the changelog displays the changes as a removal of
        # ACCOUNT from GROUP (changelog is not aware of the various group
        # operations))
        group.remove_member(int(account.entity_id),
                            int(constants.group_memberop_difference))
        
        group.add_member(int(account.entity_id),
                         int(constants.entity_account),
                         int(constants.group_memberop_union))
    except:
        # FIXME: How safe is it to do any updates if this happens?
        type, value, tb = sys.exc_info()
        logger.error("Aiee! Adding %s to %s failed: %s, %s, %s",
                     account.account_name,
                     group.group_name,
                     str(type), str(value),
                     string.join(traceback.format_tb(tb)))
        
    # yrt
# end 



def construct_group(cerebrum_group):
    """
    This is a helper function that produces a suitable data structure for
    group synchronization.

    Specifically, it returns a dictionary mapping account names to account
    ids
    """

    result = {}

    # Although get_members() performes a recursive lookup, this gives the
    # right answer nonetheless, since the groups touched by this script are
    # "flat". Also, we call this function _after_ CEREBRUM_GROUP has been
    # "sanitized", and thus get_members() and list_members()[0] produce
    # similar answers. get_members() is just a little bit more convenient to
    # use.
    for row in cerebrum_group.get_members(get_entity_name=True):
        # <username -> account_id>
        result[row[1]] = int(row[0])
    # od

    logger.info("Fetched %d entries for group %s",
                len(result), cerebrum_group.group_name)
    
    return result
# end
    


def perform_synchronization(services):
    """
    Synchronize cerebrum groups with all external SERVICES.
    """

    for item in services:
        service = item["dbname"]
        klass = item["class"]
        accessor_name = item["sync_accessor"]
        cerebrum_group = item["ceregroup"]
        user = item["dbuser"]

        logger.debug("Synchronizing against source %s (user: %s)",
                     service, user)

        try:
            db = Database.connect(user = user, service = service,
                                  DB_driver = "Oracle")
            obj = klass(db)
            accessor = getattr(obj, accessor_name)
        except:
            type, value, tb = sys.exc_info()
            logger.error("Aiee! Failed to connect to %s: %s, %s, %s",
                         service,
                         type, value,
                         string.join(traceback.format_tb(tb)))
            
        else:
            synchronize_group(accessor, cerebrum_group)
        # yrt
    # od
# end perform_synchronization



def check_owner_status(person, owner_id, username):
    """
    A help function for report_expired_users.
    """

    try:
        person.clear()
        person.find(owner_id)
    except Cerebrum.Errors.NotFoundError:
        return "Username %s has no owner\n" % username
    # yrt

    now = time.strftime("%Y%m%d", time.gmtime(time.time()))
    if not (person.get_tilsetting(now) or
            person.get_bilag() or
            person.get_gjest(now)):
        return (("Owner of account %s has no tilsetting/bilag/gjest " +
                 "records in LT\n") % username)
    # fi

    return ""
# end check_owner_status



def check_expired(account):
    """
    Check if the given account has expired.
    """

    if account.get_account_expired():
        return "Account expired: %s\n" % account.account_name
    # fi

    return ""
# end check_expired



def check_spread(account, sprd):
    """
    Check if the given account has (UiO) NIS spread.
    """

    is_nis = False
    for spread in account.get_spread():
        if int(spread["spread"]) == int(sprd):
            is_nis = True
            break
        # fi
    # od

    if not is_nis:
        return "No spread NIS_user@uio for %s\n" % account.account_name
    # fi

    return ""
# end check_nis_spread

    

def report_users(stream_name, external_dbs):
    """
    Prepare status report about users in various databases.
    """

    db_cerebrum = Factory.get("Database")()
    person = Factory.get("Person")(db_cerebrum)
    constants = Factory.get("Constants")(db_cerebrum)
    user = "ureg2000"

    report_stream = AtomicFileWriter(stream_name, "w")

    #
    # Report expired users for all databases
    for dbname in ("ajprod",):
        item = external_dbs[dbname]
        message = make_report(user, False, item, item["sync_accessor"],
                              check_expired)
        if message:
            report_stream.write("%s contains these expired accounts:\n" %
                                item["dbname"])
            report_stream.write(message)
            report_stream.write("\n")
        # fi
    # od
        
    #
    # Report NIS spread / owner's work record
    for dbname in ("ofprod", "oaprd", "fsprod", "ltprod",
                   "basware-users", "basware-masters"):
        item = external_dbs[dbname]
        message = make_report(user, True, item, item["report_accessor"],
                              check_expired,
                              lambda acc: check_spread(acc,
                                            constants.spread_uio_nis_user),
                              lambda acc: check_owner_status(person,
                                            acc.owner_id,
                                            acc.account_name))
        if message:
            report_stream.write("%s contains these strange accounts:\n" %
                                item["dbname"])
            report_stream.write(message)
            report_stream.write("\n")
        # fi
    # od

    report_stream.close()
# end report_users



import StringIO
def make_report(user, report_missing, item, acc_name, *func_list):
    """
    Help function to generate report stats.
    """

    db_cerebrum = Factory.get("Database")()
    account = Factory.get("Account")(db_cerebrum)
    service = item["dbname"]
    db = Database.connect(user = user, service = service,
                          DB_driver = "Oracle")
    source = item["class"](db)
    accessor = getattr(source, acc_name)
    stream = StringIO.StringIO()

    for db_row in accessor():
        #
        # NB! This is not quite what we want. See comments in sanitize_group
        username = string.lower(db_row["username"])
                
        try:
            account.clear()
            account.find_by_name(username)
        except Cerebrum.Errors.NotFoundError:
            if report_missing:
                stream.write("No such account in Cerebrum: %s\n" % username)
            continue
        # yrt

        for function in func_list:
            message = function(account)
            if message:
                stream.write(message)
            # fi
        # od
    # od

    report_data = stream.getvalue()
    stream.close()
    return report_data
# end make_report



def usage():

    message = """
This script performes updates of certain groups in Cerebrum and fetches
information about certain kind of expired accounts

--ofprod		update ofprod group
--fsprod		update fsprod group
--ltprod		update ltprod group
--ajprod		update ajprod group
--oaprd			update oaprd group
--expired-file, -e=file	locate expired accounts and generate a report
"""
    logger.info(message)
# end usage
                
    

def main():
    """
    Start method for this script. 
    """
    global logger

    logger = Factory.get_logger("cronjob")
    logger.info("Performing group synchronization")

    external_dbs = { "ofprod" : { "dbname"    : "OFPROD.uio.no",
                                  "dbuser"    : "ureg2000",
                                  "class"     : OF,
                                  "sync_accessor"  : "list_dbfg_usernames",
                                  "report_accessor" : "list_applsys_usernames",
                                  "ceregroup" : "ofprod" },
                     "fsprod" : { "dbname"    : "FSPROD.uio.no",
                                  "dbuser"    : "ureg2000",
                                  "class"     : FS,
                                  "sync_accessor"  : "list_dbfg_usernames",
                                  "report_accessor" : "list_dba_usernames",
                                  "ceregroup" : "fsprod" },
                     "ltprod" : { "dbname"    : "LTPROD.uio.no",
                                  "dbuser"    : "ureg2000",
                                  "class"     : LT,
                                  "sync_accessor"  : "list_dbfg_usernames",
                                  "report_accessor"  : "list_dba_usernames",
                                  "ceregroup" : "ltprod" },
                     "ajprod" : { "dbname"    : "AJPROD.uio.no",
                                  "dbuser"    : "ureg2000",
                                  "class"     : AJ,
                                  "sync_accessor"  : "list_dbfg_usernames",
                                  "ceregroup" : "ajprod" },
                     "oaprd" : { "dbname"    : "OAPRD.uio.no",
                                 "dbuser"    : "ureg2000",
                                 "class"     : OA,
                                 "sync_accessor"  : "list_dbfg_usernames",
                                 "report_accessor" : "list_applsys_usernames",
                                 "ceregroup" : "oaprd" },
                     "basware-users" : { "dbname"        : "OEPATST.uio.no",
                                         "dbuser"        : "ureg2000",
                                         "class"         : OEP,
                                         "sync_accessor" : "list_dbfg_users",
                                         "report_accessor" : "list_dbfg_users",
                                         "ceregroup"     : "basware-users", },
                     "basware-masters" : {
                                 "dbname"        : "OEPATST.uio.no",
                                 "dbuser"        : "ureg2000",
                                 "class"         : OEP,
                                 "sync_accessor" : "list_dbfg_masters",
                                 "report_accessor" : "list_dbfg_masters",
                                 "ceregroup"     : "basware-masters", },
                     }
    try:
        options, rest = getopt.getopt(sys.argv[1:],
                                      "dhe:",
                                      ["dryrun",
                                       "help",
                                       "expired-file="] + external_dbs.keys())
    except getopt.GetoptError:
        usage()
        raise
        sys.exit(1)
    # yrt

    expired_filename = None
    services = []
    global dryrun
    dryrun = False

    for option, value in options:
        if option in ("-d", "--dryrun"):
            dryrun = True
        elif option in ("-h", "--help"):
            usage()
            sys.exit(2)
        elif option in ("-e", "--expired-file"):
            report_users(value, external_dbs)
        elif option in [ "--" + x for x in external_dbs.keys() ]:
            key = option[2:]
            services.append( external_dbs[key] )
        # fi
    # od

    perform_synchronization(services)
# end main





if __name__ == "__main__":
    main()
# fi

# arch-tag: c824d744-4ffb-47f8-bd81-69f4754b9966
